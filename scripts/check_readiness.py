#!/usr/bin/env python3
"""Validate the repository's production-readiness evidence ledger."""

from __future__ import annotations

import json
import re
import hashlib
import math
import operator
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "readiness" / "production-readiness.json"
MATRIX = ROOT / "PRODUCTION_READINESS.md"
REQUIRED_GATES = {"G1", "G2", "G3", "G4", "G5", "G6"}
EXPECTED_CLASSES = {
    "G1": "internal",
    "G2": "external",
    "G3": "external",
    "G4": "external",
    "G5": "external",
    "G6": "external",
}
VERDICTS = {"NOT_PROD_READY", "PROD_READY"}
STATUSES = {"PASS", "FAIL", "BLOCKED"}
CLASSES = {"internal", "external"}
GENERIC_NON_INDEPENDENT_PRODUCER_RE = re.compile(
    r"(?:^|[\s:_-])(author|owner|implementer|operator|contributor|maintainer|thomas|willner|project|reference|local|agent|repository|repo|self)(?:$|[\s:_-])",
    re.IGNORECASE,
)
G2_NON_INDEPENDENT_PRODUCER_RE = re.compile(
    r"(?:^|[\s:_-])(author|owner|implementer|contributor|maintainer|thomas|willner|project|reference|local|agent|repository|repo|self)(?:$|[\s:_-])",
    re.IGNORECASE,
)
URN_RE = re.compile(r"^urn:[A-Za-z0-9][A-Za-z0-9-]{1,31}:[^\s]+$")
G2_ATTESTATION = "llm-errata-independent-review-v1"
G2_REQUIRED_TESTS = (
    "tests/test_adapters.py",
    "tests/test_checkpoints.py",
    "tests/test_cli.py",
    "tests/test_conformance.py",
    "tests/test_controller.py",
    "tests/test_ed25519.py",
    "tests/test_errata_feed.py",
    "tests/test_schema.py",
    "tests/test_semantic.py",
    "tests/test_sqlite_store.py",
)
G2_SCOPE = frozenset(
    {
        "schemas",
        "vectors",
        "cli",
        "adapter-interface",
        "transactional-store",
        "substrate-evidence",
        "semantic-probes",
        "security-boundaries",
    }
)
G2_RESULTS = {"pass", "pass-with-findings", "fail"}
G3_ATTESTATION = "llm-errata-independent-cryptography-review-v1"
G3_SCOPE = frozenset({
    "library-build", "constant-time", "malformed-input-refusal",
    "key-rotation", "key-recovery", "revocation", "delegation",
})
G4_ATTESTATION = "llm-errata-independent-implementation-v1"
G5_ATTESTATION = "llm-errata-independent-interoperability-review-v1"
G6_ATTESTATION = "llm-errata-independent-operational-review-v1"
G6_SCOPE = frozenset(
    {
        "deployment-integrity-provenance",
        "rollback-exercise",
        "backup-recovery-rto-rpo",
        "lifecycle-observability-alerting",
        "telemetry-privacy-redaction",
        "supported-version-compatibility",
        "representative-latency-throughput",
        "overload-rate-limit-dos",
        "incident-response-exercise",
        "operational-access-secrets-dependencies-vulnerability-management",
    }
)
G6_NON_INDEPENDENT_PRODUCER_RE = re.compile(
    r"(?:^|[\s:_-])(author|owner|implementer|operator|contributor|maintainer|thomas|willner|project|reference|local|agent|repository|repo|self)(?:$|[\s:_-])",
    re.IGNORECASE,
)
COMPARATORS = {
    "<=": operator.le,
    "<": operator.lt,
    ">=": operator.ge,
    ">": operator.gt,
    "==": operator.eq,
    "!=": operator.ne,
}
G2_MATRIX_CURRENT_EVIDENCE = (
    "Phase 2 implementation includes conflict-disclosed remediation for split-view "
    "equivocation, unsupported empty enumeration, checkpoint coverage, and adapter-contract "
    "completeness, plus schemas, semantic probes, adapter-level conformance, validator "
    "anti-vacuity controls, key rotation, invalid-target, confidentiality, and receipt binding; "
    "no qualifying independent review is recorded."
)
G2_MATRIX_NEXT_EVIDENCE = (
    "Dated independent external conformance-review result covering the exact complete Phase 2 surface after remediation."
)
G6_MATRIX_CURRENT_EVIDENCE = (
    "No independent report binds an exact commit and deployment to passing "
    "measured comparators for all ten operational scopes."
)
G6_MATRIX_NEXT_EVIDENCE = (
    "One qualifying independent report with declared workload, platform, failure domain, "
    "observation window, numeric thresholds, raw artifacts, and passing measurements for every scope."
)


