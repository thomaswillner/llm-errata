"""Store adapters.

Three deliberately different stores, as ROADMAP.md Phase 1 requires:

- `MarkdownAdapter` — exact root-to-artifact lineage, deterministic quarantine
  and rebuild. The easy case.
- `VectorAdapter` — entries carrying derivation metadata, retrieved by
  similarity rather than by key. The realistic case.
- `OpaqueAdapter` — can acknowledge an erratum and can be asked to quarantine,
  but cannot enumerate or prove anything about its own state. The control.

The opaque adapter is not a toy edge case. Without it a conformance suite grades
itself: every adapter that can be inspected passes, the aggregate goes green,
and the honesty requirement is never tested. With it, the demo cannot report
success no matter how well the other two behave.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from prototype.lineage import LineageLedger


class CannotEnumerate(Exception):
    """The store exposes no interface adequate to list its own state."""


class Coverage(str, Enum):
    """The four terminal coverage results. `pending` is deliberately absent:
    it is a lifecycle state, not an outcome."""

    VERIFIED = "verified"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    FAILED = "failed"


@dataclass(frozen=True)
class Hit:
    artifact_id: str
    content: str
    score: float = 1.0


@dataclass(frozen=True)
class HistoricalHit:
    """A proposition that was true and stopped being true.

    Reachable only through `recall_history`, never through `recall`. That split
    is what keeps supersession from rewriting history and correction from
    preserving a claim that was never true: a supersession moves the old value
    here, a correction and an erasure destroy it.
    """

    artifact_id: str
    content: str
    valid_until: str


class StoreAdapter(Protocol):
    """Complete fail-closed surface exercised by the reference controller."""

    name: str
    required: bool

    def enumerate(self, root: str) -> tuple[str, ...]: ...

    def lineage_complete(self, root: str) -> bool:
        """Whether enumeration is complete under a root-specific authority."""

        ...

    def quarantine(self, artifact_ids: tuple[str, ...]) -> None: ...

    def is_quarantined(self, artifact_id: str) -> bool: ...

    def quarantine_coverage(self, root: str) -> Coverage:
        """Coverage at the durable quarantine checkpoint, before repair."""

        ...

    def source_artifact(self, artifact_id: str) -> str:
        """Stable lineage node represented by one store artifact."""

        ...

    def repair_inputs(self, artifact_id: str) -> tuple[str, ...]:
        """Store-owned direct inputs used to classify and rebuild an artifact."""

        ...

    def retire(self, artifact_id: str, *, superseded_at: str | None = None) -> None: ...

    def rebuild(
        self, artifact_id: str, *, inputs: tuple[str, ...], replacement: str | None
    ) -> str: ...

    def recall(self, query: str) -> tuple[Hit, ...]: ...

    def snapshot(self) -> dict[str, str]:
        """Inspectable state bound into checkpoint and receipt state roots."""

        ...

    def coverage(self, root: str) -> Coverage: ...

    def dispositions(self, root: str) -> dict[str, str]: ...


class MarkdownAdapter:
    """A file-backed store with exact lineage."""

    name = "markdown"
    required = True

    def __init__(self, ledger: LineageLedger) -> None:
        self._ledger = ledger
        self._quarantined: set[str] = set()
        self._retired: set[str] = set()
        self._rebuilt: set[str] = set()
        self._history: list[HistoricalHit] = []

    def enumerate(self, root: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                item
                for item in self._ledger.descendants(root)
                if self._ledger.store_of(item) == self.name
            )
        )

    def lineage_complete(self, root: str) -> bool:
        """The write-time ledger is this adapter's enumeration authority."""

        return root in self._ledger.roots_seen() and all(
            artifact.artifact_id in self._ledger.descendants(root)
            for artifact in self._ledger.artifacts()
            if artifact.store == self.name and artifact.root == root
        )

    def quarantine(self, artifact_ids: tuple[str, ...]) -> None:
        self._quarantined.update(artifact_ids)

    def is_quarantined(self, artifact_id: str) -> bool:
        return artifact_id in self._quarantined

    def quarantine_coverage(self, root: str) -> Coverage:
        descendants = set(self.enumerate(root))
        if not self.lineage_complete(root):
            return Coverage.UNKNOWN
        if descendants.issubset(self._quarantined):
            return Coverage.VERIFIED
        if descendants & self._quarantined:
            return Coverage.PARTIAL
        return Coverage.FAILED

    def retire(self, artifact_id: str, *, superseded_at: str | None = None) -> None:
        """Remove an artifact from present-tense recall.

        `superseded_at` is supplied only for a supersession, and it carries the
        instant the proposition stopped being true. Without it the content is
        destroyed, which is the required behaviour for a correction (the claim
        was never true, so preserving it would preserve a falsehood) and for an
        erasure (the claim must no longer be retained at all).
        """

        if superseded_at is not None:
            self._history.append(
                HistoricalHit(
                    artifact_id=artifact_id,
                    content=self._ledger.artifact(artifact_id).content,
                    valid_until=superseded_at,
                )
            )
        self._retired.add(artifact_id)

    def recall_history(self, query: str) -> tuple[HistoricalHit, ...]:
        terms = _terms(query)
        return tuple(
            entry for entry in self._history if terms & _terms(entry.content)
        )

    def rebuild(
        self, artifact_id: str, *, inputs: tuple[str, ...], replacement: str | None
    ) -> str:
        parts = [self._ledger.artifact(item).content for item in inputs]
        if replacement:
            parts.insert(0, replacement)
        content = "; ".join(parts)
        self._ledger.set_content(artifact_id, content)
        self._rebuilt.add(artifact_id)
        self._quarantined.discard(artifact_id)
        return content

    def content(self, artifact_id: str) -> str:
        return self._ledger.artifact(artifact_id).content

    def source_artifact(self, artifact_id: str) -> str:
        """The ledger artifact this store item derives from. Here, itself."""

        return artifact_id

    def repair_inputs(self, artifact_id: str) -> tuple[str, ...]:
        return self._ledger.artifact(artifact_id).inputs

    def release(self, artifact_id: str) -> None:
        """Un-gate without repairing. Only a non-conforming strategy does this."""

        self._quarantined.discard(artifact_id)

    def mark_rebuilt(self, artifact_id: str) -> None:
        self._rebuilt.add(artifact_id)

    def snapshot(self) -> dict[str, str]:
        return {
            artifact.artifact_id: artifact.content
            for artifact in self._ledger.artifacts()
            if artifact.store == self.name and artifact.artifact_id not in self._retired
        }

    def recall(self, query: str) -> tuple[Hit, ...]:
        terms = _terms(query)
        hits = []
        for artifact in self._ledger.artifacts():
            if artifact.store != self.name:
                continue
            if artifact.artifact_id in self._quarantined:
                continue
            if artifact.artifact_id in self._retired:
                continue
            if terms & _terms(artifact.content):
                hits.append(Hit(artifact.artifact_id, artifact.content))
        return tuple(hits)

    def coverage(self, root: str) -> Coverage:
        descendants = set(self.enumerate(root))
        if not descendants:
            return Coverage.VERIFIED
        disposed = self._retired | self._rebuilt
        undisposed = descendants - disposed
        if not undisposed:
            return Coverage.VERIFIED
        if disposed & descendants:
            return Coverage.PARTIAL
        return Coverage.FAILED

    def dispositions(self, root: str) -> dict[str, str]:
        result = {}
        for artifact_id in self.enumerate(root):
            if artifact_id in self._retired:
                result[artifact_id] = "retired"
            elif artifact_id in self._rebuilt:
                result[artifact_id] = "rebuilt"
            elif artifact_id in self._quarantined:
                result[artifact_id] = "quarantined-only"
            else:
                result[artifact_id] = "untouched"
        return result


