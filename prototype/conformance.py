"""Provider-neutral adapter conformance with fail-closed self-controls."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConformanceInputError(ValueError):
    """Corpus or source evidence cannot support a conformance run."""


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
