"""The eight Phase 1 scenarios and the acceptance criteria in ROADMAP.md.

Each test names the criterion it enforces. The criterion that matters most is
the last one: an unknown required store prevents aggregate success even when
every executable probe passed.
"""

from __future__ import annotations

import json
import unittest
from prototype.adapters import Coverage
from prototype.checkpoints import CheckpointError, QuarantineCheckpoint
from prototype.controller import Phase
from prototype.errata import Erratum, Operation
from prototype.scenario import DIET, build_importer
from prototype.signing import DemoSigner
from prototype.strategies import (
    AppendOnlyStrategy,
    InterruptedRepair,
    InterruptingStrategy,
    RebuildStrategy,
    WipeStrategy,
)


OWNER = DemoSigner(b"owner-secret")


class SilentLineageAdapter:
    """Enumerable but supplies no evidence that its empty walk is complete."""

    name = "silent_store"
    required = True

    def enumerate(self, root: str) -> tuple[str, ...]:
        return ()

    def quarantine(self, artifact_ids: tuple[str, ...]) -> None:
        return None

    def is_quarantined(self, artifact_id: str) -> bool:
        return False

    def coverage(self, root: str) -> Coverage:
        return Coverage.VERIFIED

    def dispositions(self, root: str) -> dict[str, str]:
        return {}


class AuditedEmptyAdapter(SilentLineageAdapter):
    name = "audited_empty_store"

    def lineage_complete(self, root: str) -> bool:
        return True


class SilentFailingAdapter(SilentLineageAdapter):
    name = "silent_failing_store"

    def coverage(self, root: str) -> Coverage:
        return Coverage.FAILED


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


def erase(sequence: int = 1) -> Erratum:
    return OWNER.sign_erratum(
        Erratum(
            erratum_id="err_erase",
            sequence=sequence,
            target_root=DIET,
            operation=Operation.ERASE,
            valid_from="2026-08-01T00:00:00Z",
            postconditions={
                "negative": "vegetarian",
                "preserve": "quiet restaurants|moderate budget",
            },
        )
    )