class Reporter:
    def __init__(self) -> None:
        self.passed = 0
        self.failures: list[str] = []

    def check(self, name: str, condition: bool, detail: str) -> None:
        if condition:
            self.passed += 1
            print(f"[PASS] {name}: {detail}")
        else:
            self.failures.append(name)
            print(f"[FAIL] {name}: {detail}")

    def finish(self) -> int:
        if self.failures:
            print(f"\nReadiness validation failed: {', '.join(self.failures)}")
            return 1
        print("\nReadiness evidence is structurally valid; current verdict is not upgraded.")
        return 0


def read_ledger() -> dict[str, object]:
    payload = json.loads(LEDGER.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("readiness ledger root must be an object")
    return payload


def valid_iso_date(value: object) -> bool:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def valid_external_ref(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return bool(URN_RE.fullmatch(value)) or (parsed.scheme == "https" and bool(parsed.netloc))


def valid_g2_report_ref(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return bool(URN_RE.fullmatch(value)) or (
        parsed.scheme == "https" and bool(parsed.netloc) and parsed.path not in {"", "/"}
    )


def valid_g2_identity_ref(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc) and parsed.path not in {"", "/"}


def g2_surface_files(root: Path = ROOT) -> tuple[str, ...]:
    """Return comprehensive sorted first-party Phase 2 review manifest."""

    groups = (
        tuple(sorted((root / "prototype").glob("*.py"))),
        (root / "prototype" / "README.md",),
        (root / "spec" / "README.md",),
        (root / "spec" / "adapter-conformance.json",),
        tuple(sorted((root / "spec").glob("*.schema.json"))),
        tuple(sorted((root / "spec" / "vectors").glob("*.json"))),
        tuple(sorted((root / "spec" / "semantic").glob("*.json"))),
        tuple(root / path for path in ("ROADMAP.md", "THREAT_MODEL.md", "SECURITY.md")),
        tuple(root / path for path in G2_REQUIRED_TESTS),
    )
    if any(not group for group in groups) or any(not path.is_file() for group in groups for path in group):
        raise OSError("canonical G2 surface is incomplete")
    return tuple(
        sorted(path.relative_to(root).as_posix() for group in groups for path in group)
    )


def surface_digest_from_bytes(entries: list[tuple[str, bytes]]) -> str:
    """SHA-256 over `relative path + NUL + raw bytes + NUL` ordered entries."""

    digest = hashlib.sha256()
    for relative, content in entries:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def review_surface_content(relative: str, content: bytes) -> bytes:
    """Normalize only the corpus's self-referential target pointer.

    Cases, provenance, controls, and every other corpus byte remain digest-bound.
    The target commit and digest are validated separately. Normalizing those two
    fields lets a later packaging commit point at the immutable source commit
    without requiring a Git commit to contain its own hash.
    """

    if relative != "spec/adapter-conformance.json":
        return content
    try:
        payload = json.loads(content.decode("utf-8"))
        target = payload["normative_target"]
        if not isinstance(target, dict):
            raise TypeError
        target["commit"] = "0" * 40
        target["surface_digest"] = "0" * 64
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise OSError("conformance corpus target metadata is malformed") from error
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def g2_surface_digest(root: Path = ROOT) -> str:
    return surface_digest_from_bytes(
        [
            (relative, review_surface_content(relative, (root / relative).read_bytes()))
            for relative in g2_surface_files(root)
        ]
    )


def g2_surface_digest_at_commit(commit: str, root: Path = ROOT) -> str:
    if not reviewed_commit_exists(commit, root):
        raise OSError("reviewed commit is unavailable")
    listed = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )
    if listed.returncode != 0:
        raise OSError("reviewed commit tree is unavailable")
    commit_files = set(listed.stdout.splitlines())
    entries = []
    for relative in g2_surface_files(root):
        if relative == "spec/adapter-conformance.json" and relative not in commit_files:
            raise OSError("reviewed commit predates the conformance corpus")
        result = subprocess.run(
            ["git", "show", f"{commit}:{relative}"], cwd=root, capture_output=True, check=False
        )
        if result.returncode != 0:
            raise OSError(f"reviewed commit lacks {relative}")
        entries.append((relative, review_surface_content(relative, result.stdout)))
    return surface_digest_from_bytes(entries)


def reviewed_commit_exists(value: str, root: Path = ROOT) -> bool:
    """Fail closed unless checkout has Git metadata and commit exists."""

    if not (root / ".git").exists():
        return False
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{value}^{{commit}}"],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )
    return result.returncode == 0


def valid_external_evidence(entry: object, *, today: date | None = None) -> bool:
    """Return whether one external evidence entry meets readiness semantics."""

    if not isinstance(entry, dict):
        return False
    producer = entry.get("producer")
    observed = entry.get("observed")
    if not valid_external_ref(entry.get("ref")):
        return False
    if not isinstance(producer, str) or not producer.strip():
        return False
    if GENERIC_NON_INDEPENDENT_PRODUCER_RE.search(producer) is not None:
        return False
    if not valid_iso_date(observed):
        return False
    return date.fromisoformat(observed) <= (today or date.today())


def valid_g2_review_evidence(
    entry: object, *, today: date | None = None, root: Path = ROOT
) -> bool:
    """Validate a qualifying independent review of complete Phase 2 surface."""

    if not valid_external_evidence(entry, today=today) or not isinstance(entry, dict):
        return False
    scope = entry.get("scope")
    reviewed_commit = entry.get("reviewed_commit")
    try:
        return (
            entry.get("kind") == "external"
            and valid_g2_report_ref(entry.get("ref"))
            and entry.get("review_type") == "phase2-conformance"
            and isinstance(reviewed_commit, str)
            and re.fullmatch(r"[0-9a-f]{40}", reviewed_commit) is not None
            and G2_NON_INDEPENDENT_PRODUCER_RE.search(entry["producer"]) is None
            and isinstance(scope, list)
            and all(isinstance(token, str) for token in scope)
            and len(scope) == len(set(scope))
            and set(scope) == G2_SCOPE
            and entry.get("result") in G2_RESULTS
            and entry.get("relationship") == "independent-third-party"
            and isinstance(entry.get("conflicts"), list)
            and isinstance(entry.get("producer_identity"), str)
            and valid_g2_identity_ref(entry["producer_identity"])
            and entry.get("independence_attestation") == G2_ATTESTATION
            and entry.get("surface_digest") == g2_surface_digest(root)
            and entry.get("surface_digest") == g2_surface_digest_at_commit(reviewed_commit, root)
        )
    except OSError:
        return False


def qualifying_g2_review_evidence(
    entry: object, *, today: date | None = None, root: Path = ROOT
) -> bool:
    """Return whether a valid G2 review can satisfy a G2 PASS gate."""

    return valid_g2_review_evidence(entry, today=today, root=root) and entry.get("result") in {
        "pass",
        "pass-with-findings",
    }


def _surface_digest_for_files(files: tuple[str, ...], root: Path) -> str:
    if any(not (root / relative).is_file() for relative in files):
        raise OSError("gate surface is incomplete")
    return surface_digest_from_bytes(
        [(relative, (root / relative).read_bytes()) for relative in sorted(files)]
    )


def _surface_digest_for_files_at_commit(
    files: tuple[str, ...], commit: str, root: Path
) -> str:
    if not reviewed_commit_exists(commit, root):
        raise OSError("reviewed commit is unavailable")
    entries = []
    for relative in sorted(files):
        result = subprocess.run(
            ["git", "show", f"{commit}:{relative}"], cwd=root,
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise OSError(f"reviewed commit lacks {relative}")
        entries.append((relative, result.stdout))
    return surface_digest_from_bytes(entries)


G3_SURFACE_FILES = (
    "prototype/ed25519.py", "prototype/errata.py", "prototype/signing.py",
    "THREAT_MODEL.md", "docs/CRYPTOGRAPHY_QUALIFICATION.md",
    "tests/test_ed25519.py", "tests/test_errata_feed.py",
)
G5_SURFACE_FILES = (
    "PHASE3_SYSTEMS.md", "ROADMAP.md", "spec/erratum.schema.json",
    "spec/receipt.schema.json",
)


def _commit_bound_external(
    entry: object,
    *,
    attestation: str,
    surface_files: tuple[str, ...] | None,
    today: date | None,
    root: Path,
) -> bool:
    if not valid_external_evidence(entry, today=today) or not isinstance(entry, dict):
        return False
    commit = entry.get("reviewed_commit")
    if not (
        entry.get("kind") == "external"
        and valid_g2_report_ref(entry.get("ref"))
        and isinstance(commit, str)
        and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
        and entry.get("relationship") in {
            "independent-third-party", "independent-implementation",
            "independent-third-party-validator", "independent-experiment-report",
        }
        and isinstance(entry.get("conflicts"), list)
        and valid_g2_identity_ref(entry.get("producer_identity"))
        and entry.get("independence_attestation") == attestation
        and entry.get("result") in G2_RESULTS
    ):
        return False
    try:
        if surface_files is None:
            current = g2_surface_digest(root)
            committed = g2_surface_digest_at_commit(commit, root)
        else:
            current = _surface_digest_for_files(surface_files, root)
            committed = _surface_digest_for_files_at_commit(surface_files, commit, root)
        return entry.get("surface_digest") == current == committed
    except OSError:
        return False


def qualifying_g3_security_evidence(
    entry: object, *, today: date | None = None, root: Path = ROOT
) -> bool:
    if not _commit_bound_external(
        entry, attestation=G3_ATTESTATION, surface_files=G3_SURFACE_FILES,
        today=today, root=root,
    ) or not isinstance(entry, dict):
        return False
    implementation = entry.get("implementation")
    return (
        entry.get("review_type") == "production-cryptography"
        and entry.get("relationship") == "independent-third-party"
        and entry.get("result") in {"pass", "pass-with-findings"}
        and isinstance(entry.get("scope"), list)
        and set(entry["scope"]) == G3_SCOPE
        and len(entry["scope"]) == len(G3_SCOPE)
        and _exact_dict(implementation, {
            "library", "version", "binding", "build_digest", "platforms",
            "constant_time", "audited_build",
        })
        and all(_nonempty(implementation[key]) for key in ("library", "version", "binding"))
        and isinstance(implementation["build_digest"], str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", implementation["build_digest"]) is not None
        and isinstance(implementation["platforms"], list) and bool(implementation["platforms"])
        and all(_nonempty(item) for item in implementation["platforms"])
        and implementation["constant_time"] is True
        and implementation["audited_build"] is True
    )


def valid_g4_implementation_evidence(
    entry: object, *, today: date | None = None, root: Path = ROOT
) -> bool:
    if not _commit_bound_external(
        entry, attestation=G4_ATTESTATION, surface_files=None,
        today=today, root=root,
    ) or not isinstance(entry, dict):
        return False
    role = entry.get("evidence_role")
    expected_relationship = (
        "independent-implementation" if role == "adapter"
        else "independent-third-party-validator"
    )
    return (
        entry.get("review_type") == "g4-conformance"
        and role in {"adapter", "validator"}
        and entry.get("relationship") == expected_relationship
        and entry.get("result") in {"pass", "pass-with-findings"}
        and _nonempty(entry.get("implementation_id"))
    )


def qualifying_g4_evidence(
    entries: list[dict[str, object]], *, today: date | None = None, root: Path = ROOT
) -> bool:
    valid = [
        entry for entry in entries
        if valid_g4_implementation_evidence(entry, today=today, root=root)
    ]
    adapters = [entry for entry in valid if entry["evidence_role"] == "adapter"]
    validators = [entry for entry in valid if entry["evidence_role"] == "validator"]
    if len(adapters) < 2 or not validators:
        return False
    adapter_identities = {entry["producer_identity"] for entry in adapters}
    adapter_implementations = {entry["implementation_id"] for entry in adapters}
    validator_identities = {entry["producer_identity"] for entry in validators}
    targets = {(entry["reviewed_commit"], entry["surface_digest"]) for entry in valid}
    return (
        len(adapter_identities) >= 2
        and len(adapter_implementations) >= 2
        and validator_identities.isdisjoint(adapter_identities)
        and len(targets) == 1
    )


def qualifying_g5_interoperability_evidence(
    entry: object, *, today: date | None = None, root: Path = ROOT
) -> bool:
    if not _commit_bound_external(
        entry, attestation=G5_ATTESTATION, surface_files=G5_SURFACE_FILES,
        today=today, root=root,
    ) or not isinstance(entry, dict):
        return False
    systems = entry.get("systems")
    if not (
        entry.get("review_type") == "phase3-interoperability"
        and entry.get("relationship") == "independent-experiment-report"
        and entry.get("result") in {"pass", "pass-with-findings"}
        and entry.get("synthetic_data") is True
        and _nonempty(entry.get("root_id"))
        and isinstance(systems, list) and len(systems) == 3
    ):
        return False
    for system in systems:
        if not (
            _exact_dict(system, {
                "name", "version", "operator", "operator_identity",
                "evidence_ref", "result", "independently_operated",
            })
            and all(_nonempty(system[key]) for key in ("name", "version", "operator"))
            and valid_g2_identity_ref(system["operator_identity"])
            and valid_g2_report_ref(system["evidence_ref"])
            and system["result"] == "pass"
            and system["independently_operated"] is True
        ):
            return False
    return len({system["operator_identity"] for system in systems}) == 3


def g6_surface_files(root: Path = ROOT) -> tuple[str, ...]:
    relative = (
        "docs/OPERATIONAL_READINESS.md",
        "SECURITY.md",
        "ROADMAP.md",
        "scripts/check_readiness.py",
        "tests/test_readiness.py",
    )
    if any(not (root / path).is_file() for path in relative):
        raise OSError("canonical G6 surface is incomplete")
    return tuple(sorted(relative))


def g6_surface_digest(root: Path = ROOT) -> str:
    return surface_digest_from_bytes(
        [(relative, (root / relative).read_bytes()) for relative in g6_surface_files(root)]
    )


def g6_surface_digest_at_commit(commit: str, root: Path = ROOT) -> str:
    if not reviewed_commit_exists(commit, root):
        raise OSError("reviewed commit is unavailable")
    entries = []
    for relative in g6_surface_files(root):
        result = subprocess.run(
            ["git", "show", f"{commit}:{relative}"], cwd=root,
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise OSError(f"reviewed commit lacks {relative}")
        entries.append((relative, result.stdout))
    return surface_digest_from_bytes(entries)


def _exact_dict(value: object, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _finite_number(value: object) -> bool:
    return type(value) in {int, float} and math.isfinite(value)


def _iso_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None


def _valid_measurement(value: object) -> bool:
    keys = {"metric", "value", "unit", "comparator", "threshold", "evidence_ref"}
    if not _exact_dict(value, keys):
        return False
    return (
        _nonempty(value["metric"])
        and _finite_number(value["value"])
        and _nonempty(value["unit"])
        and value["comparator"] in COMPARATORS
        and _finite_number(value["threshold"])
        and valid_g2_report_ref(value["evidence_ref"])
    )


def _measurement_passes(value: dict[str, object]) -> bool:
    return COMPARATORS[value["comparator"]](value["value"], value["threshold"])


def valid_g6_operational_evidence(
    entry: object, *, today: date | None = None, root: Path = ROOT
) -> bool:
    """Validate complete external G6 report structure and exact bindings."""

    if not valid_external_evidence(entry, today=today) or not isinstance(entry, dict):
        return False
    deployment = entry.get("deployment")
    workload = entry.get("workload")
    window = entry.get("observation_window")
    scopes = entry.get("scopes")
    reviewed_commit = entry.get("reviewed_commit")
    if not (
        entry.get("kind") == "external"
        and valid_g2_report_ref(entry.get("ref"))
        and G6_NON_INDEPENDENT_PRODUCER_RE.search(entry["producer"]) is None
        and valid_g2_identity_ref(entry.get("producer_identity"))
        and entry.get("relationship") == "independent-third-party"
        and isinstance(entry.get("conflicts"), list)
        and entry.get("independence_attestation") == G6_ATTESTATION
        and entry.get("result") in G2_RESULTS
        and isinstance(reviewed_commit, str)
        and re.fullmatch(r"[0-9a-f]{40}", reviewed_commit) is not None
        and _exact_dict(deployment, {
            "deployment_id", "platform", "environment", "artifact_digest",
            "provenance_ref", "deployed_at",
        })
        and all(_nonempty(deployment[key]) for key in ("deployment_id", "platform", "environment"))
        and isinstance(deployment["artifact_digest"], str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", deployment["artifact_digest"]) is not None
        and valid_g2_report_ref(deployment["provenance_ref"])
        and _iso_timestamp(deployment["deployed_at"]) is not None
        and _exact_dict(workload, {
            "name", "dataset_class", "synthetic_data", "volume", "concurrency",
            "duration_seconds", "failure_domain",
        })
        and all(_nonempty(workload[key]) for key in ("name", "dataset_class", "failure_domain"))
        and isinstance(workload["synthetic_data"], bool)
        and all(type(workload[key]) is int and workload[key] > 0 for key in ("volume", "concurrency", "duration_seconds"))
        and _exact_dict(window, {"start", "end"})
        and _iso_timestamp(window["start"]) is not None
        and _iso_timestamp(window["end"]) is not None
        and _iso_timestamp(window["start"]) < _iso_timestamp(window["end"])
        and isinstance(scopes, list)
        and len(scopes) == len(G6_SCOPE)
    ):
        return False
    tokens = []
    for scope in scopes:
        if not _exact_dict(scope, {"scope", "status", "artifacts", "measurements", "findings"}):
            return False
        artifacts = scope["artifacts"]
        measurements = scope["measurements"]
        if not (
            isinstance(scope["scope"], str)
            and scope["status"] in {"pass", "fail"}
            and isinstance(artifacts, list) and artifacts
            and all(valid_g2_report_ref(item) for item in artifacts)
            and isinstance(measurements, list) and measurements
            and all(_valid_measurement(item) for item in measurements)
            and isinstance(scope["findings"], list)
        ):
            return False
        tokens.append(scope["scope"])
    try:
        return (
            len(tokens) == len(set(tokens))
            and set(tokens) == G6_SCOPE
            and entry.get("surface_digest") == g6_surface_digest(root)
            and entry.get("surface_digest") == g6_surface_digest_at_commit(reviewed_commit, root)
        )
    except OSError:
        return False


def qualifying_g6_operational_evidence(
    entry: object, *, today: date | None = None, root: Path = ROOT
) -> bool:
    if not valid_g6_operational_evidence(entry, today=today, root=root):
        return False
    return (
        entry["result"] in {"pass", "pass-with-findings"}
        and all(scope["status"] == "pass" for scope in entry["scopes"])
        and all(
            _measurement_passes(measurement)
            for scope in entry["scopes"]
            for measurement in scope["measurements"]
        )
    )


def markdown_row_cells(line: str) -> list[str] | None:
    if not line.startswith("|") or not line.endswith("|"):
        return None
    return [cell.strip() for cell in line[1:-1].split("|")]


def markdown_value(value: str) -> str:
    while True:
        for marker in ("**", "__", "`"):
            content = value[len(marker) : -len(marker)]
            if (
                value.startswith(marker)
                and value.endswith(marker)
                and bool(content)
                and value[len(marker)] != marker[0]
                and value[-len(marker) - 1] != marker[0]
                and marker not in content
            ):
                value = content
                break
        else:
            return value


def validate_matrix(
    text: str, payload: dict[str, object], reporter: Reporter
) -> None:
    lines = text.splitlines()
    matrix_rows = [
        row for line in lines if (row := markdown_row_cells(line)) is not None
    ]

    version_rows = [
        row for row in matrix_rows if markdown_value(row[0]) == "Version"
    ]
    matrix_versions = [
        markdown_value(row[1]) if len(row) == 2 else None
        for row in version_rows
    ]
    ledger_version = payload.get("project_version")
    reporter.check(
        "matrix project version",
        isinstance(ledger_version, str) and matrix_versions == [ledger_version],
        f"ledger {ledger_version!r}, matrix rows {matrix_versions!r}",
    )

    verdict_rows = [
        row for row in matrix_rows if markdown_value(row[0]) == "Verdict"
    ]
    matrix_verdicts = [
        markdown_value(row[1]) if len(row) == 2 else None
        for row in verdict_rows
    ]
    ledger_verdict = payload.get("verdict")
    reporter.check(
        "matrix verdict",
        isinstance(ledger_verdict, str) and matrix_verdicts == [ledger_verdict],
        f"ledger {ledger_verdict!r}, matrix rows {matrix_verdicts!r}",
    )

    ledger_statuses: dict[str, str] = {}
    ledger_rows_valid = True
    raw_gates = payload.get("gates")
    if isinstance(raw_gates, list):
        for gate in raw_gates:
            if not isinstance(gate, dict):
                ledger_rows_valid = False
                continue
            gate_id = gate.get("id")
            status = gate.get("status")
            if (
                not isinstance(gate_id, str)
                or gate_id not in REQUIRED_GATES
                or not isinstance(status, str)
                or gate_id in ledger_statuses
            ):
                ledger_rows_valid = False
                continue
            ledger_statuses[gate_id] = status
    else:
        ledger_rows_valid = False

    gate_rows = [
        row for row in matrix_rows if re.fullmatch(r"G\d+", markdown_value(row[0]))
    ]
    matrix_statuses: dict[str, str] = {}
    matrix_rows_valid = True
    for row in gate_rows:
        if len(row) != 5:
            matrix_rows_valid = False
            continue
        gate_id = markdown_value(row[0])
        status = markdown_value(row[2])
        if gate_id not in REQUIRED_GATES or gate_id in matrix_statuses:
            matrix_rows_valid = False
            continue
        matrix_statuses[gate_id] = status

    statuses_match = (
        ledger_rows_valid
        and matrix_rows_valid
        and len(gate_rows) == len(REQUIRED_GATES)
        and set(ledger_statuses) == REQUIRED_GATES
        and matrix_statuses == ledger_statuses
    )
    reporter.check(
        "matrix gate statuses",
        statuses_match,
        f"ledger {ledger_statuses!r}, matrix {matrix_statuses!r}; "
        "all rows must be unique, well formed, and exact",
    )

    ledger_gates = {
        gate.get("id"): gate
        for gate in raw_gates
        if isinstance(gate, dict) and isinstance(gate.get("id"), str)
    } if isinstance(raw_gates, list) else {}
    matrix_gate_rows = {
        markdown_value(row[0]): row
        for row in gate_rows
        if len(row) == 5 and markdown_value(row[0]) in REQUIRED_GATES
    }
    for gate_id in sorted(REQUIRED_GATES):
        gate = ledger_gates.get(gate_id)
        row = matrix_gate_rows.get(gate_id)
        criterion = gate.get("criterion") if isinstance(gate, dict) else None
        reporter.check(
            f"{gate_id} matrix criterion",
            isinstance(criterion, str)
            and row is not None
            and markdown_value(row[1]) == criterion,
            f"{gate_id} matrix criterion exactly matches the readiness ledger",
        )

    g2_gate = next(
        (gate for gate in raw_gates if isinstance(gate, dict) and gate.get("id") == "G2"),
        None,
    ) if isinstance(raw_gates, list) else None
    g2_row = next(
        (row for row in gate_rows if len(row) == 5 and markdown_value(row[0]) == "G2"),
        None,
    )
    reporter.check(
        "G2 matrix current evidence",
        g2_row is not None and markdown_value(g2_row[3]) == G2_MATRIX_CURRENT_EVIDENCE,
        "G2 matrix uses the canonical internal-evidence statement",
    )
    reporter.check(
        "G2 matrix next evidence",
        g2_row is not None and markdown_value(g2_row[4]) == G2_MATRIX_NEXT_EVIDENCE,
        "G2 matrix requires dated independent external review",
    )
    g6_gate = next(
        (gate for gate in raw_gates if isinstance(gate, dict) and gate.get("id") == "G6"),
        None,
    ) if isinstance(raw_gates, list) else None
    g6_row = next(
        (row for row in gate_rows if len(row) == 5 and markdown_value(row[0]) == "G6"),
        None,
    )
    reporter.check(
        "G6 matrix current evidence",
        g6_row is not None and markdown_value(g6_row[3]) == G6_MATRIX_CURRENT_EVIDENCE,
        "G6 matrix states absence of complete measured independent evidence",
    )
    reporter.check(
        "G6 matrix next evidence",
        g6_row is not None and markdown_value(g6_row[4]) == G6_MATRIX_NEXT_EVIDENCE,
        "G6 matrix requires all ten measured operational scopes",
    )


def validate_ledger(
    payload: dict[str, object], repository_version: str, reporter: Reporter
) -> None:
    schema_version = payload.get("schema_version")
    reporter.check(
        "schema version",
        type(schema_version) is int and schema_version == 1,
        f"expected 1, got {schema_version!r}",
    )

    project_version = payload.get("project_version")
    reporter.check(
        "project version",
        isinstance(project_version, str) and project_version == repository_version,
        f"ledger {project_version!r}, repository {repository_version!r}",
    )

    verdict = payload.get("verdict")
    last_reviewed = payload.get("last_reviewed")
    reporter.check(
        "verdict",
        isinstance(verdict, str) and verdict in VERDICTS,
        f"value {verdict!r}",
    )
    reporter.check("last-review date", valid_iso_date(last_reviewed), f"value {last_reviewed!r}")

    raw_gates = payload.get("gates")
    gates = raw_gates if isinstance(raw_gates, list) else []
    ids = [gate.get("id") for gate in gates if isinstance(gate, dict)]
    id_set = {gate_id for gate_id in ids if isinstance(gate_id, str)}
    gate_ids_valid = (
        isinstance(raw_gates, list)
        and len(ids) == len(gates)
        and len(ids) == len(id_set)
        and id_set == REQUIRED_GATES
    )
    reporter.check(
        "gate IDs",
        gate_ids_valid,
        f"expected {sorted(REQUIRED_GATES)}, got {ids!r}",
    )

    all_pass = True
    for gate_index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            all_pass = False
            reporter.check(f"gate[{gate_index}] structure", False, "gate must be an object")
            continue
        gate_id = gate.get("id", "<missing>")
        gate_id_valid = isinstance(gate_id, str)
        reporter.check(
            f"gate[{gate_index}] ID",
            gate_id_valid,
            f"ID must be a string, got {gate_id!r}",
        )
        if not gate_id_valid:
            all_pass = False
        prefix = f"gate {gate_id}"
        name = gate.get("name")
        gate_class = gate.get("class")
        status = gate.get("status")
        criterion = gate.get("criterion")
        evidence = gate.get("evidence")
        fields_valid = (
            isinstance(name, str)
            and bool(name.strip())
            and isinstance(gate_class, str)
            and gate_class in CLASSES
            and isinstance(status, str)
            and status in STATUSES
            and isinstance(criterion, str)
            and bool(criterion.strip())
            and isinstance(evidence, list)
            and bool(evidence)
        )
        reporter.check(
            f"{prefix} fields",
            fields_valid,
            "name, class, status, criterion, and non-empty evidence are valid",
        )
        if not fields_valid:
            all_pass = False

        expected_class = EXPECTED_CLASSES.get(gate_id) if gate_id_valid else None
        class_binding_valid = expected_class is None or gate_class == expected_class
        reporter.check(
            f"{prefix} expected class",
            class_binding_valid,
            f"required class is {expected_class!r}, got {gate_class!r}",
        )
        if not class_binding_valid:
            all_pass = False

        valid_external_entries = 0
        valid_g2_reviews = 0
        valid_g3_reports = 0
        g4_external_entries: list[dict[str, object]] = []
        valid_g5_reports = 0
        valid_g6_reports = 0
        evidence_valid = isinstance(evidence, list)
        if isinstance(evidence, list):
            for index, entry in enumerate(evidence):
                entry_name = f"{prefix} evidence {index + 1}"
                if not isinstance(entry, dict):
                    reporter.check(entry_name, False, "evidence must be an object")
                    evidence_valid = False
                    continue
                kind = entry.get("kind")
                if kind == "repository":
                    ref = entry.get("ref")
                    valid_ref = isinstance(ref, str) and bool(ref)
                    path = ROOT / ref if valid_ref else ROOT
                    try:
                        resolved = path.resolve()
                        within_root = resolved == ROOT or ROOT in resolved.parents
                        exists = path.is_file()
                    except (OSError, RuntimeError, ValueError):
                        within_root = False
                        exists = False
                    try:
                        absolute = Path(ref).is_absolute() if valid_ref else True
                    except (OSError, RuntimeError, ValueError):
                        absolute = True
                    repository_valid = valid_ref and not absolute and within_root and exists
                    reporter.check(
                        f"{entry_name} repository evidence",
                        repository_valid,
                        f"reference {ref!r} must be an existing repository-relative file",
                    )
                    evidence_valid = evidence_valid and repository_valid
                elif kind == "external":
                    reference_valid = valid_external_ref(entry.get("ref"))
                    producer = entry.get("producer")
                    producer_valid = (
                        isinstance(producer, str)
                        and bool(producer.strip())
                        and GENERIC_NON_INDEPENDENT_PRODUCER_RE.search(producer) is None
                    )
                    observed_valid = (
                        valid_iso_date(entry.get("observed"))
                        and date.fromisoformat(entry["observed"]) <= date.today()
                    )
                    if gate_id == "G2" and isinstance(producer, str):
                        producer_valid = producer_valid and (
                            G2_NON_INDEPENDENT_PRODUCER_RE.search(producer) is None
                        )
                    if gate_id == "G6" and isinstance(producer, str):
                        producer_valid = producer_valid and (
                            G6_NON_INDEPENDENT_PRODUCER_RE.search(producer) is None
                        )
                    reporter.check(
                        f"{entry_name} external reference",
                        reference_valid,
                        "reference must be an https URL or urn",
                    )
                    reporter.check(
                        f"{entry_name} producer",
                        producer_valid,
                        "independent external producer is required; structural validation cannot prove real-world independence",
                    )
                    reporter.check(
                        f"{entry_name} observed date",
                        observed_valid,
                        "observed must be an ISO YYYY-MM-DD date that is not future-dated",
                    )
                    entry_valid = valid_external_evidence(entry)
                    if gate_id == "G2":
                        entry_valid = valid_g2_review_evidence(entry, root=ROOT)
                    elif gate_id == "G6":
                        entry_valid = valid_g6_operational_evidence(entry, root=ROOT)
                    evidence_valid = evidence_valid and entry_valid
                    if entry_valid:
                        valid_external_entries += 1
                    if gate_id == "G2" and qualifying_g2_review_evidence(entry, root=ROOT):
                        valid_g2_reviews += 1
                    if gate_id == "G3" and qualifying_g3_security_evidence(entry, root=ROOT):
                        valid_g3_reports += 1
                    if gate_id == "G4":
                        g4_external_entries.append(entry)
                    if gate_id == "G5" and qualifying_g5_interoperability_evidence(entry, root=ROOT):
                        valid_g5_reports += 1
                    if gate_id == "G6" and qualifying_g6_operational_evidence(entry, root=ROOT):
                        valid_g6_reports += 1
                else:
                    reporter.check(entry_name, False, "kind must be repository or external")
                    evidence_valid = False
        reporter.check(f"{prefix} evidence", evidence_valid, "all evidence entries are valid")
        if not evidence_valid:
            all_pass = False

        qualifying_external = (
            valid_g2_reviews if gate_id == "G2"
            else valid_g3_reports if gate_id == "G3"
            else int(qualifying_g4_evidence(g4_external_entries, root=ROOT)) if gate_id == "G4"
            else valid_g5_reports if gate_id == "G5"
            else valid_g6_reports if gate_id == "G6"
            else valid_external_entries
        )
        external_pass_valid = gate_class != "external" or status != "PASS" or qualifying_external > 0
        reporter.check(
            f"{prefix} external PASS evidence",
            external_pass_valid,
            "external evidence: every external gate requires its gate-specific independent, commit-bound evidence schema",
        )
        if not external_pass_valid:
            all_pass = False
        if status != "PASS":
            all_pass = False

    reporter.check("PROD_READY verdict", verdict != "PROD_READY" or (gate_ids_valid and all_pass), "every required gate must be PASS")


def main() -> int:
    reporter = Reporter()
    try:
        payload = read_ledger()
        repository_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        reporter.check("readiness ledger", False, str(error))
        return reporter.finish()
    try:
        matrix_text = MATRIX.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        reporter.check("production readiness matrix", False, str(error))
        return reporter.finish()
    validate_ledger(payload, repository_version, reporter)
    validate_matrix(matrix_text, payload, reporter)
    print(f"Current verdict: {payload.get('verdict', '<missing>')}")
    return reporter.finish()


if __name__ == "__main__":
    sys.exit(main())
