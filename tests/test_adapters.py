"""Adapters are where the proposal meets a real store.

The interesting one is `OpaqueAdapter`. It exists to prove a negative: that an
importer which cannot enumerate a store says so, and that no amount of success
elsewhere can turn that into an aggregate pass. ROADMAP.md calls it "the
control", and these tests are what make it one.
"""

from __future__ import annotations

import unittest

from prototype.adapters import (
    Coverage,
    CannotEnumerate,
    MarkdownAdapter,
    OpaqueAdapter,
    VectorAdapter,
)
from prototype.lineage import Artifact, LineageLedger


ROOT = "mem_01HX"
QUIET = "mem_02KP"
BUDGET = "mem_03RS"


def ledger_with_a_mixed_summary() -> LineageLedger:
    """One root copied into a store, plus a summary mixing three roots."""

    ledger = LineageLedger()
    ledger.register_import(ROOT, "fact:diet", store="markdown", content="is vegetarian")
    ledger.register_import(QUIET, "fact:venue", store="markdown", content="prefers quiet restaurants")
    ledger.register_import(BUDGET, "fact:budget", store="markdown", content="moderate budget")
    ledger.register_import(
        "mem_09ZZ", "fact:pet", store="markdown", content="has a cat"
    )
    ledger.register_derivation(
        "summary:dining",
        store="markdown",
        inputs=("fact:diet", "fact:venue", "fact:budget"),
        content="is vegetarian; prefers quiet restaurants; moderate budget",
    )
    return ledger


class LineageTracksTheDerivationClosure(unittest.TestCase):
    def test_a_summary_is_a_descendant_of_every_root_it_mixed(self) -> None:
        ledger = ledger_with_a_mixed_summary()
        self.assertEqual(
            ledger.descendants(ROOT), {"fact:diet", "summary:dining"}
        )
        self.assertEqual(
            ledger.descendants(QUIET), {"fact:venue", "summary:dining"}
        )

    def test_the_closure_is_transitive(self) -> None:
        ledger = ledger_with_a_mixed_summary()
        ledger.register_derivation(
            "export:profile",
            store="markdown",
            inputs=("summary:dining",),
            content="dining profile",
        )
        self.assertIn("export:profile", ledger.descendants(ROOT))

    def test_an_unrelated_artifact_is_not_a_descendant(self) -> None:
        ledger = ledger_with_a_mixed_summary()
        self.assertNotIn("fact:pet", ledger.descendants(ROOT))

    def test_still_valid_inputs_exclude_the_retired_root(self) -> None:
        ledger = ledger_with_a_mixed_summary()
        retained = ledger.valid_inputs("summary:dining", retired={"fact:diet"})
        self.assertEqual(retained, ("fact:venue", "fact:budget"))


