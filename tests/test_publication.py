"""Negative tests for the active-publication-surface contract."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

from scripts.check_readiness import g2_surface_digest_at_commit
from tests.support import EXIT_FAIL, EXIT_INCONCLUSIVE, EXIT_OK, check_after, repo_copy, run_checker


SCRIPT = "check_publication.py"


@contextmanager
def bound_publication_repo():
    with repo_copy() as root:
        publication_path = root / "publication" / "active-surfaces.json"
        corpus_path = root / "spec" / "adapter-conformance.json"
        publication = json.loads(publication_path.read_text(encoding="utf-8"))
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        placeholder = {"commit": "0" * 40, "surface_digest": "0" * 64}
        corpus["normative_target"] = placeholder
        publication_path.unlink()
        corpus_path.write_text(json.dumps(corpus, indent=2) + "\n", encoding="utf-8")
        for command in (
            ("git", "init", "-q"),
            ("git", "config", "user.email", "tests@example.invalid"),
            ("git", "config", "user.name", "Publication tests"),
            ("git", "config", "gc.auto", "0"),
            ("git", "add", "."),
            ("git", "commit", "-q", "-m", "publication source"),
        ):
            subprocess.run(command, cwd=root, check=True)
        source_commit = subprocess.run(
            ("git", "rev-parse", "HEAD"), cwd=root, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        target = {
            "commit": source_commit,
            "surface_digest": g2_surface_digest_at_commit(source_commit, root),
        }
        publication["review_target"] = target
        for surface in publication["surfaces"]:
            surface["commit"] = target["commit"]
            surface["surface_digest"] = target["surface_digest"]
        corpus["normative_target"] = target
        publication_path.write_text(json.dumps(publication, indent=2) + "\n", encoding="utf-8")
        corpus_path.write_text(json.dumps(corpus, indent=2) + "\n", encoding="utf-8")
        subprocess.run(
            ("git", "add", "publication/active-surfaces.json", "spec/adapter-conformance.json"),
            cwd=root, check=True,
        )
        subprocess.run(
            ("git", "commit", "-q", "-m", "bind publication target"),
            cwd=root, check=True,
        )
        yield root


class PublicationGuardPasses(unittest.TestCase):
    def test_unmodified_publication_manifest_passes(self) -> None:
        with repo_copy() as root:
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_OK, result.stdout + result.stderr)

    def test_offline_result_does_not_claim_remote_surfaces_were_verified(self) -> None:
        with repo_copy() as root:
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_OK, result.stdout + result.stderr)
        self.assertIn("offline manifest consistency", result.stdout)
        self.assertIn("remote GitHub surfaces were not verified", result.stdout)
        self.assertNotIn("[PASS] active surfaces", result.stdout)

    def test_remote_required_mode_is_inconclusive_without_live_evidence(self) -> None:
        with repo_copy() as root:
            result = subprocess.run(
                [sys.executable, str(root / "scripts" / SCRIPT), "--require-remote"],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, EXIT_INCONCLUSIVE, result.stdout)
        self.assertIn("INCONCLUSIVE", result.stdout)

    def test_review_and_conformance_targets_are_identical(self) -> None:
        root = Path(__file__).resolve().parents[1]
        publication = json.loads(
            (root / "publication" / "active-surfaces.json").read_text(encoding="utf-8")
        )
        corpus = json.loads(
            (root / "spec" / "adapter-conformance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(publication["review_target"], corpus["normative_target"])


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

    def _assert_history_mutation_is_rejected(
        self, mutate_payload: Callable[[dict[str, object]], None], diagnostic: str
    ) -> None:
        with bound_publication_repo() as root:
            path = root / "publication" / "active-surfaces.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            mutate_payload(payload)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stdout)

    def test_stale_commit_is_rejected(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["review_target"].__setitem__(
                "commit", "ac4468faf73c2cc7949dd29b2a2a151f5bd23116"
            ),
            "review target",
        )

    def test_stale_digest_is_rejected(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["review_target"].__setitem__(
                "surface_digest",
                "7e0d6c88c1ca3a87743ac70ba2a3dfea0b350d112d2d3c59a3c6cbb537568f12",
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

    def test_historical_surface_cannot_be_deleted(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["historical_surfaces"].clear(),
            "historical surfaces",
        )

    def test_historical_surface_cannot_be_rewritten(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["historical_surfaces"][0].__setitem__(
                "commit", "not-a-commit"
            ),
            "historical surfaces",
        )

    def test_one_of_multiple_historical_surfaces_cannot_be_deleted(self) -> None:
        self._assert_history_mutation_is_rejected(
            lambda payload: payload["historical_surfaces"].pop(1),
            "historical surfaces",
        )

    def test_well_formed_historical_surface_rewrite_is_rejected(self) -> None:
        def mutate(payload: dict[str, object]) -> None:
            payload["historical_surfaces"][0]["commit"] = "a" * 40
            payload["historical_surfaces"][0]["url"] = (
                "https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-9999999999"
            )

        self._assert_history_mutation_is_rejected(mutate, "historical surfaces")

    def test_well_formed_active_surface_replacement_is_rejected(self) -> None:
        def mutate(payload: dict[str, object]) -> None:
            surface = payload["surfaces"][0]
            surface["id"] = "arbitrary-current-surface"
            surface["url"] = (
                "https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-9999999998"
            )

        self._assert_history_mutation_is_rejected(mutate, "active surfaces")

    def test_uncommitted_nonpackaging_delta_is_rejected(self) -> None:
        with bound_publication_repo() as root:
            readme = root / "README.md"
            readme.write_bytes(readme.read_bytes() + b"\nnon-packaging mutation\n")
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout + result.stderr)
        self.assertIn("release binding", result.stdout)

    def test_duplicate_surface_url_is_rejected(self) -> None:
        def mutate(payload: dict[str, object]) -> None:
            payload["surfaces"].append(dict(payload["surfaces"][0]))

        self._assert_manifest_mutation_is_rejected(mutate, "unique surface URLs")

    def test_duplicate_evidence_role_is_rejected(self) -> None:
        def mutate(payload: dict[str, object]) -> None:
            payload["surfaces"][0]["roles"].append(
                payload["surfaces"][0]["roles"][0]
            )

        self._assert_manifest_mutation_is_rejected(mutate, "unique evidence roles")

    def test_duplicate_mention_is_rejected(self) -> None:
        def mutate(payload: dict[str, object]) -> None:
            payload["surfaces"][0]["mentions"] = ["Reviewer", "Reviewer"]

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

    def test_future_utc_publication_date_is_rejected(self) -> None:
        self._assert_manifest_mutation_is_rejected(
            lambda payload: payload["surfaces"][0].__setitem__(
                "published", "2999-01-01"
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
