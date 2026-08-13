"""Provider-neutral adapter conformance with fail-closed self-controls."""

from __future__ import annotations

import hashlib
import inspect
import json
import re
import signal
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


class ConformanceInputError(ValueError):
    """Corpus or source evidence cannot support a conformance run."""


class TracingAdapter:
    """Proxy that records calls made through one exact adapter instance."""

    def __init__(self, target: object) -> None:
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "_calls", [])

    @property
    def calls(self) -> tuple[str, ...]:
        return tuple(object.__getattribute__(self, "_calls"))

    def reset_calls(self) -> None:
        """Start a new trace window around controller-issued lifecycle calls."""

        object.__getattribute__(self, "_calls").clear()

    def __getattr__(self, name: str) -> Any:
        value = getattr(self.target, name)
        if not callable(value):
            return value

        def traced(*args: Any, **kwargs: Any) -> Any:
            object.__getattribute__(self, "_calls").append(name)
            return value(*args, **kwargs)

        return traced


def compare_complete_outcome(
    expected: dict[str, Any], observed: dict[str, Any]
) -> tuple[str, ...]:
    """Return every exact structural/value difference between two outcomes."""

    failures: list[str] = []

    def compare(want: object, got: object, path: str) -> None:
        if isinstance(want, dict):
            if not isinstance(got, dict):
                failures.append(f"{path}: expected object, got {type(got).__name__}")
                return
            for key in want:
                child = f"{path}.{key}" if path else key
                if key not in got:
                    failures.append(f"{child}: missing")
                else:
                    compare(want[key], got[key], child)
            for key in got:
                if key not in want:
                    child = f"{path}.{key}" if path else key
                    failures.append(f"{child}: unexpected")
            return
        if type(want) is not type(got) or want != got:
            failures.append(f"{path}: expected {want!r}, got {got!r}")

    compare(expected, observed, "")
    return tuple(failures)


@dataclass(frozen=True)
class NormativeTarget:
    commit: str
    surface_digest: str


@dataclass(frozen=True, order=True)
class PropositionObservation:
    """Content-safe multiplicity for one stable provider-local proposition."""

    proposition_id: str
    fixture_label: str
    active_count: int

    def __post_init__(self) -> None:
        if not self.proposition_id or not self.fixture_label:
            raise ConformanceInputError("proposition identity and label must be non-empty")
        if isinstance(self.active_count, bool) or self.active_count < 0:
            raise ConformanceInputError("proposition active count must be non-negative")


def compare_proposition_multiplicity(
    before: tuple[PropositionObservation, ...] | None,
    after: tuple[PropositionObservation, ...] | None,
) -> str:
    """Compare exact stable identities; text similarity is never an identity seam."""

    if before is None or after is None:
        return "unknown"
    before_by_id = {item.proposition_id: item for item in before}
    after_by_id = {item.proposition_id: item for item in after}
    if len(before_by_id) != len(before) or len(after_by_id) != len(after):
        return "unknown"
    for proposition_id, prior in before_by_id.items():
        current = after_by_id.get(proposition_id)
        if current is None or current.fixture_label != prior.fixture_label:
            return "unknown"
        if current.active_count > prior.active_count:
            return "increased"
    return "known"


@dataclass(frozen=True)
class AdapterCase:
    value: dict[str, Any]

    @property
    def case_id(self) -> str:
        return self.value["id"]


@dataclass(frozen=True)
class AdapterCorpus:
    schema_version: int
    normative_target: NormativeTarget
    provenance: dict[str, str]
    cases: tuple[AdapterCase, ...]
    validator_controls: tuple[dict[str, str], ...]
    status: str
    evidence_boundary: str
    sha256: str


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    expectation_met: bool
    failures: tuple[str, ...]
    required_calls: tuple[str, ...]
    observed_calls: tuple[str, ...]
    missing_calls: tuple[str, ...]
    positive_control_passed: bool
    mutation_control_passed: bool
    mutation_failures: tuple[str, ...]
    observed: dict[str, Any]
    mutation_observed: dict[str, Any] | None

    @property
    def passed(self) -> bool:
        return (
            self.expectation_met
            and self.positive_control_passed
            and self.mutation_control_passed
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.case_id,
            "passed": self.passed,
            "expectation_met": self.expectation_met,
            "failures": list(self.failures),
            "required_calls": list(self.required_calls),
            "observed_calls": list(self.observed_calls),
            "missing_calls": list(self.missing_calls),
            "positive_control_passed": self.positive_control_passed,
            "mutation_control_passed": self.mutation_control_passed,
            "mutation_failures": list(self.mutation_failures),
            "observed": self.observed,
            "mutation_observed": self.mutation_observed,
        }


