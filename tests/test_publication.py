"""Negative tests for the active-publication-surface contract."""

from __future__ import annotations

import json
import unittest
from collections.abc import Callable
from pathlib import Path

from tests.support import EXIT_FAIL, EXIT_INCONCLUSIVE, EXIT_OK, check_after, repo_copy, run_checker


SCRIPT = "check_publication.py"


class PublicationGuardPasses(unittest.TestCase):
    def test_unmodified_publication_manifest_passes(self) -> None:
        with repo_copy() as root:
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_OK, result.stdout + result.stderr)


class PublicationGuardRejectsDrift(unittest.TestCase):
    def _assert_manifest_mutation_is_rejected(
        self, mutate_payload: Callable[[dict[str, object]], None], diagnostic: str
    ) -> None:
        def mutate(root: Path) -> None:
            path = root / "publication" / "active-surfaces.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            mutate_payload(payload)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stdout)

    def test_stale_commit_is_rejected(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["review_target"].__setitem__(
                "commit", "08b95263c9ed700c43aea0b285696956cc23e878"
            ),
            "review target",
        )

    def test_stale_digest_is_rejected(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["review_target"].__setitem__(
                "surface_digest",
                "03abc492319b875a7d528e0e8de05714bc5a7219b42031fc7c3f42cff1f0bf14",
            ),
            "review target",
        )

    def test_surface_must_bind_canonical_commit_and_digest(self) -> None:
        def mutate(payload: dict[str, object]) -> None:
            payload["surfaces"][0]["commit"] = "a" * 40
            payload["surfaces"][0]["surface_digest"] = "b" * 64

        self._assert_manifest_mutation_is_rejected(mutate, "surface target binding")

    def test_obsolete_permission_language_is_rejected(self) -> None:
        def mutate(payload: dict[str, object]) -> None:
            payload["license"]["case_by_case_permission_required"] = True
            payload["license"]["specification_implementation"] = (
                "written scoped permission grant required"
            )

        self._assert_manifest_mutation_is_rejected(mutate, "licence posture")

    def test_required_attribution_is_rejected_when_incomplete(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["license"]["required_attribution"].remove(
                "Thomas Willner"
            ),
            "licence attribution",
        )

    def test_reference_code_boundary_is_rejected_when_missing(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["license"].__setitem__(
                "reference_code", "commercial reuse permitted"
            ),
            "reference code boundary",
        )

    def test_missing_required_surface_is_rejected(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["surfaces"].pop(), "required active surfaces"
        )

    def test_duplicate_surface_url_is_rejected(self) -> None:
        def mutate(payload: dict[str, object]) -> None:
            payload["surfaces"][1]["url"] = payload["surfaces"][0]["url"]

        self._assert_manifest_mutation_is_rejected(mutate, "unique surface URLs")

    def test_duplicate_evidence_role_is_rejected(self) -> None:
        def mutate(payload: dict[str, object]) -> None:
            payload["surfaces"][1]["roles"] = [
                payload["surfaces"][0]["roles"][0]
            ]

        self._assert_manifest_mutation_is_rejected(mutate, "unique evidence roles")

    def test_duplicate_mention_is_rejected(self) -> None:
        def mutate(payload: dict[str, object]) -> None:
            payload["surfaces"][1]["mentions"] = [
                payload["surfaces"][0]["mentions"][0]
            ]

        self._assert_manifest_mutation_is_rejected(mutate, "unique GitHub mentions")

    def test_invitation_cannot_be_called_independent_evidence(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["surfaces"][0].__setitem__(
                "evidence_boundary", "independent-evidence"
            ),
            "evidence boundary",
        )

    def test_invalid_gate_is_rejected(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["surfaces"][0]["gates"].append("G7"),
            "surface fields",
        )

    def test_invalid_publication_date_is_rejected(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["surfaces"][0].__setitem__(
                "published", "13 August 2026"
            ),
            "surface fields",
        )

    def test_invalid_url_is_rejected(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["surfaces"][0].__setitem__(
                "url", "https://example.invalid/review"
            ),
            "surface fields",
        )

    def test_missing_manifest_is_inconclusive(self) -> None:
        def mutate(root: Path) -> None:
            (root / "publication" / "active-surfaces.json").unlink()

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_INCONCLUSIVE, result.stdout)
        self.assertIn("INCONCLUSIVE", result.stdout)

    def test_malformed_manifest_is_inconclusive(self) -> None:
        def mutate(root: Path) -> None:
            (root / "publication" / "active-surfaces.json").write_text(
                "{not-json}\n", encoding="utf-8"
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_INCONCLUSIVE, result.stdout)
        self.assertIn("INCONCLUSIVE", result.stdout)


if __name__ == "__main__":
    unittest.main()
