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


if __name__ == "__main__":
    unittest.main()
