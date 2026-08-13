"""Provider-neutral adapter conformance with fail-closed self-controls."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
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
        if want != got:
            failures.append(f"{path}: expected {want!r}, got {got!r}")

    compare(expected, observed, "")
    return tuple(failures)


@dataclass(frozen=True)
class NormativeTarget:
    commit: str
    surface_digest: str


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
    runtime_commit: str | None
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
            "runtime_commit": self.runtime_commit,
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


def _exact(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ConformanceInputError(f"{label} must contain exactly {sorted(keys)}")
    return value


def _nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConformanceInputError(f"{label} must be non-empty")
    return value


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, check=False
    )
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


def load_corpus(path: Path, source_root: Path) -> AdapterCorpus:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
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
    if any(not isinstance(value, str) or not value.strip() for value in provenance.values()):
        raise ConformanceInputError("provenance fields must be non-empty")
    if not re.fullmatch(r"[0-9a-f]{40}", provenance["source_commit"]):
        raise ConformanceInputError("provenance source commit must be immutable")

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
    return AdapterCorpus(
        schema_version=1,
        normative_target=NormativeTarget(target["commit"], target["surface_digest"]),
        provenance=dict(provenance),
        cases=tuple(cases),
        validator_controls=tuple(controls),
        status=_nonempty(root["status"], "status"),
        evidence_boundary=_nonempty(root["evidence_boundary"], "evidence boundary"),
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
            "diet": {"text": "is vegetarian", "inputs": (), "root": "fact:diet"},
            "quiet": {
                "text": "prefers quiet restaurants", "inputs": (), "root": "fact:quiet"
            },
            "budget": {"text": "moderate budget", "inputs": (), "root": "fact:budget"},
            "pet": {"text": "has a cat", "inputs": (), "root": "fact:pet"},
            "summary": {
                "text": "is vegetarian; prefers quiet restaurants; moderate budget",
                "inputs": ("diet", "quiet", "budget"), "root": None,
            },
        }
        if undeclared:
            self._records["orphan"] = {
                "text": "synthetic undeclared derivative",
                "inputs": (),
                "root": None,
            }
        self._active = {key: value["text"] for key, value in self._records.items()}
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
        if self._duplicate_inputs:
            for item in inputs:
                duplicate = f"duplicate:{item}"
                self._active[duplicate] = self._records[item]["text"]
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

    def proposition_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for text in self._active.values():
            for label, phrase in (
                ("quiet", "prefers quiet restaurants"),
                ("budget", "moderate budget"),
                ("pet", "has a cat"),
            ):
                if phrase in text:
                    counts[label] = counts.get(label, 0) + 1
        return counts


class ReferenceConformanceBinding:
    """Reference binding; external implementations supply an equivalent class."""

    name = "llm-errata-reference"

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
            "before_counts": adapter.proposition_counts(),
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
        after = target.proposition_counts()
        multiplicity = (
            "increased"
            if any(after.get(key, 0) > value for key, value in context["before_counts"].items())
            else "known"
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
    checkpoint = importer.quarantine(erratum)
    receipt = importer.repair_quarantined(erratum, checkpoint)
    return binding.observe(case, importer, adapter, context, checkpoint, receipt), adapter.calls


def run_validator_anti_vacuity_controls() -> tuple[ControlResult, ...]:
    """Attack validator acceptance rules, not adapter behavior."""

    # These inputs are intentionally minimal demonstrations of each historical
    # false pass. The acceptance predicate names the semantic evidence that is
    # absent instead of treating any exception or mismatch as success.
    receipt = {}
    empty_failure = "receipt is vacuous" if not receipt else ""

    offered = ("event-1", "event-2")
    accepted = offered[:1]  # no-op/partial verifier failed to return every event
    feed_failure = "accepted feed is incomplete" if accepted != offered else ""

    verdicts = ("unknown",) * 8
    semantic_failure = (
        "semantic verdict diversity is missing"
        if len(set(verdicts)) < 3 else ""
    )
    return (
        ControlResult("empty-receipt-must-fail", bool(empty_failure), empty_failure),
        ControlResult(
            "no-op-feed-verification-must-fail", bool(feed_failure), feed_failure
        ),
        ControlResult(
            "constant-unknown-aggregator-must-fail",
            bool(semantic_failure),
            semantic_failure,
        ),
    )


def _runtime_commit(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True,
        check=False,
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value) else None


def validate_adapter_conformance(
    corpus_path: Path,
    source_root: Path,
    binding_factory: Callable[[], ReferenceConformanceBinding],
) -> ConformanceReport:
    corpus = load_corpus(corpus_path, source_root)
    binding = binding_factory()
    results = []
    for case in corpus.cases:
        try:
            observed, calls = _run_case(binding, case, mutate=False)
            failures = compare_complete_outcome(case.value["expected"], observed)
            missing = tuple(sorted(set(case.value["required_calls"]) - set(calls)))
        except Exception as error:
            observed, calls, missing = {}, (), tuple(case.value["required_calls"])
            failures = (f"honest run raised unexpected {type(error).__name__}: {error}",)
        mutation_observed = None
        mutation_failures: tuple[str, ...]
        try:
            mutation_observed, _ = _run_case(binding, case, mutate=True)
            mutation_failures = compare_complete_outcome(
                case.value["mutation"]["exact_counter_result"], mutation_observed
            )
        except Exception as error:
            mutation_failures = (
                f"mutation raised unexpected {type(error).__name__}: {error}",
            )
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
        binding=binding.name,
        normative_commit=corpus.normative_target.commit,
        normative_surface_digest=corpus.normative_target.surface_digest,
        runtime_commit=_runtime_commit(source_root),
        cases=tuple(results),
        validator_controls=run_validator_anti_vacuity_controls(),
        provenance=corpus.provenance,
        evidence_boundary=corpus.evidence_boundary,
    )
