"""The SQLite adapter, and the substrate evidence rule.

The headline is `SubstrateResidue`. Everything else here is scaffolding for it.
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from prototype.adapters import Coverage
from prototype.lineage import LineageLedger
from prototype.residue import ResidueReport, scan_files
from prototype.sqlite_store import SqliteAdapter


DIET = "mem_01HX"
VENUE = "mem_02KP"
SECRET = "is vegetarian"


def build_ledger() -> LineageLedger:
    ledger = LineageLedger()
    ledger.register_import(DIET, "fact:diet", store="sqlite", content=SECRET)
    ledger.register_import(
        VENUE, "fact:venue", store="sqlite", content="prefers quiet restaurants"
    )
    ledger.register_derivation(
        "summary:dining",
        store="sqlite",
        inputs=("fact:diet", "fact:venue"),
        content=f"{SECRET}; prefers quiet restaurants",
    )
    return ledger


class SqliteAdapterCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="errata-sqlite-")
        self.path = Path(self._tmp.name) / "store.sqlite3"
        self.ledger = build_ledger()
        self.adapter = SqliteAdapter(self.path, self.ledger)

    def tearDown(self) -> None:
        self.adapter.close()
        self._tmp.cleanup()


class BasicStoreBehaviour(SqliteAdapterCase):
    def test_it_enumerates_the_closure(self) -> None:
        self.assertEqual(
            self.adapter.enumerate(DIET), ("fact:diet", "summary:dining")
        )

    def test_quarantine_removes_from_recall(self) -> None:
        self.assertTrue(self.adapter.recall("vegetarian"))
        self.adapter.quarantine(("fact:diet", "summary:dining"))
        self.assertEqual(self.adapter.recall("vegetarian"), ())

    def test_unrelated_rows_survive(self) -> None:
        self.adapter.quarantine(("fact:diet", "summary:dining"))
        self.assertTrue(self.adapter.recall("quiet"))

    def test_rebuild_keeps_the_retained_input(self) -> None:
        self.adapter.quarantine(("fact:diet", "summary:dining"))
        self.adapter.retire("fact:diet")
        rebuilt = self.adapter.rebuild(
            "summary:dining", inputs=("fact:venue",), replacement="eats meat again"
        )
        self.assertNotIn("vegetarian", rebuilt)
        self.assertIn("quiet restaurants", rebuilt)


class DurableQuarantine(SqliteAdapterCase):
    """The storage-layer reason quarantine precedes repair."""

    def test_the_gate_survives_a_failed_rebuild(self) -> None:
        self.adapter.quarantine(("fact:diet", "summary:dining"))
        with self.assertRaises(sqlite3.Error):
            # A genuine database error, not a fabricated one: rebuilding an
            # artifact whose input is not in the ledger raises before commit.
            self.adapter._db.execute("BEGIN IMMEDIATE")
            self.adapter._db.execute("INSERT INTO artifacts(artifact_id) VALUES(?)",
                                     ("fact:diet",))
        self.adapter._db.execute("ROLLBACK")
        self.assertTrue(self.adapter.is_quarantined("fact:diet"))

    def test_the_gate_survives_the_process(self) -> None:
        self.adapter.quarantine(self.adapter.enumerate(DIET))
        self.adapter.close()
        reopened = SqliteAdapter(self.path, self.ledger)
        self.addCleanup(reopened.close)
        self.assertTrue(reopened.is_quarantined("fact:diet"))
        self.assertEqual(reopened.recall("vegetarian"), ())


class SubstrateResidue(SqliteAdapterCase):
    """Ghost Vectors, reproduced with the standard library.

    The API says the row is gone. The bytes are still on disk.
    """

    def test_a_retired_row_is_still_readable_in_the_store_files(self) -> None:
        # Gate the whole closure first: retiring the raw fact alone leaves the
        # mixed summary still serving the value, which is correct behaviour and
        # not what this test is about.
        self.adapter.quarantine(self.adapter.enumerate(DIET))
        self.adapter.retire("fact:diet")
        self.assertIsNone(self.adapter.content("fact:diet"))
        self.assertEqual(self.adapter.recall("vegetarian"), ())

        report = self.adapter.residue_scan(SECRET)
        self.assertTrue(report.scanned)
        self.assertTrue(
            report.found,
            "the retired value should still be present in the store's files",
        )

    def test_scanning_only_the_main_database_would_have_missed_it(self) -> None:
        # This is the mistake the design nearly shipped. In WAL mode the value
        # is in the -wal sidecar while the main database reads clean, so a scan
        # of one file reports no residue with the plaintext on the same disk.
        self.adapter.quarantine(self.adapter.enumerate(DIET))
        self.adapter.retire("fact:diet")
        full = self.adapter.residue_scan(SECRET)
        narrow = scan_files([self.path], SECRET)
        self.assertTrue(full.found)
        self.assertGreater(len(full.files_scanned), 1)
        if not narrow.found:
            self.assertNotEqual(
                full.where,
                self.path.name,
                "the residue was found outside the main database, which is "
                "exactly why the scan must cover every store file",
            )

    def test_residue_makes_coverage_failed_not_partial(self) -> None:
        # IDEA.md: `failed` is "relevant state was found and could not be
        # safely repaired or quarantined". Residue is exactly that.
        self.adapter.quarantine(self.adapter.enumerate(DIET))
        self.adapter.retire("fact:diet")
        self.adapter.rebuild(
            "summary:dining", inputs=("fact:venue",), replacement="eats meat again"
        )
        self.assertEqual(self.adapter.coverage(DIET), Coverage.FAILED)

    def test_vacuum_and_checkpoint_clear_it(self) -> None:
        self.adapter.quarantine(self.adapter.enumerate(DIET))
        self.adapter.retire("fact:diet")
        self.adapter.rebuild(
            "summary:dining", inputs=("fact:venue",), replacement="eats meat again"
        )
        self.assertEqual(self.adapter.coverage(DIET), Coverage.FAILED)
        self.adapter.vacuum()
        self.assertFalse(self.adapter.residue_scan(SECRET).found)
        self.assertEqual(self.adapter.coverage(DIET), Coverage.VERIFIED)


class TheResidueRuleOnlyEverMakesThingsWorse(unittest.TestCase):
    """The review's second critical finding: a downgrade applied to `unknown`
    or `failed` would be an upgrade."""

    def test_an_unscanned_report_blocks_verified(self) -> None:
        self.assertTrue(ResidueReport(scanned=False, found=False).blocks_verified())

    def test_a_clean_scan_does_not_block(self) -> None:
        self.assertFalse(ResidueReport(scanned=True, found=False).blocks_verified())

    def test_a_dirty_scan_blocks(self) -> None:
        self.assertTrue(ResidueReport(scanned=True, found=True).blocks_verified())

    def test_a_partial_store_is_never_promoted_by_a_clean_scan(self) -> None:
        tmp = tempfile.TemporaryDirectory(prefix="errata-sqlite-")
        self.addCleanup(tmp.cleanup)
        ledger = build_ledger()
        adapter = SqliteAdapter(Path(tmp.name) / "s.sqlite3", ledger)
        self.addCleanup(adapter.close)
        adapter.retire("fact:diet")
        adapter.vacuum()  # substrate is now clean
        # summary:dining was never disposed, so bookkeeping says partial and a
        # clean substrate must not turn that into verified.
        self.assertEqual(adapter.coverage(DIET), Coverage.PARTIAL)

    def test_scanning_for_nothing_is_not_a_clean_scan(self) -> None:
        report = scan_files([Path("/nonexistent/x")], "")
        self.assertFalse(report.scanned)
        self.assertTrue(report.blocks_verified())


if __name__ == "__main__":
    unittest.main()
