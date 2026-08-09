"""Self-tests for the production-readiness ledger checker."""

from __future__ import annotations

import json
import unittest

from tests.support import EXIT_FAIL, EXIT_OK, check_after, repo_copy, run_checker


SCRIPT = "check_readiness.py"


class ReadinessCheckerPasses(unittest.TestCase):
    def test_current_not_ready_ledger_is_honest(self) -> None:
        with repo_copy() as root:
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_OK, result.stdout)


class ReadinessCheckerFailsClosed(unittest.TestCase):
    def _mutated(self, mutate):
        def apply(root):
            path = root / "readiness" / "production-readiness.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            mutate(payload)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        return check_after(SCRIPT, apply)

    def test_project_version_drift_is_rejected(self) -> None:
        result = self._mutated(lambda payload: payload.update(project_version="9.9.9"))
        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("project version", result.stdout)

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
