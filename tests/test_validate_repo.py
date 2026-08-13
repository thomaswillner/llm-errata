"""Negative tests for `scripts/validate_repo.py`.

These prove the linter rejects the structural faults it claims to catch. They
say nothing about whether the proposal still states its bounded claim — that is
`claim_guard.py`'s job, and `test_claim_guard.py` proves it.
"""

from __future__ import annotations

import unittest
import json
from pathlib import Path

from tests.support import EXIT_FAIL, EXIT_OK, check_after, repo_copy, rewrite, run_checker


SCRIPT = "validate_repo.py"


class ValidatorPasses(unittest.TestCase):
    def test_unmodified_repository_passes(self) -> None:
        with repo_copy() as root:
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_OK, result.stdout)


class ValidatorRejectsStructuralFaults(unittest.TestCase):
    def _assert_public_license_mutation_is_rejected(
        self, relative_path: str, old: str, new: str
    ) -> None:
        def mutate(root: Path) -> None:
            path = root / relative_path
            text = path.read_text(encoding="utf-8")
            self.assertIn(old, text, f"missing public licence contract: {old}")
            path.write_text(text.replace(old, new, 1), encoding="utf-8")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("public licence alignment", result.stdout)

    def _assert_license_mutation_is_rejected(self, old: str, new: str) -> None:
        def mutate(root: Path) -> None:
            path = root / "LICENSE"
            text = path.read_text(encoding="utf-8")
            self.assertIn(old, text, f"missing licence contract: {old}")
            path.write_text(text.replace(old, new, 1), encoding="utf-8")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("license and notice", result.stdout)

    def test_specification_implementation_grant_cannot_be_removed(self) -> None:
        self._assert_license_mutation_is_rejected(
            "commercial and non-commercial products and services",
            "personal non-commercial experiments",
        )

    def test_required_product_attribution_cannot_be_removed(self) -> None:
        self._assert_license_mutation_is_rejected(
            "Implements the LLM Errata specification by Thomas Willner",
            "Implements an unnamed memory specification",
        )

    def test_reference_code_cannot_be_relicensed_by_specification_grant(self) -> None:
        self._assert_license_mutation_is_rejected(
            "does not cover `prototype/`, `scripts/`, or `tests/`",
            "also covers `prototype/`, `scripts/`, and `tests/`",
        )

    def test_false_endorsement_protection_cannot_be_removed(self) -> None:
        self._assert_license_mutation_is_rejected(
            "does not imply endorsement, sponsorship, certification, or audit",
            "implies certification by the author",
        )

    def test_readme_dual_license_boundary_cannot_be_removed(self) -> None:
        self._assert_public_license_mutation_is_rejected(
            "README.md",
            "Commercial and non-commercial independent implementations are permitted",
            "Only personal experiments are permitted",
        )

    def test_notice_product_attribution_cannot_be_removed(self) -> None:
        self._assert_public_license_mutation_is_rejected(
            "NOTICE",
            "Implements the LLM Errata specification by Thomas Willner",
            "Implements a memory specification",
        )

    def test_independent_implementation_permission_rule_cannot_regress(self) -> None:
        self._assert_public_license_mutation_is_rejected(
            "INDEPENDENT_IMPLEMENTATION.md",
            "No per-implementer permission is required",
            "Written permission is required",
        )

    def test_contributing_clean_room_boundary_cannot_be_removed(self) -> None:
        self._assert_public_license_mutation_is_rejected(
            "CONTRIBUTING.md",
            "independently authored implementation",
            "copy of the reference implementation",
        )

    def test_security_no_endorsement_boundary_cannot_be_removed(self) -> None:
        self._assert_public_license_mutation_is_rejected(
            "SECURITY.md",
            "Licence attribution does not imply security review, endorsement, or certification",
            "Licence attribution provides security certification",
        )

    def test_publication_discipline_cannot_be_removed(self) -> None:
        required = {
            "AGENTS.md": (
                "publication/active-surfaces.json",
                "git cat-file -e <commit>:<path>",
                "Recruitment evidence is not independent readiness evidence",
            ),
            "CONTRIBUTING.md": (
                "append-only supersession",
                "make publication",
                "read-after-write",
            ),
            "docs/PUBLICATION_STRATEGY.md": (
                "Active surface",
                "Historical surface",
                "publication/active-surfaces.json",
            ),
        }
        for relative_path, phrases in required.items():
            with self.subTest(relative_path=relative_path):
                def mutate(root: Path, path: str = relative_path) -> None:
                    target = root / path
                    text = target.read_text(encoding="utf-8")
                    for phrase in required[path]:
                        self.assertIn(phrase, text, f"missing publication contract: {phrase}")
                    target.write_text(
                        text.replace(required[path][0], "removed publication rule", 1),
                        encoding="utf-8",
                    )

                result = check_after(SCRIPT, mutate)
                self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
                self.assertIn("publication discipline", result.stdout)

    def test_missing_required_file_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            (root / "SECURITY.md").unlink()

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("required files", result.stdout)

    def test_missing_production_readiness_matrix_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            (root / "PRODUCTION_READINESS.md").unlink()

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("required files", result.stdout)

    def test_missing_independent_validation_program_artifacts_are_rejected(self) -> None:
        for relative_path in (
            "REVIEW_REQUEST.md",
            "INDEPENDENT_IMPLEMENTATION.md",
            "PHASE3_SYSTEMS.md",
            "docs/PUBLICATION_STRATEGY.md",
        ):
            with self.subTest(relative_path=relative_path):
                def mutate(root: Path, path: str = relative_path) -> None:
                    (root / path).unlink()

                result = check_after(SCRIPT, mutate)
                self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
                self.assertIn("required files", result.stdout)

    def test_missing_publication_guard_artifacts_are_rejected(self) -> None:
        for relative_path in (
            "publication/active-surfaces.json",
            "scripts/check_publication.py",
            "tests/test_publication.py",
        ):
            with self.subTest(relative_path=relative_path):
                def mutate(root: Path, path: str = relative_path) -> None:
                    (root / path).unlink()

                result = check_after(SCRIPT, mutate)
                self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
                self.assertIn("required files", result.stdout)
    def test_internal_phase_two_completion_cannot_upgrade_g2(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "readiness" / "production-readiness.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            gate = next(gate for gate in payload["gates"] if gate["id"] == "G2")
            gate["status"] = "PASS"
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("G2 independent review gate", result.stdout)

    def test_g2_pass_rejects_malformed_external_review_evidence(self) -> None:
        invalid_reviews = (
            {"ref": "", "producer": "Independent reviewer", "observed": "2026-08-09"},
            {"ref": "ftp://example.invalid/review", "producer": "Independent reviewer", "observed": "2026-08-09"},
            {"ref": "urn:example:review", "producer": "local implementer", "observed": "2026-08-09"},
            {"ref": "urn:example:review", "producer": "Independent reviewer", "observed": "invalid"},
            {"ref": "urn:example:review", "producer": "Independent reviewer", "observed": "2999-01-01"},
        )
        for review in invalid_reviews:
            with self.subTest(review=review):
                def mutate(root: Path, evidence: dict[str, str] = review) -> None:
                    path = root / "readiness" / "production-readiness.json"
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    gate = next(gate for gate in payload["gates"] if gate["id"] == "G2")
                    gate["status"] = "PASS"
                    gate["evidence"].append({"kind": "external", **evidence})
                    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

                result = check_after(SCRIPT, mutate)
                self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
                self.assertIn("G2 independent review gate", result.stdout)

    def test_g2_pass_requires_complete_independent_review_schema(self) -> None:
        from scripts.check_readiness import g2_surface_digest

        review = {
            "kind": "external",
            "ref": "https://reviews.example.org/phase2/report",
            "producer": "Independent Systems Lab",
            "observed": "2026-08-12",
            "review_type": "phase2-conformance",
            "reviewed_commit": "a" * 40,
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
            "surface_digest": g2_surface_digest(),
        }
        invalid_reviews = []
        for field in (
            "kind", "review_type", "reviewed_commit", "scope", "result", "relationship",
            "conflicts", "producer_identity", "independence_attestation", "surface_digest",
        ):
            invalid = dict(review)
            invalid.pop(field)
            invalid_reviews.append(invalid)
        for field, value in (
            ("kind", "repository"),
            ("ref", "urn:"),
            ("producer", "project owner"),
            ("producer", "reference implementer"),
            ("reviewed_commit", "a" * 39),
            ("scope", ["schemas"]),
            ("scope", review["scope"] + ["schemas"]),
            ("scope", review["scope"] + ["extra"]),
            ("result", "fail"),
            ("relationship", "maintainer"),
            ("conflicts", "none"),
            ("producer_identity", "https://identity.example.org"),
            ("producer_identity", "https://identity.example.org/"),
            ("independence_attestation", "independent"),
            ("surface_digest", "a" * 64),
        ):
            invalid = dict(review)
            invalid[field] = value
            invalid_reviews.append(invalid)

        for evidence in invalid_reviews:
            with self.subTest(evidence=evidence):
                def mutate(root: Path, review_entry: dict[str, object] = evidence) -> None:
                    path = root / "readiness" / "production-readiness.json"
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    gate = next(gate for gate in payload["gates"] if gate["id"] == "G2")
                    gate["status"] = "PASS"
                    gate["evidence"].append(review_entry)
                    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

                result = check_after(SCRIPT, mutate)
                self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
                self.assertIn("G2 independent review gate", result.stdout)

    def test_broken_repository_relative_link_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(root / "README.md", "(PRIOR_ART.md)", "(PRIOR_ARTS.md)")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("repository-relative links", result.stdout)

    def test_trailing_whitespace_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "README.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "trailing   \n", encoding="utf-8"
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("trailing whitespace", result.stdout)

    def test_absolute_local_path_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "ROADMAP.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nSee /Users/example/notes.md\n",
                encoding="utf-8",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("portable documentation paths", result.stdout)

    def test_unclosed_markdown_fence_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "ROADMAP.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\n```text\nunterminated\n",
                encoding="utf-8",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("Markdown fences", result.stdout)

    def test_version_disagreement_is_rejected(self) -> None:
        # Derived from the current version rather than hardcoded. An earlier
        # version of this test wrote a literal "0.2.0", which silently stopped
        # testing anything the moment 0.2.0 was released: it set VERSION to the
        # value it already had, so nothing disagreed and the check passed.
        def mutate(root: Path) -> None:
            current = (root / "VERSION").read_text(encoding="utf-8").strip()
            major = int(current.split(".")[0])
            (root / "VERSION").write_text(f"{major + 1}.0.0\n", encoding="utf-8")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("CITATION.cff release version", result.stdout)

    def test_readme_maturity_version_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            current = (root / "VERSION").read_text(encoding="utf-8").strip()
            rewrite(root / "README.md", f"Version {current}", "Version 0.0.0")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("README maturity version", result.stdout)

    def test_readme_maturity_version_prefix_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            current = (root / "VERSION").read_text(encoding="utf-8").strip()
            rewrite(root / "README.md", f"Version {current}", f"Version {current}.1")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("README maturity version", result.stdout)

    def test_security_supported_version_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            current = (root / "VERSION").read_text(encoding="utf-8").strip()
            major, minor, _ = current.split(".")
            rewrite(root / "SECURITY.md", f"| {major}.{minor}.x | Yes |", "| 0.0.x | Yes |")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("SECURITY supported version", result.stdout)

    def test_extra_security_supported_version_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            current = (root / "VERSION").read_text(encoding="utf-8").strip()
            major, minor, _ = current.split(".")
            supported = f"| {major}.{minor}.x | Yes |"
            rewrite(root / "SECURITY.md", supported, supported + "\n| 0.2.x | Yes |")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("SECURITY supported version", result.stdout)

    def test_earlier_security_versions_cannot_be_supported(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(
                root / "SECURITY.md",
                "| 0.2.x and earlier | No |",
                "| 0.2.x and earlier | Yes |",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("SECURITY supported version", result.stdout)

    def test_unreleased_security_revisions_cannot_be_supported(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(
                root / "SECURITY.md",
                "| Unreleased development revisions | No |",
                "| Unreleased development revisions | Yes |",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("SECURITY supported version", result.stdout)

    def test_missing_canonical_source_link_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            for name in ("IDEA.md", "PRIOR_ART.md", "RESEARCH.md", "ROADMAP.md"):
                path = root / name
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "https://www.w3.org/TR/prov-dm/", "https://example.invalid/"
                    ),
                    encoding="utf-8",
                )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("canonical link", result.stdout)


class PublicationGuardIntegration(unittest.TestCase):
    def test_make_check_runs_publication_guard(self) -> None:
        makefile = (Path(__file__).resolve().parents[1] / "Makefile").read_text(
            encoding="utf-8"
        )
        self.assertIn("check: lint claim readiness publication test demo", makefile)
        self.assertIn(
            "publication: ## Validate active public calls without upgrading readiness",
            makefile,
        )
        self.assertIn("$(PYTHON) scripts/check_publication.py", makefile)

    def test_ci_runs_publication_guard_explicitly(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[1] / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("- name: Validate active publication surfaces", workflow)
        self.assertIn("run: make publication", workflow)


class GitHubActionsRuntimeGuard(unittest.TestCase):
    def test_workflows_pin_node24_action_releases(self) -> None:
        workflow_dir = (
            Path(__file__).resolve().parents[1] / ".github" / "workflows"
        )
        workflows = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(workflow_dir.glob("*.yml"))
        )
        self.assertNotIn("actions/checkout@v4", workflows)
        self.assertNotIn("actions/setup-python@v5", workflows)
        self.assertIn("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", workflows)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", workflows)

    def test_validator_rejects_deprecated_action_major(self) -> None:
        def mutate(root: Path) -> None:
            path = root / ".github" / "workflows" / "links.yml"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
                    "actions/checkout@v4",
                    1,
                ),
                encoding="utf-8",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("GitHub Actions Node 24 pins", result.stdout)


if __name__ == "__main__":
    unittest.main()
