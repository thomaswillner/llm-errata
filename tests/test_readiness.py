"""Self-tests for the production-readiness ledger checker."""

from __future__ import annotations

import json
import unittest

from scripts.check_readiness import markdown_value
from tests.support import (
    EXIT_FAIL,
    EXIT_OK,
    check_after,
    repo_copy,
    rewrite,
    run_checker,
)


SCRIPT = "check_readiness.py"


class ReadinessCheckerPasses(unittest.TestCase):
    def test_current_not_ready_ledger_is_honest(self) -> None:
        with repo_copy() as root:
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_OK, result.stdout)

    def test_consistently_formatted_canonical_matrix_cells_are_accepted(self) -> None:
        def mutate(root):
            path = root / "PRODUCTION_READINESS.md"
            lines = path.read_text(encoding="utf-8").splitlines()
            formatted = []
            for line in lines:
                if line.startswith("| Version |"):
                    formatted.append("| **Version** | `**0.3.0**` |")
                elif line.startswith("| Verdict |"):
                    formatted.append("| `Verdict` | __**NOT_PROD_READY**__ |")
                elif line.startswith("| G"):
                    cells = line[1:-1].split("|")
                    cells[0] = f" `**{cells[0].strip()}**` "
                    cells[2] = f" __{cells[2].strip()}__ "
                    formatted.append("|" + "|".join(cells) + "|")
                else:
                    formatted.append(line)
            path.write_text("\n".join(formatted) + "\n", encoding="utf-8")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_OK, result.stdout)
        self.assertEqual(result.stderr, "")

    def test_partial_or_unbalanced_decoration_is_not_canonicalized(self) -> None:
        self.assertEqual(markdown_value("**G2"), "**G2")
        self.assertEqual(markdown_value("G2**"), "G2**")
        self.assertEqual(markdown_value("**G2** trailing"), "**G2** trailing")

    def test_ambiguous_delimiter_runs_are_not_canonicalized(self) -> None:
        for value in (
            "***G2**",
            "**G2***",
            "__G2___",
            "`G2```",
            "```G2`",
            "```G2```",
        ):
            with self.subTest(value=value):
                self.assertEqual(markdown_value(value), value)