class VectorAdapter:
    """A local vector store whose entries carry derivation metadata.

    The embedding is a deterministic bag-of-terms, not a model. That is
    sufficient for the property under test — that a quarantined entry stops
    being retrieved and an unrelated entry does not — and it keeps the demo
    reproducible from a clean checkout with no network and no API key.
    """

    name = "vector"
    required = True

    def __init__(self, ledger: LineageLedger) -> None:
        self._ledger = ledger
        # `_source_of` is written once at index time and never removed, so a
        # retired entry still enumerates as a descendant. An entry that
        # disappeared from the closure the moment it was retired would let a
        # store report full coverage by deleting the evidence.
        self._source_of: dict[str, str] = {}
        self._text: dict[str, str] = {}
        self._quarantined: set[str] = set()
        self._retired: set[str] = set()
        self._rebuilt: set[str] = set()

    def index(self, entry_id: str, *, source: str, text: str) -> None:
        self._source_of[entry_id] = source
        self._text[entry_id] = text

    def enumerate(self, root: str) -> tuple[str, ...]:
        closure = self._ledger.descendants(root)
        return tuple(
            sorted(
                entry_id
                for entry_id, source in self._source_of.items()
                if source in closure
            )
        )

    def lineage_complete(self, root: str) -> bool:
        """Every indexed entry records its source in ``_source_of`` at write time."""

        return (
            root in self._ledger.roots_seen()
            and set(self._text).issubset(self._source_of)
            and all(
                source in self._ledger.artifact_ids()
                for source in self._source_of.values()
            )
        )

    def quarantine(self, artifact_ids: tuple[str, ...]) -> None:
        self._quarantined.update(artifact_ids)

    def is_quarantined(self, artifact_id: str) -> bool:
        return artifact_id in self._quarantined

    def quarantine_coverage(self, root: str) -> Coverage:
        descendants = set(self.enumerate(root))
        if not self.lineage_complete(root):
            return Coverage.UNKNOWN
        if descendants.issubset(self._quarantined):
            return Coverage.VERIFIED
        if descendants & self._quarantined:
            return Coverage.PARTIAL
        return Coverage.FAILED

    def retire(self, entry_id: str, *, superseded_at: str | None = None) -> None:
        self._retired.add(entry_id)
        self._text.pop(entry_id, None)

    def rebuild(
        self, entry_id: str, *, inputs: tuple[str, ...], replacement: str | None
    ) -> str:
        parts = [self._ledger.artifact(item).content for item in inputs]
        if replacement:
            parts.insert(0, replacement)
        text = "; ".join(parts)
        self._text[entry_id] = text
        self._rebuilt.add(entry_id)
        self._quarantined.discard(entry_id)
        return text

    def recall(self, query: str, *, threshold: float = 0.2) -> tuple[Hit, ...]:
        hits = []
        for entry_id, text in self._text.items():
            if entry_id in self._quarantined:
                continue
            score = _similarity(query, text)
            if score >= threshold:
                hits.append(Hit(entry_id, text, score))
        return tuple(sorted(hits, key=lambda hit: (-hit.score, hit.artifact_id)))

    def source_of(self, entry_id: str) -> str:
        return self._source_of[entry_id]

    def source_artifact(self, entry_id: str) -> str:
        return self.source_of(entry_id)

    def repair_inputs(self, entry_id: str) -> tuple[str, ...]:
        return self._ledger.artifact(self.source_artifact(entry_id)).inputs

    def release(self, entry_id: str) -> None:
        self._quarantined.discard(entry_id)

    def mark_rebuilt(self, entry_id: str) -> None:
        self._rebuilt.add(entry_id)

    def snapshot(self) -> dict[str, str]:
        return dict(self._text)

    def coverage(self, root: str) -> Coverage:
        descendants = set(self.enumerate(root))
        if not descendants:
            return Coverage.VERIFIED
        disposed = self._retired | self._rebuilt
        outstanding = descendants - disposed
        if not outstanding:
            return Coverage.VERIFIED
        if disposed & descendants:
            return Coverage.PARTIAL
        return Coverage.FAILED

    def dispositions(self, root: str) -> dict[str, str]:
        result = {}
        for entry_id in self.enumerate(root):
            if entry_id in self._retired:
                result[entry_id] = "retired"
            elif entry_id in self._rebuilt:
                result[entry_id] = "rebuilt"
            elif entry_id in self._quarantined:
                result[entry_id] = "quarantined-only"
            else:
                result[entry_id] = "untouched"
        return result


