#!/usr/bin/env python3
"""Validate the repository's production-readiness evidence ledger."""

from __future__ import annotations

import json
import re
import hashlib
import subprocess
import sys
from datetime import date
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
    r"(?:^|[\s:_-])(local|self|maintainer|agent|repository|repo)(?:$|[\s:_-])",
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
    "tests/test_cli.py",
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
G2_MATRIX_CURRENT_EVIDENCE = (
    "Semantic probes are internally implemented, but Phase 2 remains incomplete: "
    "`errata quarantine` and vectors for key rotation, concurrency, invalid targets, "
    "and confidentiality are absent; receipt-binding vectors are partial; no qualifying independent review is recorded."
)
G2_MATRIX_NEXT_EVIDENCE = (
    "Complete listed Phase 2 gaps, then record dated independent external "
    "conformance-review result covering complete Phase 2 surface."
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


def g2_surface_digest(root: Path = ROOT) -> str:
    return surface_digest_from_bytes(
        [(relative, (root / relative).read_bytes()) for relative in g2_surface_files(root)]
    )


def g2_surface_digest_at_commit(commit: str, root: Path = ROOT) -> str:
    if not reviewed_commit_exists(commit, root):
        raise OSError("reviewed commit is unavailable")
    entries = []
    for relative in g2_surface_files(root):
        result = subprocess.run(
            ["git", "show", f"{commit}:{relative}"], cwd=root, capture_output=True, check=False
        )
        if result.returncode != 0:
            raise OSError(f"reviewed commit lacks {relative}")
        entries.append((relative, result.stdout))
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

    g2_gate = next(
        (gate for gate in raw_gates if isinstance(gate, dict) and gate.get("id") == "G2"),
        None,
    ) if isinstance(raw_gates, list) else None
    g2_row = next(
        (row for row in gate_rows if len(row) == 5 and markdown_value(row[0]) == "G2"),
        None,
    )
    g2_criterion = g2_gate.get("criterion") if isinstance(g2_gate, dict) else None
    reporter.check(
        "G2 matrix criterion",
        isinstance(g2_criterion, str)
        and g2_row is not None
        and markdown_value(g2_row[1]) == g2_criterion,
        "G2 matrix criterion exactly matches the readiness ledger",
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
                    evidence_valid = evidence_valid and entry_valid
                    if entry_valid:
                        valid_external_entries += 1
                    if gate_id == "G2" and qualifying_g2_review_evidence(entry, root=ROOT):
                        valid_g2_reviews += 1
                else:
                    reporter.check(entry_name, False, "kind must be repository or external")
                    evidence_valid = False
        reporter.check(f"{prefix} evidence", evidence_valid, "all evidence entries are valid")
        if not evidence_valid:
            all_pass = False

        external_pass_valid = (
            gate_class != "external"
            or status != "PASS"
            or (valid_g2_reviews > 0 if gate_id == "G2" else valid_external_entries > 0)
        )
        reporter.check(
            f"{prefix} external PASS evidence",
            external_pass_valid,
            "G2 PASS requires a complete independent Phase 2 review; other external PASS gates require independently observed external evidence",
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
