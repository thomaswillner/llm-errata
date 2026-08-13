"""Self-tests for the production-readiness ledger checker."""

from __future__ import annotations

import json
import copy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_readiness import (
    G6_SCOPE,
    g2_surface_digest,
    g2_surface_digest_at_commit,
    g2_surface_files,
    g6_surface_digest,
    qualifying_g6_operational_evidence,
    qualifying_g2_review_evidence,
    valid_external_evidence,
    valid_g2_review_evidence,
    valid_g6_operational_evidence,
    markdown_value,
)
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
    def test_cryptography_qualification_foregrounds_refusal_evidence(self) -> None:
        qualification = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "CRYPTOGRAPHY_QUALIFICATION.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "non-canonical scalar",
            "malformed public-key and signature lengths",
            "tampered message",
            "tampered signature",
            "wrong public key",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, qualification)

    def test_current_not_ready_ledger_is_honest(self) -> None:
        with repo_copy() as root:
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_OK, result.stdout)

    def test_g2_surface_includes_checkpoint_contract_and_tests(self) -> None:
        files = set(g2_surface_files())
        self.assertIn("prototype/checkpoints.py", files)
        self.assertIn("tests/test_checkpoints.py", files)

    def test_g6_complete_measured_report_is_commit_and_deployment_bound(self) -> None:
        with repo_copy() as source, tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repository"
            shutil.copytree(source, root)
            for command in (
                ("git", "init"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Readiness tests"),
                ("git", "add", "."),
                ("git", "commit", "-m", "operational baseline"),
            ):
                subprocess.run(command, cwd=root, check=True, capture_output=True)
            commit = subprocess.run(
                ("git", "rev-parse", "HEAD"), cwd=root, check=True,
                capture_output=True, text=True,
            ).stdout.strip()
            report = self._complete_g6_report(root, commit)
            self.assertTrue(valid_g6_operational_evidence(report, root=root))
            self.assertTrue(qualifying_g6_operational_evidence(report, root=root))

    def test_g6_failed_comparator_is_valid_but_not_qualifying(self) -> None:
        with repo_copy() as source, tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repository"
            shutil.copytree(source, root)
            for command in (
                ("git", "init"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Readiness tests"),
                ("git", "add", "."),
                ("git", "commit", "-m", "operational baseline"),
            ):
                subprocess.run(command, cwd=root, check=True, capture_output=True)
            commit = subprocess.run(
                ("git", "rev-parse", "HEAD"), cwd=root, check=True,
                capture_output=True, text=True,
            ).stdout.strip()
            report = self._complete_g6_report(root, commit)
            report["scopes"][0]["measurements"][0]["value"] = 11
            self.assertTrue(valid_g6_operational_evidence(report, root=root))
            self.assertFalse(qualifying_g6_operational_evidence(report, root=root))

    def test_g6_report_rejects_missing_or_ambiguous_measurement_evidence(self) -> None:
        with repo_copy() as source, tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repository"
            shutil.copytree(source, root)
            for command in (
                ("git", "init"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Readiness tests"),
                ("git", "add", "."),
                ("git", "commit", "-m", "operational baseline"),
            ):
                subprocess.run(command, cwd=root, check=True, capture_output=True)
            commit = subprocess.run(
                ("git", "rev-parse", "HEAD"), cwd=root, check=True,
                capture_output=True, text=True,
            ).stdout.strip()
            baseline = self._complete_g6_report(root, commit)

            mutations = {
                "nine scopes": lambda report: report["scopes"].pop(),
                "duplicate scope": lambda report: report["scopes"].__setitem__(
                    1, copy.deepcopy(report["scopes"][0])
                ),
                "no measurements": lambda report: report["scopes"][0].update(measurements=[]),
                "no artifacts": lambda report: report["scopes"][0].update(artifacts=[]),
                "missing threshold": lambda report: report["scopes"][0]["measurements"][0].pop("threshold"),
                "nonfinite value": lambda report: report["scopes"][0]["measurements"][0].update(value=float("nan")),
                "unitless": lambda report: report["scopes"][0]["measurements"][0].update(unit=""),
                "invalid comparator": lambda report: report["scopes"][0]["measurements"][0].update(comparator="approximately"),
                "missing platform": lambda report: report["deployment"].update(platform=""),
                "missing failure domain": lambda report: report["workload"].update(failure_domain=""),
                "zero volume": lambda report: report["workload"].update(volume=0),
                "reversed window": lambda report: report["observation_window"].update(
                    start="2026-08-12T11:00:00Z", end="2026-08-12T10:00:00Z"
                ),
            }
            for name, mutate in mutations.items():
                with self.subTest(name=name):
                    report = copy.deepcopy(baseline)
                    mutate(report)
                    self.assertFalse(valid_g6_operational_evidence(report, root=root))

    @staticmethod
    def _complete_g6_report(root: Path, commit: str) -> dict[str, object]:
        return {
            "kind": "external",
            "ref": "https://reviews.example.org/operations/report-1",
            "producer": "Independent Reliability Laboratory",
            "producer_identity": "https://identity.example.org/reliability-lab",
            "observed": "2026-08-12",
            "relationship": "independent-third-party",
            "conflicts": [],
            "independence_attestation": "llm-errata-independent-operational-review-v1",
            "result": "pass-with-findings",
            "reviewed_commit": commit,
            "surface_digest": g6_surface_digest(root),
            "deployment": {
                "deployment_id": "deploy-20260812-01",
                "platform": "linux-amd64",
                "environment": "production-like-isolated",
                "artifact_digest": "sha256:" + "a" * 64,
                "provenance_ref": "https://evidence.example.org/build/1",
                "deployed_at": "2026-08-12T08:00:00Z",
            },
            "workload": {
                "name": "synthetic-correction-mix",
                "dataset_class": "synthetic",
                "synthetic_data": True,
                "volume": 1000,
                "concurrency": 10,
                "duration_seconds": 600,
                "failure_domain": "single-region-store-loss",
            },
            "observation_window": {
                "start": "2026-08-12T08:00:00Z",
                "end": "2026-08-12T10:00:00Z",
            },
            "scopes": [
                {
                    "scope": scope,
                    "status": "pass",
                    "artifacts": [f"https://evidence.example.org/{scope}/raw"],
                    "measurements": [{
                        "metric": f"{scope}.gate",
                        "value": 1,
                        "unit": "count",
                        "comparator": "<=",
                        "threshold": 10,
                        "evidence_ref": f"https://evidence.example.org/{scope}/measurement",
                    }],
                    "findings": [],
                }
                for scope in sorted(G6_SCOPE)
            ],
        }

    def test_generic_external_evidence_allows_https_root_url(self) -> None:
        self.assertTrue(
            valid_external_evidence(
                {
                    "ref": "https://reviewer.example.org",
                    "producer": "Independent Systems Lab",
                    "observed": "2026-08-12",
                }
            )
        )

    def test_g2_review_binds_current_committed_surface(self) -> None:
        with repo_copy() as source, tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repository"
            shutil.copytree(source, root)
            for command in (
                ("git", "init"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Readiness tests"),
                ("git", "add", "."),
                ("git", "commit", "-m", "surface baseline"),
            ):
                subprocess.run(command, cwd=root, check=True, capture_output=True)
            commit = subprocess.run(
                ("git", "rev-parse", "HEAD"), cwd=root, check=True,
                capture_output=True, text=True,
            ).stdout.strip()
            review = self._complete_review(root, commit)
            self.assertTrue(valid_g2_review_evidence(review, root=root))
            controller = root / "prototype" / "controller.py"
            controller.write_bytes(controller.read_bytes() + b"\n# digest mutation\n")
            self.assertNotEqual(g2_surface_digest(root), review["surface_digest"])
            self.assertFalse(valid_g2_review_evidence(review, root=root))

    def test_g2_review_requires_git_metadata(self) -> None:
        with repo_copy() as root:
            review = self._complete_review(root, "a" * 40)
            self.assertFalse(valid_g2_review_evidence(review, root=root))

    def test_g2_review_rejects_nonexistent_commit(self) -> None:
        with repo_copy() as source, tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repository"
            shutil.copytree(source, root)
            for command in (
                ("git", "init"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Readiness tests"),
                ("git", "add", "."),
                ("git", "commit", "-m", "surface baseline"),
            ):
                subprocess.run(command, cwd=root, check=True, capture_output=True)
            self.assertFalse(valid_g2_review_evidence(self._complete_review(root, "a" * 40), root=root))

    @staticmethod
    def _complete_review(root: Path, commit: str) -> dict[str, object]:
        return {
            "kind": "external",
            "ref": "https://reviews.example.org/phase2/report",
            "producer": "Independent Systems Lab",
            "observed": "2026-08-12",
            "review_type": "phase2-conformance",
            "reviewed_commit": commit,
            "scope": [
                "schemas", "vectors", "cli", "adapter-interface",
                "transactional-store", "substrate-evidence", "semantic-probes",
                "security-boundaries",
            ],
            "result": "pass-with-findings",
            "relationship": "independent-third-party",
            "conflicts": [],
            "producer_identity": "https://identity.example.org/reviewer",
            "independence_attestation": "llm-errata-independent-review-v1",
            "surface_digest": g2_surface_digest(root),
        }

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

    def test_g2_matrix_criterion_drift_is_rejected(self) -> None:
        def mutate(root):
            rewrite(
                root / "PRODUCTION_READINESS.md",
                "Complete Phase 2 implementation, including provider-neutral semantic probes, and an independent reviewer evaluates the complete conformance surface.",
                "Internal Phase 2 implementation is enough.",
            )

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "G2 matrix criterion")

    def test_g2_matrix_current_evidence_drift_is_rejected(self) -> None:
        def mutate(root):
            rewrite(
                root / "PRODUCTION_READINESS.md",
                "Phase 2 implementation includes conflict-disclosed remediation for split-view equivocation and unsupported empty enumeration, plus schemas, checkpoints, semantic probes, key rotation, invalid-target, confidentiality, and receipt binding; no qualifying independent review is recorded.",
                "local tests prove readiness.",
            )

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "G2 matrix current evidence")

    def test_internal_phase2_completion_cannot_upgrade_g2(self) -> None:
        def mutate(payload):
            gate = next(gate for gate in payload["gates"] if gate["id"] == "G2")
            gate["status"] = "PASS"

        result = self._mutated(mutate)
        self.assert_rejected_without_traceback(result, "G2 external PASS evidence")

    def test_g2_matrix_next_evidence_drift_is_rejected(self) -> None:
        def mutate(root):
            rewrite(
                root / "PRODUCTION_READINESS.md",
                "Dated independent external conformance-review result covering the exact complete Phase 2 surface after remediation.",
                "Local tests are enough.",
            )

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "G2 matrix next evidence")

    def test_g6_matrix_current_evidence_drift_is_rejected(self) -> None:
        def mutate(root):
            rewrite(
                root / "PRODUCTION_READINESS.md",
                "No independent report binds an exact commit and deployment to passing measured comparators for all ten operational scopes.",
                "Internal tests prove operations readiness.",
            )

        result = check_after(SCRIPT, mutate)
        self.assert_rejected_without_traceback(result, "G6 matrix current evidence")

    def test_generic_external_record_does_not_qualify_as_g6_evidence(self) -> None:
        def mutate(payload):
            gate = next(gate for gate in payload["gates"] if gate["id"] == "G6")
            gate["evidence"].append({
                "kind": "external",
                "ref": "https://reviews.example.org/operations/report",
                "producer": "Independent Reliability Laboratory",
                "observed": "2026-08-12",
            })

        result = self._mutated(mutate)
        self.assert_rejected_without_traceback(result, "G6 evidence")

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

    def test_g2_pass_requires_complete_independent_review_schema(self) -> None:
        def mutate(payload):
            gate = next(gate for gate in payload["gates"] if gate["id"] == "G2")
            gate["status"] = "PASS"
            gate["evidence"].append(
                {
                    "kind": "external",
                    "ref": "https://reviews.example.org/phase2/report",
                    "producer": "Independent Systems Lab",
                    "observed": "2026-08-12",
                    "review_type": "phase2-conformance",
                    "reviewed_commit": "a" * 40,
                    "scope": ["schemas"],
                    "result": "pass-with-findings",
                    "relationship": "independent-third-party",
                    "conflicts": [],
                    "producer_identity": "https://identity.example.org/reviewer",
                    "independence_attestation": "llm-errata-independent-review-v1",
                    "surface_digest": g2_surface_digest(),
                }
            )

        result = self._mutated(mutate)
        self.assert_rejected_without_traceback(result, "G2 external PASS evidence")

    def test_malformed_g2_external_evidence_is_rejected_while_blocked(self) -> None:
        def mutate(payload):
            gate = next(gate for gate in payload["gates"] if gate["id"] == "G2")
            gate["evidence"].append({"kind": "external", "ref": "urn:"})

        result = self._mutated(mutate)
        self.assert_rejected_without_traceback(result, "G2 evidence")


if __name__ == "__main__":
    unittest.main()