def correct(sequence: int = 1) -> Erratum:
    return OWNER.sign_erratum(
        Erratum(
            erratum_id="err_correct",
            sequence=sequence,
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


class QuarantinePrecedesRepair(unittest.TestCase):
    """Acceptance: quarantine is observable before any rebuild begins."""

    def test_the_journal_orders_quarantine_before_rebuild(self) -> None:
        importer = build_importer(OWNER)
        importer.repair(supersede())
        phases = [event.phase for event in importer.journal]
        self.assertLess(
            phases.index(Phase.QUARANTINE_COMPLETE),
            phases.index(Phase.REBUILD_BEGIN),
        )

    def test_every_known_descendant_is_gated_before_the_first_rebuild(self) -> None:
        importer = build_importer(OWNER)
        importer.repair(supersede())
        gated = next(
            event
            for event in importer.journal
            if event.phase is Phase.QUARANTINE_COMPLETE
        )
        self.assertIn("fact:diet", gated.detail["markdown"])
        self.assertIn("summary:dining", gated.detail["markdown"])
        self.assertIn("vec:diet", gated.detail["vector"])

    def test_explicit_quarantine_returns_bound_evidence_without_rebuild(self) -> None:
        importer = build_importer(OWNER)
        checkpoint = importer.quarantine(supersede())
        self.assertEqual(checkpoint.erratum_id, "err_supersede")
        self.assertEqual(checkpoint.pre_state_root, importer.state_root())
        self.assertEqual(
            {item.name: item.coverage for item in checkpoint.adapters},
            {"markdown": "verified", "prompt_cache": "unknown", "vector": "verified"},
        )
        self.assertNotIn(Phase.REBUILD_BEGIN, [event.phase for event in importer.journal])

    def test_checkpointed_repair_does_not_quarantine_twice(self) -> None:
        importer = build_importer(OWNER)
        checkpoint = importer.quarantine(supersede())
        receipt = importer.repair_quarantined(supersede(), checkpoint)
        self.assertEqual(receipt.erratum_id, checkpoint.erratum_id)
        self.assertEqual(
            [event.phase for event in importer.journal].count(Phase.QUARANTINE_BEGIN), 1
        )

    def test_drifted_checkpoint_is_refused_before_rebuild(self) -> None:
        importer = build_importer(OWNER)
        checkpoint = importer.quarantine(supersede())
        drifted = QuarantineCheckpoint.create(
            erratum_id=checkpoint.erratum_id,
            sequence=checkpoint.sequence,
            target_root=checkpoint.target_root,
            pre_state_root="b" * 32,
            adapters=checkpoint.adapters,
            created_at=checkpoint.created_at,
        )
        with self.assertRaisesRegex(CheckpointError, "state"):
            importer.repair_quarantined(supersede(), drifted)
        self.assertNotIn(Phase.REBUILD_BEGIN, [event.phase for event in importer.journal])


class EveryDescendantGetsADisposition(unittest.TestCase):
    """Acceptance: every known descendant receives an explicit disposition."""

    def test_no_descendant_is_left_untouched(self) -> None:
        importer = build_importer(OWNER)
        receipt = importer.repair(supersede())
        for store, dispositions in receipt.dispositions.items():
            for artifact_id, disposition in dispositions.items():
                self.assertNotEqual(
                    disposition, "untouched", f"{store}:{artifact_id} was skipped"
                )


class TheRepairTriadIsRecordedIndependently(unittest.TestCase):
    """Acceptance: negative, positive, and preservation are separate results."""

    def test_all_three_are_present_and_pass_for_a_supersession(self) -> None:
        importer = build_importer(OWNER)
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.triad["negative"], "pass")
        self.assertEqual(receipt.triad["positive"], "pass")
        self.assertEqual(receipt.triad["preserve"], "pass")

    def test_erasure_has_no_positive_leg(self) -> None:
        importer = build_importer(OWNER)
        receipt = importer.repair(erase())
        self.assertNotIn("positive", receipt.triad)
        self.assertEqual(receipt.triad["negative"], "pass")
        self.assertEqual(receipt.triad["preserve"], "pass")

    def test_a_wipe_that_destroys_retained_memory_fails_preservation(self) -> None:
        # The cheap trick the triad exists to defeat: "fix" the problem by
        # deleting the whole profile. The negative probe passes; preservation
        # must not.
        importer = build_importer(OWNER, strategy=WipeStrategy())
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.triad["negative"], "pass")
        self.assertEqual(receipt.triad["preserve"], "fail")
        self.assertNotEqual(receipt.aggregate, Coverage.VERIFIED)

    def test_adding_the_new_fact_while_still_serving_the_old_fails_negative(self) -> None:
        # The other cheap trick: append the replacement and leave the retired
        # proposition retrievable.
        importer = build_importer(OWNER, strategy=AppendOnlyStrategy())
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.triad["negative"], "fail")
        self.assertNotEqual(receipt.aggregate, Coverage.VERIFIED)


class MixedArtifactsAreRebuiltNotDeleted(unittest.TestCase):
    """Acceptance: a mixed artifact retains its unrelated inputs."""

    def test_the_summary_keeps_the_two_retained_facts(self) -> None:
        importer = build_importer(OWNER)
        importer.repair(supersede())
        summary = importer.markdown.content("summary:dining")
        self.assertNotIn("vegetarian", summary)
        self.assertIn("quiet restaurants", summary)
        self.assertIn("moderate budget", summary)
        self.assertIn("eats meat again", summary)


class OperationsStayDistinct(unittest.TestCase):
    def test_correction_does_not_preserve_the_false_history(self) -> None:
        importer = build_importer(OWNER)
        receipt = importer.repair(correct())
        self.assertEqual(receipt.operation, "correct")
        self.assertFalse(receipt.history_retained)

    def test_supersession_retains_the_old_value_for_its_valid_interval(self) -> None:
        importer = build_importer(OWNER)
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.operation, "supersede")
        self.assertTrue(receipt.history_retained)

    def test_erasure_evidence_does_not_repeat_the_erased_value(self) -> None:
        importer = build_importer(OWNER)
        receipt = importer.repair(erase())
        serialised = json.dumps(receipt.to_dict())
        self.assertNotIn("vegetarian", serialised.lower())


