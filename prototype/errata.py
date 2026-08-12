"""The errata feed: an append-only, monotonically sequenced channel of
authorised corrections, supersessions, and erasures for exported memory roots.

This module is the trust boundary. Everything downstream — quarantine, rebuild,
probes, receipts — assumes that an erratum which reached the controller was
authorised by the owner, arrived in order, and named exactly one known root.

IDEA.md states the rejection set: invalid signatures, rollback, sequence gaps,
conflicting events, and ambiguous targets. Each has a test.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Iterable, Iterator, Mapping, Sequence

from prototype.signing import VerificationKey


class FeedError(Exception):
    """An erratum was refused. The caller must not act on it."""


class Operation(str, Enum):
    """The three operations, which must never be collapsed into each other.

    CORRECT    the earlier proposition was wrong for some or all of the
               interval it claimed to describe
    SUPERSEDE  the earlier proposition was true and later stopped being true
    ERASE      the proposition must no longer be retained or used, whether or
               not it was true
    """

    CORRECT = "correct"
    SUPERSEDE = "supersede"
    ERASE = "erase"


class RootRegistry:
    """The roots this importer has actually accepted.

    An erratum naming anything else is ambiguous rather than merely unknown:
    the importer cannot tell which local state it is supposed to act on, so it
    refuses instead of guessing.
    """

    def __init__(self, roots: Iterable[str]) -> None:
        self._roots = frozenset(roots)

    def __contains__(self, root: object) -> bool:
        return root in self._roots

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self._roots))


@dataclass(frozen=True)
class OwnerKeySchedule:
    """Owner verification keys activated at explicit feed sequences."""

    activations: tuple[tuple[int, VerificationKey], ...]

    def __post_init__(self) -> None:
        sequences = tuple(item[0] for item in self.activations)
        key_ids = tuple(item[1].key_id for item in self.activations)
        if (
            not self.activations
            or sequences[0] != 1
            or sequences != tuple(sorted(set(sequences)))
            or len(key_ids) != len(set(key_ids))
        ):
            raise ValueError("key schedule must start at 1 with unique ordered activations")

    def key_for(self, sequence: int) -> VerificationKey:
        active = self.activations[0][1]
        for activation, key in self.activations:
            if activation > sequence:
                break
            active = key
        return active


@dataclass(frozen=True)
class Erratum:
    erratum_id: str
    sequence: int
    target_root: str
    operation: Operation
    valid_from: str
    postconditions: Mapping[str, str]
    replacement: str | None = None
    signing_key_id: str | None = None
    signature: str | None = None

    def replace(self, **changes: Any) -> Erratum:
        return replace(self, **changes)

    def signable(self) -> dict[str, Any]:
        """Everything the signature covers. Excludes the signature itself."""

        return {
            "erratum_id": self.erratum_id,
            "sequence": self.sequence,
            "target_root": self.target_root,
            "operation": self.operation.value,
            "valid_from": self.valid_from,
            "postconditions": dict(self.postconditions),
            "replacement": self.replacement,
            "signing_key_id": self.signing_key_id,
        }

    def to_json(self) -> str:
        payload = self.signable()
        payload["signature"] = self.signature
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, line: str) -> Erratum:
        raw = json.loads(line)
        return cls(
            erratum_id=raw["erratum_id"],
            sequence=raw["sequence"],
            target_root=raw["target_root"],
            operation=Operation(raw["operation"]),
            valid_from=raw["valid_from"],
            postconditions=raw["postconditions"],
            replacement=raw.get("replacement"),
            signing_key_id=raw.get("signing_key_id"),
            signature=raw.get("signature"),
        )


def read_feed(text: str) -> list[Erratum]:
    """Parse a JSONL feed. Parsing is not acceptance — call `verify_feed`."""

    return [Erratum.from_json(line) for line in text.splitlines() if line.strip()]


def _check_shape(erratum: Erratum, roots: RootRegistry) -> None:
    if erratum.target_root not in roots:
        raise FeedError(
            f"{erratum.erratum_id}: unknown target root {erratum.target_root!r}. "
            "An erratum must name a root this importer accepted."
        )

    if erratum.operation is Operation.ERASE:
        if erratum.replacement is not None:
            raise FeedError(
                f"{erratum.erratum_id}: erasure carries a replacement. Erasure has "
                "no positive replacement; accepting one would let erased content "
                "return under a different operation."
            )
    elif not erratum.replacement:
        raise FeedError(
            f"{erratum.erratum_id}: {erratum.operation.value} without a replacement. "
            "Correction and supersession both state what is true instead."
        )

    required = {"negative", "preserve"}
    if erratum.operation is not Operation.ERASE:
        required.add("positive")
    missing = sorted(required - set(erratum.postconditions))
    if missing:
        raise FeedError(
            f"{erratum.erratum_id}: missing postconditions {missing}. "
            "The repair triad cannot be evaluated against an unstated postcondition."
        )


def verify_feed(
    errata: Sequence[Erratum],
    *,
    owner: VerificationKey | OwnerKeySchedule,
    roots: RootRegistry,
    last_sequence: int = 0,
) -> list[Erratum]:
    """Authenticate and order a feed, or raise `FeedError`.

    Returns the accepted errata in sequence order. Refuses the whole feed
    rather than the offending entry: a feed that equivocates or skips has
    already failed as a channel, and salvaging the entries an attacker chose to
    make well formed is not a safe default.
    """

    accepted: list[Erratum] = []
    seen: dict[int, str] = {}
    previous = last_sequence

    for erratum in errata:
        schedule = owner if isinstance(owner, OwnerKeySchedule) else OwnerKeySchedule(((1, owner),))
        active_key = schedule.key_for(erratum.sequence)
        if erratum.signing_key_id != active_key.key_id:
            raise FeedError(
                f"{erratum.erratum_id}: signing key {erratum.signing_key_id!r} is not "
                f"the active key {active_key.key_id!r} at sequence {erratum.sequence}."
            )
        if erratum.signature is None or not active_key.verify(
            erratum.signable(), erratum.signature
        ):
            raise FeedError(
                f"{erratum.erratum_id}: invalid signature. A forged erratum is "
                "durable memory poisoning, so the feed is refused."
            )

        if erratum.sequence in seen and seen[erratum.sequence] != erratum.erratum_id:
            raise FeedError(
                f"sequence {erratum.sequence} conflict: {seen[erratum.sequence]!r} "
                f"and {erratum.erratum_id!r} both claim it. The owner has "
                "equivocated, or the feed was spliced."
            )

        if erratum.sequence <= previous:
            raise FeedError(
                f"{erratum.erratum_id}: rollback to sequence {erratum.sequence} "
                f"after {previous}. Replaying an older state would resurrect a "
                "retired proposition."
            )

        if erratum.sequence != previous + 1:
            raise FeedError(
                f"{erratum.erratum_id}: gap at sequence {erratum.sequence}, "
                f"expected {previous + 1}. A missing erratum may be the one that "
                "retired the state this importer is about to serve."
            )

        _check_shape(erratum, roots)

        seen[erratum.sequence] = erratum.erratum_id
        previous = erratum.sequence
        accepted.append(erratum)

    return accepted
