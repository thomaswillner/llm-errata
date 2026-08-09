#!/usr/bin/env python3
"""Validate the repository's production-readiness evidence ledger."""

from __future__ import annotations

import json
import re
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
NON_INDEPENDENT_PRODUCER_RE = re.compile(
    r"(?:^|[\s:_-])(local|self|maintainer|agent|repository|repo)(?:$|[\s:_-])",
    re.IGNORECASE,
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
    return value.startswith("urn:") or (parsed.scheme == "https" and bool(parsed.netloc))


def markdown_row_cells(line: str) -> list[str] | None:
    if not line.startswith("|") or not line.endswith("|"):
        return None
    return [cell.strip() for cell in line[1:-1].split("|")]


def markdown_value(value: str) -> str:
    while True:
        for marker in ("**", "__", "`"):
            if (
                value.startswith(marker)
                and value.endswith(marker)
                and len(value) > 2 * len(marker)
                and value.count(marker) % 2 == 0
            ):
                value = value[len(marker) : -len(marker)]
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
                        and NON_INDEPENDENT_PRODUCER_RE.search(producer) is None
                    )
                    observed_valid = valid_iso_date(entry.get("observed"))
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
                        "observed must be an ISO YYYY-MM-DD date",
                    )
                    entry_valid = reference_valid and producer_valid and observed_valid
                    evidence_valid = evidence_valid and entry_valid
                    if entry_valid:
                        valid_external_entries += 1
                else:
                    reporter.check(entry_name, False, "kind must be repository or external")
                    evidence_valid = False
        reporter.check(f"{prefix} evidence", evidence_valid, "all evidence entries are valid")
        if not evidence_valid:
            all_pass = False

        external_pass_valid = gate_class != "external" or status != "PASS" or valid_external_entries > 0
        reporter.check(
            f"{prefix} external PASS evidence",
            external_pass_valid,
            "external PASS requires independently observed external evidence",
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
