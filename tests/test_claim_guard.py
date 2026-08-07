"""Negative tests for `scripts/claim_guard.py`.

A guard that has only ever passed has not been shown to work. Every test here
constructs a corpus that misstates the proposal and requires the guard to
reject it. The first two cases are the mutations that a keyword-presence check
cannot catch, and are the reason this guard exists.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.support import (
    EXIT_FAIL,
    EXIT_INCONCLUSIVE,
    EXIT_OK,
    check_after,
    repo_copy,
    rewrite,
    run_checker,
)


SCRIPT = "claim_guard.py"

BOUNDED_NOVELTY = (
    "This is a **novel synthesis with a narrow, apparently unimplemented "
    "conformance gap**. The public evidence does not support claims of a world "
    "first, patentability, non-infringement, legal priority, or freedom to "
    "operate."
)


class ClaimGuardPasses(unittest.TestCase):
    def test_unmodified_repository_passes(self) -> None:
        with repo_copy() as root:
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_OK, result.stdout)


class ClaimGuardRejectsOverclaims(unittest.TestCase):
    def test_world_first_assertion_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(
                root / "PRIOR_ART.md",
                BOUNDED_NOVELTY,
                "This is the **world first** implementation of verified "
                "descendant repair.",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("world first", result.stdout)

    def test_patentability_assertion_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(
                root / "PRIOR_ART.md",
                BOUNDED_NOVELTY,
                "The conformance conjunction is clearly patentable.",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("patentability", result.stdout)

    def test_freedom_to_operate_assertion_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(
                root / "PRIOR_ART.md",
                BOUNDED_NOVELTY,
                "Freedom to operate is established for this conjunction.",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)


class ClaimGuardRejectsInvariantLoss(unittest.TestCase):
    def test_inverted_loop_order_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "IDEA.md"
            text = path.read_text(encoding="utf-8")
            quarantine = "2. **Quarantine.** Deny the root"
            rebuild = "3. **Rebuild.** Traverse exact lineage"
            if quarantine not in text or rebuild not in text:
                raise AssertionError("loop steps not found in IDEA.md")
            text = text.replace(quarantine, "\x00PLACEHOLDER\x00", 1)
            text = text.replace(rebuild, quarantine.replace("2.", "3."), 1)
            text = text.replace("\x00PLACEHOLDER\x00", rebuild.replace("3.", "2."), 1)
            path.write_text(text, encoding="utf-8")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("ordering", result.stdout)

    def test_dropped_quarantine_invariant_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(root / "AGENTS.md", "Quarantine always precedes repair.", "")

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)

    def test_dropped_core_thesis_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(
                root / "README.md",
                "**An imported memory is a dependency, not a copy.**",
                "**An imported memory is a copy.**",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)

    def test_dropped_falsifier_section_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(
                root / "PRIOR_ART.md",
                "## What would invalidate the claim",
                "## Notes",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)

    def test_green_aggregate_over_unknown_coverage_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(
                root / "IDEA.md",
                "Aggregate success requires every required store to be `verified`.",
                "Aggregate success is reported when the observable stores pass.",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)


class ClaimGuardHandlesUnevaluableInput(unittest.TestCase):
    def test_missing_guarded_file_is_inconclusive_not_a_pass(self) -> None:
        def mutate(root: Path) -> None:
            (root / "PRIOR_ART.md").unlink()

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_INCONCLUSIVE, result.stdout)
        self.assertIn("This is not a pass.", result.stdout)

    def test_stale_reviewed_exception_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            rewrite(
                root / "RESEARCH.md",
                "- A claim that behavioral probes can mathematically prove "
                "semantic absence.",
                "- A claim about what probes can show.",
            )

        result = check_after(SCRIPT, mutate)
        self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
        self.assertIn("reviewed exceptions", result.stdout)


if __name__ == "__main__":
    unittest.main()