class StaleExportsCannotRecontaminate(unittest.TestCase):
    """Acceptance: a stale export cannot silently restore the retired state."""

    def test_reimporting_the_original_export_is_refused(self) -> None:
        importer = build_importer(OWNER)
        importer.repair(supersede())
        accepted = importer.reimport(DIET, content="is vegetarian", sequence=0)
        self.assertFalse(accepted)
        self.assertEqual(importer.markdown.recall("vegetarian"), ())

    def test_only_an_export_newer_than_the_erratum_is_accepted(self) -> None:
        # This test previously asserted that a reimport at the *same* sequence
        # as the applied erratum was accepted, which is exactly the off-by-one
        # that let a stale export restore the retired proposition. The erratum
        # at sequence N is the one that retired it, so an export stamped N
        # predates the repair. See tests/test_regressions.py.
        importer = build_importer(OWNER)
        importer.repair(supersede())
        self.assertFalse(importer.reimport(DIET, content="is vegetarian", sequence=1))
        self.assertTrue(importer.reimport(DIET, content="eats meat again", sequence=2))


class InterruptedRepairFailsClosed(unittest.TestCase):
    """Acceptance: an interrupted repair keeps affected recall quarantined and
    does not expose partially repaired state."""

    def test_state_stays_quarantined_when_a_rebuild_raises(self) -> None:
        importer = build_importer(OWNER, strategy=InterruptingStrategy())
        with self.assertRaises(InterruptedRepair):
            importer.repair(supersede())
        self.assertTrue(importer.markdown.is_quarantined("summary:dining"))
        self.assertEqual(importer.markdown.recall("vegetarian"), ())

    def test_the_repair_resumes_from_the_quarantined_state(self) -> None:
        importer = build_importer(OWNER, strategy=InterruptingStrategy())
        with self.assertRaises(InterruptedRepair):
            importer.repair(supersede())
        importer.use_strategy(RebuildStrategy())
        receipt = importer.repair(supersede(), resume=True)
        self.assertEqual(receipt.triad["negative"], "pass")
        self.assertIn("quiet restaurants", importer.markdown.content("summary:dining"))