class ReadinessCheckerFailsClosed(unittest.TestCase):
    def _mutated(self, mutate):
        def apply(root):
            path = root / "readiness" / "production-readiness.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            mutate(payload)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        return check_after(SCRIPT, apply)

    def assert_rejected_without_traceback(self, result, rule: str) -> None:
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn(rule, result.stdout)
        self.assertEqual(result.stderr, "")

    def test_non_integer_schema_versions_are_rejected(self) -> None:
        for invalid in (True, 1.0):
            with self.subTest(schema_version=invalid):
                result = self._mutated(
                    lambda payload, value=invalid: payload.update(schema_version=value)
                )
                self.assert_rejected_without_traceback(result, "schema version")

    def test_unhashable_gate_ids_are_rejected_without_traceback(self) -> None:
        for invalid in (["G1"], {"value": "G1"}):
            with self.subTest(gate_id=invalid):
                def mutate(payload, value=invalid):
                    payload["gates"][0]["id"] = value

                result = self._mutated(mutate)
                self.assert_rejected_without_traceback(result, "gate[0] ID")

    def test_non_string_scalar_gate_ids_are_rejected_without_traceback(self) -> None:
        for invalid in (None, True, 1, 1.0):
            with self.subTest(gate_id=invalid):
                def mutate(payload, value=invalid):
                    payload["gates"][0]["id"] = value

                result = self._mutated(mutate)
                self.assert_rejected_without_traceback(result, "gate[0] ID")

    def test_project_version_drift_is_rejected(self) -> None:
        result = self._mutated(lambda payload: payload.update(project_version="9.9.9"))
        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("project version", result.stdout)

    def test_matrix_project_version_contradiction_is_rejected(self) -> None:
        def mutate(root):
            rewrite(
                root / "PRODUCTION_READINESS.md",
                "| Version | 0.3.0 |",
                "| Version | 9.9.9 |",
            )

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "matrix project version")

    def test_formatted_duplicate_matrix_project_version_is_rejected(self) -> None:
        def mutate(root):
            path = root / "PRODUCTION_READINESS.md"
            with path.open("a", encoding="utf-8") as handle:
                handle.write("| **Version** | **9.9.9** |\n")

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "matrix project version")

    def test_matrix_verdict_contradiction_is_rejected(self) -> None:
        def mutate(root):
            rewrite(
                root / "PRODUCTION_READINESS.md",
                "| Verdict | **NOT_PROD_READY** |",
                "| Verdict | **PROD_READY** |",
            )

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "matrix verdict")

    def test_bold_duplicate_matrix_verdict_is_rejected(self) -> None:
        def mutate(root):
            path = root / "PRODUCTION_READINESS.md"
            with path.open("a", encoding="utf-8") as handle:
                handle.write("| **Verdict** | **PROD_READY** |\n")

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "matrix verdict")

    def test_matrix_gate_status_contradiction_is_rejected(self) -> None:
        def mutate(root):
            path = root / "PRODUCTION_READINESS.md"
            lines = path.read_text(encoding="utf-8").splitlines()
            matches = [
                index for index, line in enumerate(lines) if line.startswith("| G2 |")
            ]
            if len(matches) != 1:
                raise AssertionError(f"expected one G2 matrix row, got {len(matches)}")
            index = matches[0]
            if "| `BLOCKED` |" not in lines[index]:
                raise AssertionError("G2 matrix row does not contain BLOCKED status")
            lines[index] = lines[index].replace("| `BLOCKED` |", "| `PASS` |", 1)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "matrix gate statuses")

    def test_code_formatted_duplicate_matrix_gate_is_rejected(self) -> None:
        def mutate(root):
            path = root / "PRODUCTION_READINESS.md"
            lines = path.read_text(encoding="utf-8").splitlines()
            matches = [line for line in lines if line.startswith("| G2 |")]
            if len(matches) != 1:
                raise AssertionError(f"expected one G2 matrix row, got {len(matches)}")
            duplicate = matches[0].replace("| G2 |", "| `G2` |", 1)
            duplicate = duplicate.replace("| `BLOCKED` |", "| `PASS` |", 1)
            path.write_text("\n".join(lines + [duplicate]) + "\n", encoding="utf-8")

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "matrix gate statuses")

    def test_missing_matrix_project_version_is_rejected(self) -> None:
        def mutate(root):
            rewrite(root / "PRODUCTION_READINESS.md", "| Version | 0.3.0 |\n", "")

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "matrix project version")

    def test_duplicate_matrix_verdict_is_rejected(self) -> None:
        def mutate(root):
            row = "| Verdict | **NOT_PROD_READY** |"
            rewrite(root / "PRODUCTION_READINESS.md", row, f"{row}\n{row}")

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "matrix verdict")

    def test_malformed_matrix_gate_row_is_rejected(self) -> None:
        def mutate(root):
            path = root / "PRODUCTION_READINESS.md"
            lines = path.read_text(encoding="utf-8").splitlines()
            matches = [
                index for index, line in enumerate(lines) if line.startswith("| G2 |")
            ]
            if len(matches) != 1:
                raise AssertionError(f"expected one G2 matrix row, got {len(matches)}")
            index = matches[0]
            lines[index] = lines[index].replace("| `BLOCKED` |", "| BLOCKED ", 1)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "matrix gate statuses")

    def test_missing_required_gate_is_rejected(self) -> None:
        def mutate(payload):
            payload["gates"] = [gate for gate in payload["gates"] if gate["id"] != "G6"]

        result = self._mutated(mutate)
        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("gate IDs", result.stdout)

    def test_missing_repository_evidence_is_rejected(self) -> None:
        def mutate(payload):
            payload["gates"][0]["evidence"][0]["ref"] = "MISSING.md"

        result = self._mutated(mutate)
        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("repository evidence", result.stdout)

    def test_prod_ready_with_a_blocked_gate_is_rejected(self) -> None:
        result = self._mutated(lambda payload: payload.update(verdict="PROD_READY"))
        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("PROD_READY", result.stdout)

    def test_required_external_gate_cannot_be_reclassified_internal(self) -> None:
        def mutate(payload):
            for gate in payload["gates"]:
                gate["class"] = "internal"
                gate["status"] = "PASS"
            payload["verdict"] = "PROD_READY"

        result = self._mutated(mutate)
        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("expected class", result.stdout)

    def test_external_pass_without_independent_evidence_is_rejected(self) -> None:
        def mutate(payload):
            gate = next(gate for gate in payload["gates"] if gate["id"] == "G2")
            gate["status"] = "PASS"

        result = self._mutated(mutate)
        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("external evidence", result.stdout)

    def test_external_evidence_without_producer_is_rejected(self) -> None:
        def mutate(payload):
            gate = next(gate for gate in payload["gates"] if gate["id"] == "G2")
            gate["evidence"].append(
                {"kind": "external", "ref": "urn:example:review", "observed": "2026-08-09"}
            )

        result = self._mutated(mutate)
        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("producer", result.stdout)

    def test_external_evidence_without_iso_date_is_rejected(self) -> None:
        def mutate(payload):
            gate = next(gate for gate in payload["gates"] if gate["id"] == "G2")
            gate["evidence"].append(
                {"kind": "external", "ref": "urn:example:review", "producer": "Independent reviewer"}
            )

        result = self._mutated(mutate)
        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("observed date", result.stdout)

    def test_local_producer_is_not_independent_external_evidence(self) -> None:
        def mutate(payload):
            gate = next(gate for gate in payload["gates"] if gate["id"] == "G2")
            gate["status"] = "PASS"
            gate["evidence"].append(
                {
                    "kind": "external",
                    "ref": "urn:example:review",
                    "producer": "local implementer",
                    "observed": "2026-08-09",
                }
            )

        result = self._mutated(mutate)
        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("independence", result.stdout)


if __name__ == "__main__":
    unittest.main()