@dataclass(frozen=True)
class ControlResult:
    control_id: str
    passed: bool
    observed_failure: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.control_id,
            "passed": self.passed,
            "observed_failure": self.observed_failure,
        }


@dataclass(frozen=True)
class ConformanceReport:
    binding: str
    normative_commit: str
    normative_surface_digest: str
    corpus_sha256: str
    runtime_commit: str | None
    runtime_tree: str
    binding_source: dict[str, str]
    cases: tuple[CaseResult, ...]
    validator_controls: tuple[ControlResult, ...]
    provenance: dict[str, str]
    evidence_boundary: str

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.cases) and all(
            item.passed for item in self.validator_controls
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "binding": self.binding,
            "passed": self.passed,
            "normative_target": {
                "commit": self.normative_commit,
                "surface_digest": self.normative_surface_digest,
            },
            "corpus_sha256": self.corpus_sha256,
            "runtime_commit": self.runtime_commit,
            "runtime_tree": self.runtime_tree,
            "binding_source": dict(sorted(self.binding_source.items())),
            "cases": [item.to_dict() for item in self.cases],
            "validator_controls": [
                item.to_dict() for item in self.validator_controls
            ],
            "provenance": dict(sorted(self.provenance.items())),
            "evidence_boundary": self.evidence_boundary,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


ROOT_KEYS = {
    "schema_version", "status", "evidence_boundary", "normative_target",
    "provenance", "cases", "validator_controls",
}
TARGET_KEYS = {"commit", "surface_digest"}
PROVENANCE_KEYS = {
    "reported_by", "source_url", "source_commit", "source_license",
    "relationship", "ai_assistance", "implementation",
}
CASE_KEYS = {
    "id", "operation", "normative", "scenario", "required_calls",
    "expected", "mutation",
}
NORMATIVE_KEYS = {"commit", "path", "quote"}
EXPECTED_KEYS = {"checkpoint", "aggregate", "triad", "store", "receipt"}
STORE_KEYS = {"multiplicity", "erased_absent", "preserved_present", "unrelated_present"}
RECEIPT_KEYS = {"names_store", "non_trivial", "forbidden_absent"}
MUTATION_KEYS = {"id", "exact_counter_result"}
CONTROL_KEYS = {"id", "mutation", "required_failure"}
REQUIRED_TARGET = "ac4468faf73c2cc7949dd29b2a2a151f5bd23116"
REQUIRED_DIGEST = "7e0d6c88c1ca3a87743ac70ba2a3dfea0b350d112d2d3c59a3c6cbb537568f12"
GIT_TIMEOUT_SECONDS = 10.0
BINDING_TIMEOUT_SECONDS = 10.0
REQUIRED_PROVENANCE = {
    "reported_by": "Rastislav Drahos / DanceNitra",
    "source_url": "https://github.com/DanceNitra/agora/tree/2ba1e299b3483b9038d03387345702427608b90b/contrib/llm-errata-adapter-conformance",
    "source_commit": "2ba1e299b3483b9038d03387345702427608b90b",
    "source_license": "MIT",
    "relationship": "interested-party: Inspeximus is a G4 adapter candidate",
    "ai_assistance": "Source commit discloses Claude Opus 5 co-authorship.",
    "implementation": "Independently authored in LLM Errata; external runner and fixture files were not copied or vendored.",
}
REQUIRED_CONTROLS = (
    {
        "id": "empty-receipt-must-fail",
        "mutation": "empty-receipt",
        "required_failure": "receipt is vacuous",
    },
    {
        "id": "no-op-feed-verification-must-fail",
        "mutation": "no-op-feed-verification",
        "required_failure": "accepted feed is incomplete",
    },
    {
        "id": "constant-unknown-aggregator-must-fail",
        "mutation": "constant-unknown-aggregator",
        "required_failure": "semantic verdict diversity is missing",
    },
)


def _exact(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ConformanceInputError(f"{label} must contain exactly {sorted(keys)}")
    return value


def _nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConformanceInputError(f"{label} must be non-empty")
    return value


def _git(root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise ConformanceInputError("Git source verification timed out") from error
    if result.returncode != 0:
        raise ConformanceInputError("immutable source commit is unavailable")
    return result.stdout


def _surface_paths_at_commit(root: Path, commit: str) -> tuple[str, ...]:
    required_tests = (
        "tests/test_adapters.py", "tests/test_checkpoints.py", "tests/test_cli.py",
        "tests/test_controller.py", "tests/test_ed25519.py",
        "tests/test_errata_feed.py", "tests/test_schema.py",
        "tests/test_semantic.py", "tests/test_sqlite_store.py",
    )
    listed = _git(root, "ls-tree", "-r", "--name-only", commit).decode("utf-8").splitlines()
    files = set(listed)
    groups = (
        tuple(sorted(path for path in files if re.fullmatch(r"prototype/[^/]+\.py", path))),
        ("prototype/README.md", "spec/README.md"),
        tuple(sorted(path for path in files if re.fullmatch(r"spec/[^/]+\.schema\.json", path))),
        tuple(sorted(path for path in files if re.fullmatch(r"spec/vectors/[^/]+\.json", path))),
        tuple(sorted(path for path in files if re.fullmatch(r"spec/semantic/[^/]+\.json", path))),
        ("ROADMAP.md", "THREAT_MODEL.md", "SECURITY.md"),
        required_tests,
    )
    paths = tuple(sorted(item for group in groups for item in group))
    if any(path not in files for path in paths):
        raise ConformanceInputError("canonical surface is incomplete")
    return paths


def _surface_digest_at_commit(root: Path, commit: str) -> str:
    digest = hashlib.sha256()
    for relative in _surface_paths_at_commit(root, commit):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_git(root, "show", f"{commit}:{relative}"))
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_outcome(value: object, operation: str, label: str) -> dict[str, Any]:
    outcome = _exact(value, EXPECTED_KEYS, f"{label} expected outcome")
    triad_keys = {"negative", "preserve"} if operation == "erase" else {
        "negative", "positive", "preserve"
    }
    _exact(outcome["triad"], triad_keys, f"{label} expected outcome triad")
    _exact(outcome["store"], STORE_KEYS, f"{label} expected outcome store")
    _exact(outcome["receipt"], RECEIPT_KEYS, f"{label} expected outcome receipt")
    if outcome["checkpoint"] not in {"verified", "partial", "unknown", "failed"}:
        raise ConformanceInputError(f"{label} expected outcome checkpoint is invalid")
    if outcome["aggregate"] not in {"verified", "partial", "unknown", "failed"}:
        raise ConformanceInputError(f"{label} expected outcome aggregate is invalid")
    if set(outcome["triad"].values()) - {"pass", "fail"}:
        raise ConformanceInputError(f"{label} expected outcome triad is invalid")
    return outcome


def load_corpus(
    path: Path, source_root: Path, *, require_canonical_path: bool = False
) -> AdapterCorpus:
    if require_canonical_path and path.resolve() != (
        source_root / "spec" / "adapter-conformance.json"
    ).resolve():
        raise ConformanceInputError("corpus is not the canonical checked-in corpus")
    try:
        corpus_bytes = path.read_bytes()
        payload = json.loads(corpus_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ConformanceInputError("corpus is not readable canonical JSON") from error
    root = _exact(payload, ROOT_KEYS, "corpus")
    if root["schema_version"] != 1:
        raise ConformanceInputError("corpus schema version must be 1")
    target = _exact(root["normative_target"], TARGET_KEYS, "normative target")
    if target["commit"] != REQUIRED_TARGET:
        raise ConformanceInputError("normative target commit is not canonical")
    if target["surface_digest"] != REQUIRED_DIGEST:
        raise ConformanceInputError("normative surface digest is not canonical")
    actual_digest = _surface_digest_at_commit(source_root, target["commit"])
    if actual_digest != target["surface_digest"]:
        raise ConformanceInputError("normative surface digest does not match source")

    provenance = _exact(root["provenance"], PROVENANCE_KEYS, "provenance")
    if provenance != REQUIRED_PROVENANCE:
        raise ConformanceInputError("provenance does not match the accepted contribution")

    raw_cases = root["cases"]
    if not isinstance(raw_cases, list) or len(raw_cases) != 5:
        raise ConformanceInputError("corpus must contain exactly five cases")
    cases = []
    ids = set()
    for index, value in enumerate(raw_cases):
        case = _exact(value, CASE_KEYS, f"case[{index}]")
        case_id = _nonempty(case["id"], f"case[{index}] id")
        if case_id in ids:
            raise ConformanceInputError("case IDs must be unique")
        ids.add(case_id)
        if case["operation"] not in {"correct", "supersede", "erase"}:
            raise ConformanceInputError(f"{case_id} operation is invalid")
        normative = _exact(case["normative"], NORMATIVE_KEYS, f"{case_id} normative")
        commit = _nonempty(normative["commit"], f"{case_id} normative commit")
        try:
            _git(source_root, "merge-base", "--is-ancestor", commit, "HEAD")
        except ConformanceInputError as error:
            raise ConformanceInputError(
                f"{case_id} normative commit is not reachable from runtime history"
            ) from error
        relative = _nonempty(normative["path"], f"{case_id} normative path")
        quote = _nonempty(normative["quote"], f"{case_id} normative quotation")
        source = _git(source_root, "show", f"{commit}:{relative}").decode("utf-8")
        if quote not in source:
            raise ConformanceInputError(f"{case_id} normative quotation does not match source")
        calls = case["required_calls"]
        if not isinstance(calls, list) or not calls or not all(
            isinstance(item, str) and item for item in calls
        ) or len(calls) != len(set(calls)):
            raise ConformanceInputError(f"{case_id} required calls are invalid")
        _validate_outcome(case["expected"], case["operation"], case_id)
        mutation = _exact(case["mutation"], MUTATION_KEYS, f"{case_id} mutation")
        _nonempty(mutation["id"], f"{case_id} mutation id")
        _validate_outcome(
            mutation["exact_counter_result"], case["operation"], f"{case_id} mutation"
        )
        cases.append(AdapterCase(case))

    raw_controls = root["validator_controls"]
    if not isinstance(raw_controls, list) or len(raw_controls) != 3:
        raise ConformanceInputError("corpus must contain exactly three validator controls")
    controls = []
    for index, value in enumerate(raw_controls):
        control = _exact(value, CONTROL_KEYS, f"validator control[{index}]")
        if any(not isinstance(item, str) or not item.strip() for item in control.values()):
            raise ConformanceInputError("validator control fields must be non-empty")
        controls.append(control)
    if tuple(controls) != REQUIRED_CONTROLS:
        raise ConformanceInputError("validator controls do not match the executable attacks")
    return AdapterCorpus(
        schema_version=1,
        normative_target=NormativeTarget(target["commit"], target["surface_digest"]),
        provenance=dict(provenance),
        cases=tuple(cases),
        validator_controls=tuple(controls),
        status=_nonempty(root["status"], "status"),
        evidence_boundary=_nonempty(root["evidence_boundary"], "evidence boundary"),
        sha256=hashlib.sha256(corpus_bytes).hexdigest(),
    )


class _SyntheticHit:
    def __init__(self, artifact_id: str, content: str) -> None:
        self.artifact_id = artifact_id
        self.content = content


class ReferenceConformanceAdapter:
    """Synthetic store exercising the public StoreAdapter contract."""

    name = "reference-conformance"
    required = True

    def __init__(self, *, undeclared: bool = False) -> None:
        self._records = {
            "diet": {
                "text": "is vegetarian", "inputs": (), "root": "fact:diet",
                "propositions": ("fixture:diet",),
            },
            "quiet": {
                "text": "prefers quiet restaurants", "inputs": (), "root": "fact:quiet",
                "propositions": ("fixture:quiet",),
            },
            "budget": {
                "text": "moderate budget", "inputs": (), "root": "fact:budget",
                "propositions": ("fixture:budget",),
            },
            "pet": {
                "text": "has a cat", "inputs": (), "root": "fact:pet",
                "propositions": ("fixture:pet",),
            },
            "summary": {
                "text": "is vegetarian; prefers quiet restaurants; moderate budget",
                "inputs": ("diet", "quiet", "budget"), "root": None,
                "propositions": (
                    "fixture:diet", "fixture:quiet", "fixture:budget",
                ),
            },
        }
        if undeclared:
            self._records["orphan"] = {
                "text": "synthetic undeclared derivative",
                "inputs": (),
                "root": None,
                "propositions": (),
            }
        self._active = {key: value["text"] for key, value in self._records.items()}
        self._active_propositions = {
            key: tuple(value["propositions"]) for key, value in self._records.items()
        }
        self._quarantined: set[str] = set()
        self._retired: set[str] = set()
        self._rebuilt: set[str] = set()
        self._undeclared = undeclared
        self._force_lineage_complete = False
        self._force_unknown = False
        self._duplicate_inputs = False
        self._empty_receipt = False
        self._retire_all = False

    def enumerate(self, root: str) -> tuple[str, ...]:
        if root != "fact:diet":
            return ()
        return ("diet", "summary")

    def lineage_complete(self, root: str) -> bool:
        return self._force_lineage_complete or not self._undeclared

    def quarantine(self, artifact_ids: tuple[str, ...]) -> None:
        self._quarantined.update(artifact_ids)

    def is_quarantined(self, artifact_id: str) -> bool:
        return artifact_id in self._quarantined

    def quarantine_coverage(self, root: str):
        from prototype.adapters import Coverage

        if self._force_unknown or not self.lineage_complete(root):
            return Coverage.UNKNOWN
        descendants = set(self.enumerate(root))
        return Coverage.VERIFIED if descendants <= self._quarantined else Coverage.FAILED

    def source_artifact(self, artifact_id: str) -> str:
        return artifact_id

    def repair_inputs(self, artifact_id: str) -> tuple[str, ...]:
        return tuple(self._records[artifact_id]["inputs"])

    def retire(self, artifact_id: str, *, superseded_at: str | None = None) -> None:
        targets = tuple(self._active) if self._retire_all else (artifact_id,)
        for target in targets:
            self._retired.add(target)
            self._active.pop(target, None)
            self._active_propositions.pop(target, None)

    def rebuild(
        self, artifact_id: str, *, inputs: tuple[str, ...], replacement: str | None
    ) -> str:
        if self._retire_all:
            return ""
        parts = [self._records[item]["text"] for item in inputs]
        if replacement:
            parts.insert(0, replacement)
        text = "; ".join(parts)
        self._active[artifact_id] = text
        propositions = tuple(
            proposition
            for item in inputs
            for proposition in self._records[item]["propositions"]
        )
        self._active_propositions[artifact_id] = propositions
        if self._duplicate_inputs:
            for item in inputs:
                duplicate = f"duplicate:{item}"
                self._active[duplicate] = self._records[item]["text"]
                self._active_propositions[duplicate] = tuple(
                    self._records[item]["propositions"]
                )
        self._rebuilt.add(artifact_id)
        self._quarantined.discard(artifact_id)
        return text

    def recall(self, query: str) -> tuple[_SyntheticHit, ...]:
        term = query.lower()
        return tuple(
            _SyntheticHit(key, text)
            for key, text in self._active.items()
            if key not in self._quarantined and term in text.lower()
        )

    def snapshot(self) -> dict[str, str]:
        return dict(self._active)

    def coverage(self, root: str):
        from prototype.adapters import Coverage

        if self._force_unknown or not self.lineage_complete(root):
            return Coverage.UNKNOWN
        descendants = set(self.enumerate(root))
        disposed = self._retired | self._rebuilt
        return Coverage.VERIFIED if descendants <= disposed else Coverage.FAILED

    def dispositions(self, root: str) -> dict[str, str]:
        result = {}
        for item in self.enumerate(root):
            if item in self._retired:
                result[item] = "retired"
            elif item in self._rebuilt:
                result[item] = "rebuilt"
            elif item in self._quarantined:
                result[item] = "quarantined-only"
            else:
                result[item] = "untouched"
        return result

    def proposition_observations(self) -> tuple[PropositionObservation, ...]:
        labels = {
            "fixture:diet": "diet",
            "fixture:quiet": "quiet",
            "fixture:budget": "budget",
            "fixture:pet": "pet",
        }
        counts = {proposition_id: 0 for proposition_id in labels}
        for identities in self._active_propositions.values():
            for proposition_id in identities:
                counts[proposition_id] = counts.get(proposition_id, 0) + 1
        return tuple(
            PropositionObservation(proposition_id, labels[proposition_id], count)
            for proposition_id, count in sorted(counts.items())
        )


class ReferenceConformanceBinding:
    """Reference binding; external implementations supply an equivalent class."""

    name = "llm-errata-reference"
    preserved_proposition_ids = frozenset(
        {"fixture:quiet", "fixture:budget", "fixture:pet"}
    )

    @classmethod
    def preserved_observations(
        cls, adapter: ReferenceConformanceAdapter
    ) -> tuple[PropositionObservation, ...]:
        return tuple(
            item
            for item in adapter.proposition_observations()
            if item.proposition_id in cls.preserved_proposition_ids
        )

    def build(self, case: AdapterCase):
        from prototype.controller import Importer
        from prototype.errata import RootRegistry
        from prototype.lineage import LineageLedger
        from prototype.signing import Ed25519Signer

        adapter = ReferenceConformanceAdapter(
            undeclared=case.value["scenario"] == "undeclared-derivative"
        )
        traced = TracingAdapter(adapter)
        owner = Ed25519Signer(b"conformance-owner")
        importer = Importer(
            "conformance-importer",
            ledger=LineageLedger(),
            adapters=[traced],
            signer=Ed25519Signer(b"conformance-importer"),
            owner=owner.public,
            roots=RootRegistry({"fact:diet"}),
        )
        return importer, traced, {
            "adapter": adapter,
            "owner": owner,
            "before_observations": self.preserved_observations(adapter),
        }

    def erratum(self, case: AdapterCase, context: dict[str, Any]):
        from prototype.errata import Erratum, Operation

        operation = Operation(case.value["operation"])
        postconditions = {
            "negative": "vegetarian",
            "preserve": "quiet restaurants|moderate budget|cat",
        }
        replacement = None
        if operation is not Operation.ERASE:
            replacement = "eats meat again"
            postconditions["positive"] = replacement
        return context["owner"].sign_erratum(
            Erratum(
                erratum_id=f"case-{case.case_id}",
                sequence=1,
                target_root="fact:diet",
                operation=operation,
                valid_from="2026-08-01T00:00:00Z",
                replacement=replacement,
                postconditions=postconditions,
            )
        )

    def apply_mutation(
        self, case: AdapterCase, importer: object, adapter: TracingAdapter,
        context: dict[str, Any],
    ) -> None:
        target = context["adapter"]
        mutation = case.value["mutation"]["id"]
        if mutation == "constant-lineage-complete":
            target._force_lineage_complete = True
        elif mutation == "constant-unknown-coverage":
            target._force_unknown = True
        elif mutation == "duplicate-preserved-inputs":
            target._duplicate_inputs = True
        elif mutation == "empty-receipt":
            target._empty_receipt = True
        elif mutation == "retire-entire-store":
            target._retire_all = True
        else:
            raise ConformanceInputError(f"unknown mutation: {mutation}")

    def observe(
        self, case: AdapterCase, importer: object, adapter: TracingAdapter,
        context: dict[str, Any], checkpoint: object, receipt: object,
    ) -> dict[str, Any]:
        target: ReferenceConformanceAdapter = context["adapter"]
        blob = "{}" if target._empty_receipt else json.dumps(
            receipt.to_dict(), sort_keys=True
        )
        triad = dict(receipt.triad)
        multiplicity = compare_proposition_multiplicity(
            context["before_observations"], self.preserved_observations(target)
        )
        preserved = all(
            target.recall(term)
            for term in ("quiet restaurants", "moderate budget")
        )
        unrelated = bool(target.recall("cat"))
        forbidden_absent = (
            "is vegetarian" not in blob if case.value["operation"] == "erase" else None
        )
        erased_absent = (
            not bool(target.recall("vegetarian"))
            if case.value["operation"] == "erase" else None
        )
        if multiplicity == "increased":
            triad["preserve"] = "fail"
        if target._empty_receipt:
            aggregate = "failed"
        elif any(value != "pass" for value in triad.values()):
            aggregate = "failed"
        else:
            aggregate = receipt.aggregate.value
        return {
            "checkpoint": next(
                row.coverage for row in checkpoint.adapters if row.name == adapter.name
            ),
            "aggregate": aggregate,
            "triad": triad,
            "store": {
                "multiplicity": multiplicity,
                "erased_absent": erased_absent,
                "preserved_present": preserved,
                "unrelated_present": unrelated,
            },
            "receipt": {
                "names_store": adapter.name in blob,
                "non_trivial": len(blob) > 200,
                "forbidden_absent": forbidden_absent,
            },
        }


def _run_case(
    binding: ReferenceConformanceBinding, case: AdapterCase, *, mutate: bool
) -> tuple[dict[str, Any], tuple[str, ...]]:
    importer, adapter, context = binding.build(case)
    if mutate:
        binding.apply_mutation(case, importer, adapter, context)
    erratum = binding.erratum(case, context)
    adapter.reset_calls()
    checkpoint = importer.quarantine(erratum)
    receipt = importer.repair_quarantined(erratum, checkpoint)
    calls = adapter.calls
    observed = binding.observe(case, importer, adapter, context, checkpoint, receipt)
    return observed, calls


def _anti_vacuity_receipt(
    corpus: AdapterCorpus, receipt_validator: Callable[[object], tuple[str, ...]]
) -> str:
    mutation = next(
        item for item in corpus.validator_controls if item["mutation"] == "empty-receipt"
    )
    errors = tuple(receipt_validator({}))
    return mutation["required_failure"] if mutation["required_failure"] in errors else ""


def _anti_vacuity_feed(
    corpus: AdapterCorpus, feed_verifier: Callable[..., list[object]]
) -> str:
    from prototype.errata import Erratum, FeedError, Operation, RootRegistry
    from prototype.signing import Ed25519Signer

    mutation = next(
        item for item in corpus.validator_controls
        if item["mutation"] == "no-op-feed-verification"
    )
    owner = Ed25519Signer(b"conformance-validator-feed")
    event = owner.sign_erratum(
        Erratum(
            erratum_id="anti-vacuity-gap",
            sequence=2,
            target_root="fact:diet",
            operation=Operation.SUPERSEDE,
            valid_from="2026-08-01T00:00:00Z",
            replacement="eats meat again",
            postconditions={
                "negative": "vegetarian",
                "positive": "eats meat again",
                "preserve": "quiet restaurants",
            },
        )
    )
    try:
        feed_verifier([event], owner=owner.public, roots=RootRegistry({"fact:diet"}))
    except FeedError as error:
        expected = (
            "anti-vacuity-gap: gap at sequence 2, expected 1. "
            "A missing erratum may be the one that retired the state this importer "
            "is about to serve."
        )
        return mutation["required_failure"] if str(error) == expected else ""
    except Exception:
        return ""
    return ""


def _semantic_fixture(source_root: Path, case_name: str):
    from prototype.semantic import (
        RecordedSemanticVerifier, SemanticObservation, SemanticProbe, VerifierConfig,
    )

    semantic_root = source_root / "spec" / "semantic"
    probes_payload = json.loads((semantic_root / "probes.json").read_text())["cases"]
    observations_payload = json.loads(
        (semantic_root / "observations.json").read_text()
    )["cases"]
    config = VerifierConfig.from_dict(
        json.loads((semantic_root / "verifier-config.json").read_text())
    )
    probes = tuple(SemanticProbe.from_dict(item) for item in probes_payload[case_name])
    observations = tuple(
        SemanticObservation.from_dict(item) for item in observations_payload[case_name]
    )
    return probes, config, RecordedSemanticVerifier(observations)


def _anti_vacuity_semantic(
    corpus: AdapterCorpus, source_root: Path, semantic_runner_factory: Callable[[], object]
) -> str:
    from prototype.semantic import SemanticCoverage

    mutation = next(
        item for item in corpus.validator_controls
        if item["mutation"] == "constant-unknown-aggregator"
    )
    runner = semantic_runner_factory()
    coverages = {
        runner.run(*_semantic_fixture(source_root, case_name)).coverage
        for case_name in ("verified-correction", "failed-supersession", "unknown-erasure")
    }
    required = {
        SemanticCoverage.VERIFIED, SemanticCoverage.FAILED, SemanticCoverage.UNKNOWN,
    }
    return mutation["required_failure"] if coverages == required else ""


def run_validator_anti_vacuity_controls(
    corpus: AdapterCorpus,
    source_root: Path,
    *,
    receipt_validator: Callable[[object], tuple[str, ...]] | None = None,
    feed_verifier: Callable[..., list[object]] | None = None,
    semantic_runner_factory: Callable[[], object] | None = None,
) -> tuple[ControlResult, ...]:
    """Install declared flattering mutations against actual acceptance seams."""

    from prototype.errata import verify_feed
    from prototype.receipts import receipt_acceptance_errors
    from prototype.semantic import SemanticProbeRunner

    receipt = receipt_validator or receipt_acceptance_errors
    feed = feed_verifier or verify_feed
    semantic = semantic_runner_factory or SemanticProbeRunner
    failures = (
        _anti_vacuity_receipt(corpus, receipt),
        _anti_vacuity_feed(corpus, feed),
        _anti_vacuity_semantic(corpus, source_root, semantic),
    )
    return tuple(
        ControlResult(control["id"], failure == control["required_failure"], failure)
        for control, failure in zip(corpus.validator_controls, failures)
    )


def _runtime_identity(root: Path) -> tuple[str, str]:
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status.strip():
        raise ConformanceInputError("runtime source tree is dirty")
    commit = _git(root, "rev-parse", "HEAD").decode().strip()
    tree = _git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or not re.fullmatch(
        r"[0-9a-f]{40}", tree
    ):
        raise ConformanceInputError("runtime source identity is invalid")
    return commit, tree


def _binding_source(
    binding_factory: Callable[[], ReferenceConformanceBinding],
    binding_root: Path | None,
) -> dict[str, str]:
    try:
        file_path = Path(inspect.getsourcefile(binding_factory) or "").resolve()
        root = binding_root.resolve() if binding_root is not None else Path(
            _git(file_path.parent, "rev-parse", "--show-toplevel").decode().strip()
        ).resolve()
        relative = file_path.relative_to(root).as_posix()
        payload = file_path.read_bytes()
    except (OSError, TypeError, ValueError) as error:
        raise ConformanceInputError(
            "binding source is not inside a clean Git repository"
        ) from error
    if relative.startswith(".git/"):
        raise ConformanceInputError("binding source is not executable repository source")
    tracked = set(
        _git(root, "ls-files", "--cached").decode("utf-8").splitlines()
    )
    if relative not in tracked:
        raise ConformanceInputError("binding source is not tracked by the runtime tree")
    commit, tree = _runtime_identity(root)
    return {
        "commit": commit,
        "tree": tree,
        "path": relative,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


class _BindingTimeout(Exception):
    pass


def _run_with_timeout(action: Callable[[], Any]) -> Any:
    if threading.current_thread() is not threading.main_thread():
        raise ConformanceInputError(
            "binding execution requires the main thread for timeout enforcement"
        )

    def expire(signum: int, frame: object) -> None:
        raise _BindingTimeout

    prior = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, BINDING_TIMEOUT_SECONDS)
    try:
        return action()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior)


def validate_adapter_conformance(
    corpus_path: Path,
    source_root: Path,
    binding_factory: Callable[[], ReferenceConformanceBinding],
    binding_root: Path | None = None,
) -> ConformanceReport:
    runtime_commit, runtime_tree = _runtime_identity(source_root)
    corpus = load_corpus(corpus_path, source_root, require_canonical_path=True)
    binding_source = _binding_source(binding_factory, binding_root)
    try:
        binding = _run_with_timeout(binding_factory)
    except _BindingTimeout as error:
        raise ConformanceInputError("binding construction timed out") from error
    except ConformanceInputError:
        raise
    except Exception as error:
        raise ConformanceInputError(
            f"binding construction failed: {type(error).__name__}"
        ) from error
    try:
        binding_name = _run_with_timeout(lambda: binding.name)
    except _BindingTimeout as error:
        raise ConformanceInputError("binding metadata timed out") from error
    except ConformanceInputError:
        raise
    except Exception as error:
        raise ConformanceInputError(
            f"binding metadata failed: {type(error).__name__}"
        ) from error
    if not isinstance(binding_name, str) or not binding_name.strip():
        raise ConformanceInputError("binding metadata name must be non-empty")
    results = []
    for case in corpus.cases:
        try:
            observed, calls = _run_with_timeout(
                lambda case=case: _run_case(binding, case, mutate=False)
            )
            failures = compare_complete_outcome(case.value["expected"], observed)
            missing = tuple(sorted(set(case.value["required_calls"]) - set(calls)))
        except _BindingTimeout as error:
            raise ConformanceInputError("binding execution timed out") from error
        except Exception as error:
            raise ConformanceInputError(
                f"binding execution failed for {case.case_id}: {type(error).__name__}"
            ) from error
        mutation_observed = None
        mutation_failures: tuple[str, ...]
        try:
            mutation_observed, _ = _run_with_timeout(
                lambda case=case: _run_case(binding, case, mutate=True)
            )
            mutation_failures = compare_complete_outcome(
                case.value["mutation"]["exact_counter_result"], mutation_observed
            )
        except _BindingTimeout as error:
            raise ConformanceInputError("binding execution timed out") from error
        except Exception as error:
            raise ConformanceInputError(
                f"binding execution failed for {case.case_id} mutation: "
                f"{type(error).__name__}"
            ) from error
        results.append(
            CaseResult(
                case_id=case.case_id,
                expectation_met=not failures,
                failures=failures,
                required_calls=tuple(case.value["required_calls"]),
                observed_calls=tuple(sorted(set(calls))),
                missing_calls=missing,
                positive_control_passed=not missing,
                mutation_control_passed=not mutation_failures,
                mutation_failures=mutation_failures,
                observed=observed,
                mutation_observed=mutation_observed,
            )
        )
    return ConformanceReport(
        binding=binding_name,
        normative_commit=corpus.normative_target.commit,
        normative_surface_digest=corpus.normative_target.surface_digest,
        corpus_sha256=corpus.sha256,
        runtime_commit=runtime_commit,
        runtime_tree=runtime_tree,
        binding_source=binding_source,
        cases=tuple(results),
        validator_controls=run_validator_anti_vacuity_controls(corpus, source_root),
        provenance=corpus.provenance,
        evidence_boundary=corpus.evidence_boundary,
    )
