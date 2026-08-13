"""A real, transactional store.

The in-memory adapters prove the model. This one tests whether it survives
contact with a database that has durability semantics, a file on disk, and its
own opinions about what "deleted" means.

Two things it demonstrates that a dictionary cannot:

- **Quarantine commits before the rebuild starts, in its own transaction.** A
  rebuild that fails rolls back; the gate stays shut and survives the process
  dying. That is the storage-layer reason for the ordering the whole proposal
  insists on, rather than an assertion about code.
- **Deleting a row does not remove its bytes.** SQLite moves freed pages to a
  freelist and reuses them later; the text stays readable in the file until
  `VACUUM`, and in WAL mode it is in the `-wal` sidecar rather than the main
  database. This is the same failure Ghost Vectors reports for vector indexes,
  reproducible with nothing but the standard library.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from prototype.adapters import Coverage, Hit
from prototype.lineage import LineageLedger
from prototype.residue import ResidueReport, scan_files


SCHEMA = """
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    root        TEXT,
    content     TEXT,
    inputs      TEXT NOT NULL DEFAULT '[]',
    quarantined INTEGER NOT NULL DEFAULT 0,
    retired     INTEGER NOT NULL DEFAULT 0,
    rebuilt     INTEGER NOT NULL DEFAULT 0
);
"""


class SqliteAdapter:
    name = "sqlite"
    required = True

    def __init__(
        self,
        path: Path,
        ledger: LineageLedger,
        *,
        name: str = "sqlite",
        journal_mode: str = "WAL",
        secure_delete: bool = False,
    ) -> None:
        self.name = name
        self.path = Path(path)
        self._ledger = ledger
        self._db = sqlite3.connect(self.path, isolation_level=None)
        self._db.execute(f"PRAGMA journal_mode={journal_mode}")
        # Left off by default on purpose. Turning it on scrubs freed pages and
        # would hide the very failure this adapter exists to make visible; a
        # deployment that wants it should turn it on and still scan.
        self._db.execute(f"PRAGMA secure_delete={'ON' if secure_delete else 'OFF'}")
        self._db.execute(SCHEMA)
        self._retired_values: list[str] = []
        self._sync_from_ledger()

    # -- setup ---------------------------------------------------------

    def _sync_from_ledger(self) -> None:
        for artifact in self._ledger.artifacts():
            if artifact.store != self.name:
                continue
            self._db.execute(
                "INSERT OR IGNORE INTO artifacts(artifact_id, root, content, inputs) "
                "VALUES(?,?,?,?)",
                (
                    artifact.artifact_id,
                    artifact.root,
                    artifact.content,
                    json.dumps(list(artifact.inputs)),
                ),
            )

    def store_files(self) -> list[Path]:
        """Every file this store occupies, including its journal sidecars."""

        return [
            self.path,
            self.path.with_name(self.path.name + "-wal"),
            self.path.with_name(self.path.name + "-shm"),
            self.path.with_name(self.path.name + "-journal"),
        ]

    def close(self) -> None:
        self._db.close()

    # -- adapter protocol ----------------------------------------------

    def enumerate(self, root: str) -> tuple[str, ...]:
        closure = self._ledger.descendants(root)
        rows = self._db.execute("SELECT artifact_id FROM artifacts").fetchall()
        return tuple(sorted(r[0] for r in rows if r[0] in closure))

    def lineage_complete(self, root: str) -> bool:
        """Database and write-time ledger inventories agree for this store."""

        rows = {
            row[0]
            for row in self._db.execute("SELECT artifact_id FROM artifacts").fetchall()
        }
        expected = {
            artifact.artifact_id
            for artifact in self._ledger.artifacts()
            if artifact.store == self.name
        }
        return root in self._ledger.roots_seen() and rows == expected

    def quarantine(self, artifact_ids: tuple[str, ...]) -> None:
        """Commit the gate immediately, in its own transaction.

        This is deliberately not part of the rebuild transaction. If the two
        shared one, a failed rebuild would roll the gate back and the store
        would resume serving the retired value.
        """

        self._db.execute("BEGIN IMMEDIATE")
        try:
            for artifact_id in artifact_ids:
                self._db.execute(
                    "UPDATE artifacts SET quarantined=1 WHERE artifact_id=?",
                    (artifact_id,),
                )
            self._db.execute("COMMIT")
        except Exception:
            self._db.execute("ROLLBACK")
            raise

    def is_quarantined(self, artifact_id: str) -> bool:
        row = self._db.execute(
            "SELECT quarantined FROM artifacts WHERE artifact_id=?", (artifact_id,)
        ).fetchone()
        return bool(row and row[0])

    def quarantine_coverage(self, root: str) -> Coverage:
        descendants = set(self.enumerate(root))
        if not self.lineage_complete(root):
            return Coverage.UNKNOWN
        quarantined = {
            artifact_id
            for artifact_id in descendants
            if self.is_quarantined(artifact_id)
        }
        if quarantined == descendants:
            return Coverage.VERIFIED
        if quarantined:
            return Coverage.PARTIAL
        return Coverage.FAILED

    def source_artifact(self, artifact_id: str) -> str:
        return artifact_id

    def repair_inputs(self, artifact_id: str) -> tuple[str, ...]:
        row = self._db.execute(
            "SELECT inputs FROM artifacts WHERE artifact_id=?", (artifact_id,)
        ).fetchone()
        return tuple(json.loads(row[0])) if row else ()

    def retire(self, artifact_id: str, *, superseded_at: str | None = None) -> None:
        """Remove the row, and remember what it said.

        The content is deleted rather than flagged, so `VACUUM` has something to
        reclaim. The value is kept in memory for the residue scan: the erratum
        does not carry it and the controller never learns it, so if the adapter
        does not capture it here, nothing can scan for it later.
        """

        row = self._db.execute(
            "SELECT content FROM artifacts WHERE artifact_id=?", (artifact_id,)
        ).fetchone()
        if row and row[0]:
            self._retired_values.append(row[0])
        self._db.execute("BEGIN IMMEDIATE")
        try:
            self._db.execute(
                "UPDATE artifacts SET content=NULL, retired=1, quarantined=1 "
                "WHERE artifact_id=?",
                (artifact_id,),
            )
            self._db.execute("COMMIT")
        except Exception:
            self._db.execute("ROLLBACK")
            raise

    def rebuild(
        self, artifact_id: str, *, inputs: tuple[str, ...], replacement: str | None
    ) -> str:
        parts = [self._ledger.artifact(item).content for item in inputs]
        if replacement:
            parts.insert(0, replacement)
        content = "; ".join(parts)
        self._db.execute("BEGIN IMMEDIATE")
        try:
            self._db.execute(
                "UPDATE artifacts SET content=?, rebuilt=1, quarantined=0 "
                "WHERE artifact_id=?",
                (content, artifact_id),
            )
            self._db.execute("COMMIT")
        except Exception:
            self._db.execute("ROLLBACK")
            raise
        self._ledger.set_content(artifact_id, content)
        return content

    def content(self, artifact_id: str) -> str | None:
        row = self._db.execute(
            "SELECT content FROM artifacts WHERE artifact_id=?", (artifact_id,)
        ).fetchone()
        return row[0] if row else None

    def recall(self, query: str) -> tuple[Hit, ...]:
        rows = self._db.execute(
            "SELECT artifact_id, content FROM artifacts "
            "WHERE quarantined=0 AND retired=0 AND content IS NOT NULL"
        ).fetchall()
        terms = set(query.lower().split())
        return tuple(
            Hit(artifact_id, content)
            for artifact_id, content in rows
            if terms & set(content.lower().replace(";", " ").split())
        )

    def snapshot(self) -> dict[str, str]:
        rows = self._db.execute(
            "SELECT artifact_id, content FROM artifacts WHERE retired=0"
        ).fetchall()
        return {a: c for a, c in rows if c is not None}

    def dispositions(self, root: str) -> dict[str, str]:
        result = {}
        for artifact_id in self.enumerate(root):
            row = self._db.execute(
                "SELECT quarantined, retired, rebuilt FROM artifacts "
                "WHERE artifact_id=?",
                (artifact_id,),
            ).fetchone()
            quarantined, retired, rebuilt = row
            if retired:
                result[artifact_id] = "retired"
            elif rebuilt:
                result[artifact_id] = "rebuilt"
            elif quarantined:
                result[artifact_id] = "quarantined-only"
            else:
                result[artifact_id] = "untouched"
        return result

    # -- substrate evidence --------------------------------------------

    def residue_scan(self, value: str | None = None) -> ResidueReport:
        """Scan every file this store occupies for a retired value."""

        needles = [value] if value else self._retired_values
        if not needles:
            return ResidueReport(
                scanned=False,
                found=False,
                detail="nothing has been retired, so there is no value to scan for",
            )
        last = ResidueReport(scanned=False, found=False)
        for needle in needles:
            last = scan_files(self.store_files(), needle)
            if last.found or not last.scanned:
                return last
        return last

    def vacuum(self) -> None:
        """Reclaim freed pages. Not a security control on its own.

        VACUUM rewrites the database, which removes the freelist copies. It does
        nothing about the WAL, the page cache, backups, or filesystem free space
        holding the old file's contents.
        """

        self._db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        self._db.execute("VACUUM")

    def coverage(self, root: str) -> Coverage:
        descendants = set(self.enumerate(root))
        if not descendants:
            return Coverage.VERIFIED

        disposed = set()
        for artifact_id in descendants:
            row = self._db.execute(
                "SELECT retired, rebuilt FROM artifacts WHERE artifact_id=?",
                (artifact_id,),
            ).fetchone()
            if row and (row[0] or row[1]):
                disposed.add(artifact_id)

        if descendants - disposed:
            bookkeeping = Coverage.PARTIAL if disposed else Coverage.FAILED
        else:
            bookkeeping = Coverage.VERIFIED

        # The residue rule may only ever make the result worse. Applying it to a
        # store already reporting partial or failed would upgrade it.
        if bookkeeping is not Coverage.VERIFIED:
            return bookkeeping

        report = self.residue_scan()
        if report.found:
            return Coverage.FAILED
        if report.blocks_verified() and self._retired_values:
            return Coverage.PARTIAL
        return Coverage.VERIFIED