class OpaqueAdapter:
    """A store that can be told, but cannot be inspected.

    A vendor-owned prompt cache is the motivating example: it will accept a
    deletion request and return 200, and there is no interface that lets an
    importer confirm what happened. Everything it reports is `unknown`, and it
    reports that whether or not it was asked to quarantine, because being asked
    is not evidence.
    """

    required = True

    def __init__(self, name: str = "opaque") -> None:
        self.name = name
        self._acknowledged: set[str] = set()

    def enumerate(self, root: str) -> tuple[str, ...]:
        raise CannotEnumerate(
            f"{self.name}: no interface exposes the artifacts derived from {root}. "
            "Coverage for this store is unknown, and no repair elsewhere changes "
            "that."
        )

    def acknowledge(self, root: str) -> bool:
        self._acknowledged.add(root)
        return True

    def lineage_complete(self, root: str) -> bool:
        return False

    def quarantine(self, artifact_ids: tuple[str, ...]) -> None:
        return None

    def is_quarantined(self, artifact_id: str) -> bool:
        return False

    def quarantine_coverage(self, root: str) -> Coverage:
        return Coverage.UNKNOWN

    def source_artifact(self, artifact_id: str) -> str:
        return artifact_id

    def repair_inputs(self, artifact_id: str) -> tuple[str, ...]:
        return ()

    def retire(
        self, artifact_id: str, *, superseded_at: str | None = None
    ) -> None:
        return None

    def rebuild(
        self, artifact_id: str, *, inputs: tuple[str, ...], replacement: str | None
    ) -> str:
        raise CannotEnumerate(f"{self.name}: cannot rebuild what it cannot enumerate.")

    def recall(self, query: str) -> tuple[Hit, ...]:
        return ()

    def snapshot(self) -> dict[str, str]:
        return {}

    def coverage(self, root: str) -> Coverage:
        return Coverage.UNKNOWN

    def dispositions(self, root: str) -> dict[str, str]:
        return {}


_WORD = re.compile(r"[a-z0-9]+")


def _terms(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def _similarity(left: str, right: str) -> float:
    a, b = _terms(left), _terms(right)
    if not a or not b:
        return 0.0
    return len(a & b) / math.sqrt(len(a) * len(b))