class MarkdownAdapterExposesExactLineage(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = ledger_with_a_mixed_summary()
        self.adapter = MarkdownAdapter(self.ledger)

    def test_it_enumerates_the_descendants_of_a_root(self) -> None:
        self.assertEqual(
            self.adapter.enumerate(ROOT), ("fact:diet", "summary:dining")
        )

    def test_quarantine_removes_an_artifact_from_recall(self) -> None:
        self.assertIn("fact:diet", [item.artifact_id for item in self.adapter.recall("vegetarian")])
        self.adapter.quarantine(("fact:diet", "summary:dining"))
        self.assertEqual(self.adapter.recall("vegetarian"), ())

    def test_quarantine_does_not_touch_unrelated_artifacts(self) -> None:
        self.adapter.quarantine(("fact:diet", "summary:dining"))
        self.assertIn(
            "fact:pet",
            [item.artifact_id for item in self.adapter.recall("cat")],
        )
        self.assertIn(
            "fact:budget",
            [item.artifact_id for item in self.adapter.recall("budget")],
        )

    def test_rebuild_keeps_the_retained_inputs_and_drops_the_retired_one(self) -> None:
        self.adapter.quarantine(("fact:diet", "summary:dining"))
        self.adapter.retire("fact:diet")
        self.adapter.rebuild(
            "summary:dining",
            inputs=("fact:venue", "fact:budget"),
            replacement="eats meat again",
        )
        rebuilt = self.adapter.content("summary:dining")
        self.assertNotIn("vegetarian", rebuilt)
        self.assertIn("quiet restaurants", rebuilt)
        self.assertIn("moderate budget", rebuilt)
        self.assertIn("eats meat again", rebuilt)

    def test_a_fully_enumerated_repair_reports_verified(self) -> None:
        self.adapter.quarantine(("fact:diet", "summary:dining"))
        self.adapter.retire("fact:diet")
        self.adapter.rebuild(
            "summary:dining", inputs=("fact:venue", "fact:budget"), replacement="x"
        )
        self.assertEqual(self.adapter.coverage(ROOT), Coverage.VERIFIED)

    def test_an_undisposed_descendant_reports_partial(self) -> None:
        self.adapter.quarantine(("fact:diet",))
        self.adapter.retire("fact:diet")
        # summary:dining was never rebuilt or retired.
        self.assertEqual(self.adapter.coverage(ROOT), Coverage.PARTIAL)


class VectorAdapterRebuildsAffectedEntries(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = ledger_with_a_mixed_summary()
        self.adapter = VectorAdapter(self.ledger)
        self.adapter.index("vec:diet", source="fact:diet", text="is vegetarian")
        self.adapter.index(
            "vec:dining",
            source="summary:dining",
            text="is vegetarian; prefers quiet restaurants; moderate budget",
        )
        self.adapter.index("vec:pet", source="fact:pet", text="has a cat")

    def test_it_enumerates_entries_by_derivation_metadata(self) -> None:
        self.assertEqual(self.adapter.enumerate(ROOT), ("vec:diet", "vec:dining"))

    def test_lineage_completeness_survives_intentional_retirement(self) -> None:
        self.assertTrue(self.adapter.lineage_complete(ROOT))
        self.adapter.retire("vec:diet")
        self.assertTrue(self.adapter.lineage_complete(ROOT))

    def test_live_entry_without_source_metadata_breaks_completeness(self) -> None:
        self.adapter._text["vec:orphan"] = "untracked live entry"
        self.assertFalse(self.adapter.lineage_complete(ROOT))

    def test_quarantined_entries_stop_being_retrieved(self) -> None:
        self.assertTrue(self.adapter.recall("vegetarian"))
        self.adapter.quarantine(("vec:diet", "vec:dining"))
        self.assertEqual(self.adapter.recall("vegetarian"), ())

    def test_unrelated_entries_survive_the_repair(self) -> None:
        self.adapter.quarantine(("vec:diet", "vec:dining"))
        self.adapter.retire("vec:diet")
        self.adapter.rebuild(
            "vec:dining",
            inputs=(),
            replacement="eats meat again; prefers quiet restaurants; moderate budget",
        )
        self.assertTrue(self.adapter.recall("cat"))


class OpaqueAdapterCannotClaimSuccess(unittest.TestCase):
    """The control. A store that acknowledges an erratum but cannot show its
    work must never be counted as repaired."""

    def setUp(self) -> None:
        self.adapter = OpaqueAdapter(name="prompt_cache")

    def test_it_refuses_to_enumerate(self) -> None:
        with self.assertRaises(CannotEnumerate):
            self.adapter.enumerate(ROOT)

    def test_it_acknowledges_the_erratum(self) -> None:
        self.assertTrue(self.adapter.acknowledge(ROOT))

    def test_acknowledgement_does_not_become_coverage(self) -> None:
        self.adapter.acknowledge(ROOT)
        self.assertEqual(self.adapter.coverage(ROOT), Coverage.UNKNOWN)

    def test_it_reports_unknown_even_after_quarantine_is_requested(self) -> None:
        self.adapter.acknowledge(ROOT)
        self.adapter.quarantine(())
        self.assertEqual(self.adapter.coverage(ROOT), Coverage.UNKNOWN)

    def test_unknown_is_not_silently_omitted(self) -> None:
        # A store outside the required scope is omitted from a receipt. This
        # one is in scope, so it must appear and it must appear as unknown.
        self.assertNotEqual(self.adapter.coverage(ROOT), Coverage.VERIFIED)
        self.assertIsNotNone(self.adapter.coverage(ROOT))


if __name__ == "__main__":
    unittest.main()
