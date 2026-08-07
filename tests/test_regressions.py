"""Regressions found by adversarial review of the Phase 1 build.

Every test here failed when it was written. Each one corresponds to a defect
that the original test suite passed straight over, which is the point: the
suite proved the happy path and the two cheap tricks, and missed three ways to
defeat the contract entirely.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from prototype.errata import Erratum, FeedError, Operation
from prototype.scenario import DIET, build_importer
from prototype.signing import DemoSigner


REPO_ROOT = Path(__file__).resolve().parents[1]

OWNER = DemoSigner(b"owner-secret")
IMPOSTOR = DemoSigner(b"not-the-owner")


def supersede(sequence: int = 1) -> Erratum:
    return OWNER.sign_erratum(
        Erratum(
            erratum_id="err_supersede",
            sequence=sequence,
            target_root=DIET,
            operation=Operation.SUPERSEDE,
            valid_from="2026-08-01T00:00:00Z",
            replacement="eats meat again",
            postconditions={
                "negative": "vegetarian",
                "positive": "eats meat again",
                "preserve": "quiet restaurants|moderate budget",
            },
        )
    )


class ResumeIsNotABypass(unittest.TestCase):
    """`resume=True` skipped `observe()` entirely, so an unsigned erratum from
    anyone was applied and produced a signed receipt. Resuming an interrupted
    repair must re-authenticate; the interruption is not a reason to trust the
    input less carefully."""

    def test_an_unsigned_erratum_cannot_be_applied_by_resuming(self) -> None:
        importer = build_importer(OWNER)
        forged = Erratum(
            erratum_id="err_evil",
            sequence=99,
            target_root=DIET,
            operation=Operation.ERASE,
            valid_from="2026-08-01T00:00:00Z",
            postconditions={"negative": "x", "preserve": "y"},
        )
        with self.assertRaises(FeedError):
            importer.repair(forged, resume=True)

    def test_an_erratum_signed_by_the_wrong_key_cannot_be_resumed(self) -> None:
        importer = build_importer(OWNER)
        forged = IMPOSTOR.sign_erratum(supersede().replace(signature=None))
        with self.assertRaises(FeedError):
            importer.repair(forged, resume=True)

    def test_resuming_the_genuine_erratum_still_works(self) -> None:
        # Re-authenticating must not break resumption: the sequence has not
        # advanced, because the interrupted attempt never reached attest.
        from prototype.strategies import InterruptedRepair, InterruptingStrategy, RebuildStrategy

        importer = build_importer(OWNER, strategy=InterruptingStrategy())
        with self.assertRaises(InterruptedRepair):
            importer.repair(supersede())
        importer.use_strategy(RebuildStrategy())
        receipt = importer.repair(supersede(), resume=True)
        self.assertEqual(receipt.triad["negative"], "pass")


class StaleReimportIsRefusedAtEquality(unittest.TestCase):
    """The guard read `sequence < applied`, so a re-export carrying exactly the
    sequence of the erratum that retired the proposition was accepted — and it
    carried the retired proposition back in."""

    def test_a_reimport_at_the_applied_sequence_cannot_carry_the_old_value(self) -> None:
        importer = build_importer(OWNER)
        importer.repair(supersede(sequence=1))
        importer.reimport(DIET, content="is vegetarian", sequence=1)
        self.assertEqual(
            importer.markdown.recall("vegetarian"),
            (),
            "a stale export restored the retired proposition",
        )

    def test_a_genuinely_newer_export_is_still_accepted(self) -> None:
        importer = build_importer(OWNER)
        importer.repair(supersede(sequence=1))
        self.assertTrue(
            importer.reimport(DIET, content="eats meat again", sequence=2)
        )


class MakeDemoFailsOnAnyUnexpectedExit(unittest.TestCase):
    """`make demo` only failed on exit 0, so a crash — an ImportError, exit 1 —
    was reported as success by `make check`."""

    def test_the_target_requires_exactly_the_expected_exit_code(self) -> None:
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn(
            "-ne 2",
            makefile,
            "make demo must require exit 2 exactly, not merely non-zero",
        )

    def test_a_crashing_demo_is_reported_as_a_failure(self) -> None:
        result = subprocess.run(
            ["make", "demo", "PYTHON=" + sys.executable + " -c 'import sys;sys.exit(1)' #"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(
            result.returncode, 0, "a demo exiting 1 was reported as success"
        )


class SupersessionPreservesHistoryAndCorrectionDoesNot(unittest.TestCase):
    """`valid_from` was signed and never read, and both operations retired the
    artifact identically. The correct/supersede distinction was a boolean on
    the receipt rather than a difference in what the importer retains.

    IDEA.md: "Present-day recommendations use the new state; correctly scoped
    historical questions may retain the old one." And for correction: "The
    false history should not be preserved merely because it appeared first."
    """

    def test_supersession_keeps_the_old_value_out_of_present_tense_recall(self) -> None:
        importer = build_importer(OWNER)
        importer.repair(supersede())
        self.assertEqual(importer.markdown.recall("vegetarian"), ())

    def test_supersession_retains_the_old_value_as_scoped_history(self) -> None:
        importer = build_importer(OWNER)
        importer.repair(supersede())
        history = importer.markdown.recall_history("vegetarian")
        self.assertTrue(history, "supersession discarded valid history")
        self.assertEqual(history[0].valid_until, "2026-08-01T00:00:00Z")

    def test_correction_destroys_the_false_history(self) -> None:
        importer = build_importer(OWNER)
        correction = OWNER.sign_erratum(
            Erratum(
                erratum_id="err_correct",
                sequence=1,
                target_root=DIET,
                operation=Operation.CORRECT,
                valid_from="2026-01-01T00:00:00Z",
                replacement="never was vegetarian",
                postconditions={
                    "negative": "vegetarian",
                    "positive": "never was vegetarian",
                    "preserve": "quiet restaurants|moderate budget",
                },
            )
        )
        importer.repair(correction)
        self.assertEqual(
            importer.markdown.recall_history("vegetarian"),
            (),
            "a correction preserved a proposition that was never true",
        )

    def test_erasure_leaves_no_history_either(self) -> None:
        importer = build_importer(OWNER)
        erasure = OWNER.sign_erratum(
            Erratum(
                erratum_id="err_erase",
                sequence=1,
                target_root=DIET,
                operation=Operation.ERASE,
                valid_from="2026-08-01T00:00:00Z",
                postconditions={
                    "negative": "vegetarian",
                    "preserve": "quiet restaurants|moderate budget",
                },
            )
        )
        importer.repair(erasure)
        self.assertEqual(importer.markdown.recall_history("vegetarian"), ())


if __name__ == "__main__":
    unittest.main()