class ReceiptsBindStateAndReportCoverageHonestly(unittest.TestCase):
    def test_the_receipt_binds_the_erratum_and_both_state_roots(self) -> None:
        importer = build_importer(OWNER)
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.erratum_id, "err_supersede")
        self.assertEqual(receipt.sequence, 1)
        self.assertNotEqual(receipt.pre_state_root, receipt.post_state_root)
        self.assertTrue(receipt.verify(importer.signer.public))

    def test_state_roots_are_deterministic(self) -> None:
        first = build_importer(OWNER).repair(supersede())
        second = build_importer(OWNER).repair(supersede())
        self.assertEqual(first.pre_state_root, second.pre_state_root)
        self.assertEqual(first.post_state_root, second.post_state_root)

    def test_a_tampered_receipt_fails_verification(self) -> None:
        importer = build_importer(OWNER)
        receipt = importer.repair(supersede())
        forged = receipt.with_aggregate(Coverage.VERIFIED)
        self.assertFalse(forged.verify(importer.signer.public))

    def test_the_opaque_store_appears_as_unknown(self) -> None:
        importer = build_importer(OWNER)
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.stores["prompt_cache"], Coverage.UNKNOWN)

    def test_an_unknown_required_store_prevents_aggregate_success(self) -> None:
        # The point of the whole demo. Both inspectable stores are verified and
        # all three probes passed, and the aggregate is still not verified.
        importer = build_importer(OWNER)
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.stores["markdown"], Coverage.VERIFIED)
        self.assertEqual(receipt.stores["vector"], Coverage.VERIFIED)
        self.assertEqual(set(receipt.triad.values()), {"pass"})
        self.assertEqual(receipt.aggregate, Coverage.PARTIAL)

    def test_removing_the_opaque_store_is_what_would_turn_it_green(self) -> None:
        # Stated as a test so the previous result cannot be mistaken for a bug
        # in the aggregation: with every required store inspectable, the same
        # repair does report verified.
        importer = build_importer(OWNER, include_opaque=False)
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.aggregate, Coverage.VERIFIED)

    def test_the_receipt_lists_what_it_could_not_verify(self) -> None:
        importer = build_importer(OWNER)
        receipt = importer.repair(supersede())
        self.assertTrue(
            any("prompt_cache" in item for item in receipt.limitations),
            receipt.limitations,
        )

    def test_empty_enumeration_without_lineage_audit_cannot_verify(self) -> None:
        importer = build_importer(OWNER, include_opaque=False)
        importer.adapters.append(SilentLineageAdapter())
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.stores["silent_store"], Coverage.UNKNOWN)
        self.assertNotEqual(receipt.aggregate, Coverage.VERIFIED)
        self.assertTrue(
            any("silent_store" in item and "lineage" in item for item in receipt.limitations),
            receipt.limitations,
        )

    def test_audited_empty_scope_can_verify(self) -> None:
        importer = build_importer(OWNER, include_opaque=False)
        importer.adapters.append(AuditedEmptyAdapter())
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.stores["audited_empty_store"], Coverage.VERIFIED)
        self.assertEqual(receipt.aggregate, Coverage.VERIFIED)

    def test_missing_lineage_evidence_never_upgrades_a_failure(self) -> None:
        importer = build_importer(OWNER, include_opaque=False)
        importer.adapters.append(SilentFailingAdapter())
        receipt = importer.repair(supersede())
        self.assertEqual(receipt.stores["silent_failing_store"], Coverage.FAILED)
        self.assertEqual(receipt.aggregate, Coverage.FAILED)


class SplitViewEquivocationIsOutsideOneImporter(unittest.TestCase):
    def test_one_importer_remembers_a_conflict_across_observe_calls(self) -> None:
        importer = build_importer(OWNER, include_opaque=False)
        first_event = supersede().replace(erratum_id="err_A", signature=None)
        second_event = supersede().replace(
            erratum_id="err_B", replacement="is vegan now", signature=None
        )
        importer.quarantine(OWNER.sign_erratum(first_event))
        with self.assertRaisesRegex(Exception, "conflict in this importer view"):
            importer.quarantine(OWNER.sign_erratum(second_event))

    def test_each_receipt_discloses_that_its_feed_view_is_local(self) -> None:
        first_event = supersede().replace(erratum_id="err_A", signature=None)
        second_event = supersede().replace(
            erratum_id="err_B",
            replacement="is vegan now",
            postconditions={
                "negative": "vegetarian",
                "positive": "is vegan now",
                "preserve": "quiet restaurants|moderate budget",
            },
            signature=None,
        )
        first = build_importer(OWNER).repair(OWNER.sign_erratum(first_event))
        second = build_importer(OWNER).repair(OWNER.sign_erratum(second_event))

        self.assertTrue(first.verify(build_importer(OWNER).signer.public))
        self.assertTrue(second.verify(build_importer(OWNER).signer.public))
        self.assertNotEqual(first.erratum_id, second.erratum_id)
        for receipt in (first, second):
            self.assertTrue(
                any("global" in item and "equivocation" in item for item in receipt.limitations),
                receipt.limitations,
            )


class FeedRollbackIsRefusedByTheController(unittest.TestCase):
    def test_an_older_erratum_after_a_newer_one_is_refused(self) -> None:
        importer = build_importer(OWNER)
        importer.repair(supersede(sequence=1))
        with self.assertRaises(Exception) as raised:
            importer.repair(supersede(sequence=1))
        self.assertIn("rollback", str(raised.exception).lower())


if __name__ == "__main__":
    unittest.main()
