"""Self-tests for the production-readiness ledger checker."""

from __future__ import annotations

import json
import copy
import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from prototype.conformance import _surface_digest_at_commit as conformance_surface_digest_at_commit
from scripts.check_readiness import (
    G2_MATRIX_CURRENT_EVIDENCE,
    G3_SCOPE,
    G3_SURFACE_FILES,
    G5_SURFACE_FILES,
    G6_SCOPE,
    g2_surface_digest,
    g2_surface_digest_at_commit,
    g2_surface_files,
    g6_surface_digest,
    qualifying_g3_security_evidence,
    qualifying_g4_evidence,
    qualifying_g5_interoperability_evidence,
    qualifying_g6_operational_evidence,
    qualifying_g2_review_evidence,
    valid_external_evidence,
    valid_g2_review_evidence,
    valid_g4_implementation_evidence,
    valid_g6_operational_evidence,
    markdown_value,
    surface_digest_from_bytes,
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


@contextmanager
def committed_repo():
    with repo_copy() as root:
        for command in (
            ("git", "init", "-q"),
            ("git", "config", "user.email", "tests@example.invalid"),
            ("git", "config", "user.name", "Readiness tests"),
            ("git", "config", "gc.auto", "0"),
            ("git", "add", "."),
            ("git", "commit", "-q", "-m", "gate evidence baseline"),
        ):
            subprocess.run(command, cwd=root, check=True)
        commit = subprocess.run(
            ("git", "rev-parse", "HEAD"), cwd=root, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        yield root, commit


def gate_surface_digest(root: Path, files: tuple[str, ...]) -> str:
    return surface_digest_from_bytes(
        [(relative, (root / relative).read_bytes()) for relative in sorted(files)]
    )


class Release041ReadinessBoundary(unittest.TestCase):
    def test_release_updates_version_without_upgrading_external_gates(self) -> None:
        root = Path(__file__).resolve().parents[1]
        payload = json.loads(
            (root / "readiness" / "production-readiness.json").read_text()
        )
        self.assertEqual(payload["project_version"], "0.4.1")
        self.assertEqual(payload["verdict"], "NOT_PROD_READY")
        self.assertEqual(
            {gate["id"]: gate["status"] for gate in payload["gates"]},
            {
                "G1": "PASS",
                "G2": "BLOCKED",
                "G3": "BLOCKED",
                "G4": "BLOCKED",
                "G5": "BLOCKED",
                "G6": "BLOCKED",
            },
        )
        g2 = next(gate for gate in payload["gates"] if gate["id"] == "G2")
        refs = {item.get("ref") for item in g2["evidence"]}
        self.assertIn("prototype/conformance.py", refs)
        self.assertIn("spec/adapter-conformance.json", refs)
        self.assertIn("tests/test_conformance.py", refs)


class ReadinessCheckerPasses(unittest.TestCase):
    def test_g2_digest_binds_non_target_corpus_bytes_with_conformance_parity(self) -> None:
        with committed_repo() as (root, baseline_commit):
            baseline = g2_surface_digest_at_commit(baseline_commit, root)
            self.assertEqual(
                baseline,
                conformance_surface_digest_at_commit(root, baseline_commit),
            )
            corpus = root / "spec" / "adapter-conformance.json"
            corpus.write_bytes(
                corpus.read_bytes().replace(
                    b'  "schema_version": 1,',
                    b'    "schema_version": 1,',
                    1,
                )
            )
            subprocess.run(("git", "add", str(corpus)), cwd=root, check=True)
            subprocess.run(
                ("git", "commit", "-q", "-m", "change corpus whitespace"),
                cwd=root, check=True,
            )
            changed_commit = subprocess.run(
                ("git", "rev-parse", "HEAD"), cwd=root, check=True,
                capture_output=True, text=True,
            ).stdout.strip()
            changed = g2_surface_digest_at_commit(changed_commit, root)
            self.assertNotEqual(changed, baseline)
            self.assertEqual(
                changed,
                conformance_surface_digest_at_commit(root, changed_commit),
            )

    @staticmethod
    def _complete_g3_report(root: Path, commit: str) -> dict[str, object]:
        return {
            "kind": "external",
            "ref": "https://reviews.example.org/cryptography/report-1",
            "producer": "Independent Cryptography Laboratory",
            "producer_identity": "https://identity.example.org/crypto-lab",
            "observed": "2026-08-12",
            "review_type": "production-cryptography",
            "reviewed_commit": commit,
            "scope": sorted(G3_SCOPE),
            "result": "pass-with-findings",
            "relationship": "independent-third-party",
            "conflicts": [],
            "independence_attestation": "llm-errata-independent-cryptography-review-v1",
            "surface_digest": gate_surface_digest(root, G3_SURFACE_FILES),
            "implementation": {
                "library": "example-constant-time-library",
                "version": "1.2.3",
                "binding": "example-python-binding",
                "build_digest": "sha256:" + "a" * 64,
                "platforms": ["linux-amd64", "macos-arm64"],
                "constant_time": True,
                "audited_build": True,
            },
        }

    def test_g3_complete_report_qualifies_and_malformed_scope_fails_closed(self) -> None:
        with committed_repo() as (root, commit):
            report = self._complete_g3_report(root, commit)
            self.assertTrue(qualifying_g3_security_evidence(report, root=root))
            for invalid in ([[]], [{}], ["constant-time", []]):
                with self.subTest(scope=invalid):
                    malformed = copy.deepcopy(report)
                    malformed["scope"] = invalid
                    self.assertFalse(
                        qualifying_g3_security_evidence(malformed, root=root)
                    )

    @staticmethod
    def _g4_common(
        root: Path,
        commit: str,
        *,
        producer: str,
        producer_identity: str,
        role: str,
        implementation_id: str,
    ) -> dict[str, object]:
        return {
            "kind": "external",
            "ref": f"https://evidence.example.org/g4/{implementation_id}",
            "producer": producer,
            "producer_identity": producer_identity,
            "observed": "2026-08-12",
            "review_type": "g4-conformance",
            "reviewed_commit": commit,
            "result": "pass",
            "relationship": (
                "independent-implementation"
                if role == "adapter"
                else "independent-third-party-validator"
            ),
            "conflicts": [],
            "independence_attestation": "llm-errata-independent-implementation-v1",
            "surface_digest": g2_surface_digest(root),
            "evidence_role": role,
            "implementation_id": implementation_id,
            "erratum_id": "erratum-synthetic-001",
        }

    @classmethod
    def _complete_g4_records(
        cls, root: Path, commit: str
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        adapter_a = cls._g4_common(
            root, commit, producer="Systems Laboratory Alpha",
            producer_identity="https://identity.example.org/lab-alpha",
            role="adapter", implementation_id="adapter-alpha",
        )
        adapter_a["receipt"] = {
            "receipt_id": "receipt-alpha",
            "receipt_digest": "sha256:" + "a" * 64,
            "evidence_ref": "https://evidence.example.org/receipts/alpha",
        }
        adapter_b = cls._g4_common(
            root, commit, producer="Systems Laboratory Beta",
            producer_identity="https://identity.example.org/lab-beta",
            role="adapter", implementation_id="adapter-beta",
        )
        adapter_b["receipt"] = {
            "receipt_id": "receipt-beta",
            "receipt_digest": "sha256:" + "b" * 64,
            "evidence_ref": "https://evidence.example.org/receipts/beta",
        }
        validator = cls._g4_common(
            root, commit, producer="Independent Validator Laboratory",
            producer_identity="https://identity.example.org/validator-lab",
            role="validator", implementation_id="validator-one",
        )
        validator["validated_receipts"] = [
            {
                "implementation_id": "adapter-alpha",
                "receipt_id": "receipt-alpha",
                "receipt_digest": "sha256:" + "a" * 64,
                "result": "pass",
                "evidence_ref": "https://evidence.example.org/validation/alpha",
            },
            {
                "implementation_id": "adapter-beta",
                "receipt_id": "receipt-beta",
                "receipt_digest": "sha256:" + "b" * 64,
                "result": "pass",
                "evidence_ref": "https://evidence.example.org/validation/beta",
            },
        ]
        return adapter_a, adapter_b, validator

    def test_g4_validator_must_bind_both_adapter_receipts_for_same_erratum(self) -> None:
        with committed_repo() as (root, commit):
            adapter_a, adapter_b, validator = self._complete_g4_records(root, commit)
            self.assertTrue(qualifying_g4_evidence(
                [adapter_a, adapter_b, validator], root=root
            ))

            unrelated = copy.deepcopy(validator)
            unrelated["validated_receipts"][0]["implementation_id"] = "adapter-other-a"
            unrelated["validated_receipts"][1]["implementation_id"] = "adapter-other-b"
            self.assertFalse(qualifying_g4_evidence(
                [adapter_a, adapter_b, unrelated], root=root
            ))

            wrong_erratum = copy.deepcopy(validator)
            wrong_erratum["erratum_id"] = "erratum-unrelated"
            self.assertFalse(qualifying_g4_evidence(
                [adapter_a, adapter_b, wrong_erratum], root=root
            ))

    def test_g4_role_specific_records_reject_malformed_receipt_shapes(self) -> None:
        with committed_repo() as (root, commit):
            adapter_a, _, validator = self._complete_g4_records(root, commit)
            for entry, field, invalid in (
                (adapter_a, "receipt", []),
                (adapter_a, "receipt", {"receipt_id": []}),
                (validator, "validated_receipts", [[]]),
                (validator, "validated_receipts", [{"implementation_id": []}]),
            ):
                with self.subTest(field=field, invalid=invalid):
                    malformed = copy.deepcopy(entry)
                    malformed[field] = invalid
                    self.assertFalse(
                        valid_g4_implementation_evidence(malformed, root=root)
                    )

    @staticmethod
    def _complete_g5_report(root: Path, commit: str) -> dict[str, object]:
        metrics = (
            "observation-to-quarantine-time",
            "known-descendant-coverage",
            "stale-behavior-rate",
            "replacement-activation",
            "collateral-retention",
            "stale-reimport-resistance",
            "opaque-coverage",
            "operator-effort",
            "user-visible-friction",
        )
        systems = []
        for index, name in enumerate(("system-alpha", "system-beta", "system-gamma")):
            systems.append({
                "name": name,
                "version": "1.0.0",
                "operator": f"Operator {index + 1}",
                "operator_identity": f"https://identity.example.org/operator-{index + 1}",
                "evidence_ref": f"https://evidence.example.org/systems/{name}",
                "result": "pass",
                "independently_operated": True,
                "intentionally_nonconforming": index == 0,
                "coverage": "opaque" if index == 1 else "complete",
                "mixed_artifact_lineage": index == 2,
                "operations": [
                    {
                        "operation": operation,
                        "completed": True,
                        "evidence_ref": (
                            f"https://evidence.example.org/systems/{name}/{operation}"
                        ),
                    }
                    for operation in ("correction", "supersession", "erasure")
                ],
                "measurements": [
                    {
                        "metric": metric,
                        "value": index + 1,
                        "unit": "synthetic-unit",
                        "evidence_ref": (
                            f"https://evidence.example.org/systems/{name}/metrics/{metric}"
                        ),
                    }
                    for metric in metrics
                ],
            })
        return {
            "kind": "external",
            "ref": "https://reviews.example.org/interoperability/report-1",
            "producer": "Independent Interoperability Laboratory",
            "producer_identity": "https://identity.example.org/interoperability-lab",
            "observed": "2026-08-12",
            "review_type": "phase3-interoperability",
            "reviewed_commit": commit,
            "surface_digest": gate_surface_digest(root, G5_SURFACE_FILES),
            "result": "pass-with-findings",
            "relationship": "independent-experiment-report",
            "conflicts": [],
            "independence_attestation": "llm-errata-independent-interoperability-review-v1",
            "synthetic_data": True,
            "user_controlled_root": True,
            "root_id": "synthetic-root-001",
            "systems": systems,
        }

    def test_g5_complete_declared_experiment_qualifies(self) -> None:
        with committed_repo() as (root, commit):
            report = self._complete_g5_report(root, commit)
            self.assertTrue(qualifying_g5_interoperability_evidence(report, root=root))

    def test_g5_partial_or_malformed_experiment_cannot_qualify(self) -> None:
        with committed_repo() as (root, commit):
            baseline = self._complete_g5_report(root, commit)
            legacy_shape = copy.deepcopy(baseline)
            legacy_shape.pop("user_controlled_root")
            for system in legacy_shape["systems"]:
                for field in (
                    "intentionally_nonconforming", "coverage",
                    "mixed_artifact_lineage", "operations", "measurements",
                ):
                    system.pop(field)
            self.assertFalse(
                qualifying_g5_interoperability_evidence(legacy_shape, root=root)
            )
            mutations = {
                "missing operation": lambda report: report["systems"][0]["operations"].pop(),
                "missing measurement": lambda report: report["systems"][0]["measurements"].pop(),
                "no nonconforming importer": lambda report: [
                    system.update(intentionally_nonconforming=False)
                    for system in report["systems"]
                ],
                "no incomplete system": lambda report: [
                    system.update(coverage="complete") for system in report["systems"]
                ],
                "no mixed lineage": lambda report: [
                    system.update(mixed_artifact_lineage=False)
                    for system in report["systems"]
                ],
                "malformed system": lambda report: report.update(systems=[[]]),
            }
            for name, mutate in mutations.items():
                with self.subTest(name=name):
                    report = copy.deepcopy(baseline)
                    mutate(report)
                    self.assertFalse(
                        qualifying_g5_interoperability_evidence(report, root=root)
                    )

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
        self.assertIn("spec/adapter-conformance.json", files)
        self.assertIn("docs/READINESS_EVIDENCE_SCHEMAS.md", files)

    def test_g6_complete_measured_report_is_commit_and_deployment_bound(self) -> None:
        with repo_copy() as source, tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repository"
            shutil.copytree(source, root)
            for command in (
                ("git", "init"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Readiness tests"),
                ("git", "config", "gc.auto", "0"),
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
                ("git", "config", "gc.auto", "0"),
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
                ("git", "config", "gc.auto", "0"),
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
                ("git", "config", "gc.auto", "0"),
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
                ("git", "config", "gc.auto", "0"),
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
            version = (root / "VERSION").read_text(encoding="utf-8").strip()
            path = root / "PRODUCTION_READINESS.md"
            lines = path.read_text(encoding="utf-8").splitlines()
            formatted = []
            for line in lines:
                if line.startswith("| Version |"):
                    formatted.append(f"| **Version** | `**{version}**` |")
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
            version = (root / "VERSION").read_text(encoding="utf-8").strip()
            rewrite(
                root / "PRODUCTION_READINESS.md",
                f"| Version | {version} |",
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

    def test_every_gate_matrix_criterion_drift_is_rejected(self) -> None:
        for gate_id in ("G1", "G3", "G4", "G5"):
            with self.subTest(gate_id=gate_id):
                def mutate(root, selected=gate_id):
                    path = root / "PRODUCTION_READINESS.md"
                    lines = path.read_text(encoding="utf-8").splitlines()
                    index = next(
                        i for i, line in enumerate(lines) if line.startswith(f"| {selected} |")
                    )
                    cells = lines[index][1:-1].split("|")
                    cells[1] = " criterion drift "
                    lines[index] = "|" + "|".join(cells) + "|"
                    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

                result = check_after(SCRIPT, mutate)
                self.assert_rejected_without_traceback(
                    result, f"{gate_id} matrix criterion"
                )

    def test_g2_matrix_current_evidence_drift_is_rejected(self) -> None:
        def mutate(root):
            rewrite(
                root / "PRODUCTION_READINESS.md",
                G2_MATRIX_CURRENT_EVIDENCE,
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
            version = (root / "VERSION").read_text(encoding="utf-8").strip()
            rewrite(root / "PRODUCTION_READINESS.md", f"| Version | {version} |\n", "")

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

    def test_g3_g4_g5_reject_generic_or_owner_produced_external_records(self) -> None:
        for gate_id in ("G3", "G4", "G5"):
            with self.subTest(gate_id=gate_id):
                def mutate(payload, selected=gate_id):
                    gate = next(g for g in payload["gates"] if g["id"] == selected)
                    gate["status"] = "PASS"
                    gate["evidence"].append(
                        {
                            "kind": "external",
                            "ref": "https://reviews.example.org/generic/report",
                            "producer": "Thomas Willner",
                            "observed": "2026-08-14",
                        }
                    )

                result = self._mutated(mutate)
                self.assert_rejected_without_traceback(
                    result, f"{gate_id} external PASS evidence"
                )

    def test_pre_corpus_review_target_fails_explicitly(self) -> None:
        with repo_copy() as root:
            corpus = root / "spec" / "adapter-conformance.json"
            corpus_bytes = corpus.read_bytes()
            corpus.unlink()
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Readiness tests"),
                ("git", "add", "."),
                ("git", "commit", "-q", "-m", "pre-corpus"),
            ):
                subprocess.run(command, cwd=root, check=True)
            pre_corpus = subprocess.run(
                ("git", "rev-parse", "HEAD"), cwd=root, check=True,
                capture_output=True, text=True,
            ).stdout.strip()
            corpus.write_bytes(corpus_bytes)
            with self.assertRaisesRegex(OSError, "predates the conformance corpus"):
                g2_surface_digest_at_commit(pre_corpus, root)

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
