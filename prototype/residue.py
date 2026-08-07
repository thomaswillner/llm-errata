"""Substrate evidence.

THREAT_MODEL.md names this the sharpest open problem: an adapter is trusted to
characterise itself, and [Ghost Vectors](https://arxiv.org/abs/2606.18497v1)
shows that is not safe. Soft-deleted embeddings stay reconstructible from HNSW
index files in ChromaDB, FAISS and Weaviate after the API reports the record
gone. An adapter that answers `verified` on the strength of a delete response is
honest and wrong.

A residue scan is the smallest available correction. It reads the store's own
bytes and looks for the retired value. It does not prove absence — nothing here
does — but it converts one specific silent failure into a loud one.

Two rules, and the second is the one that is easy to get wrong:

1. Residue found is `failed`, not `partial`. IDEA.md defines `failed` as
   "relevant state was found and could not be safely repaired or quarantined",
   which is exactly this.
2. A scan that did not run is not a scan that came back clean. `verified`
   requires positive evidence, so an unscanned store cannot reach it.

The residue rule may only ever make a result worse. Applying it to a store
already reporting `unknown` or `failed` would *upgrade* it, which is the
opposite of the point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ResidueReport:
    """What a substrate scan actually established."""

    scanned: bool
    found: bool
    where: str = ""
    detail: str = ""
    #: Every file inspected, so a narrow scan is visible rather than implied.
    files_scanned: tuple[str, ...] = field(default_factory=tuple)

    def blocks_verified(self) -> bool:
        """True when this report is not positive evidence of a clean substrate."""

        return (not self.scanned) or self.found

    def describe(self) -> str:
        if not self.scanned:
            return f"no substrate scan was performed{': ' + self.detail if self.detail else ''}"
        if self.found:
            return f"retired value still present in {self.where}"
        checked = ", ".join(self.files_scanned) or "the store"
        return f"substrate scanned clean ({checked})"


def scan_files(paths: list[Path], needle: str) -> ResidueReport:
    """Search every file in a store's on-disk footprint for a literal value.

    **Every file, not the main one.** Measured on SQLite: in WAL mode a deleted
    row's bytes sit in `<db>-wal` while `<db>` itself is clean. A scan of the
    main database alone reports no residue with the plaintext on the same disk —
    which is precisely the false `verified` this module exists to prevent.

    What this does not cover, and must not be read as covering: the operating
    system page cache, filesystem free space and snapshots, backups, replicas,
    a WAL that has been checkpointed elsewhere, and any index structure that
    encodes the value without storing it verbatim.
    """

    if not needle:
        return ResidueReport(
            scanned=False,
            found=False,
            detail="no value to scan for; the operation retired nothing quotable",
        )

    target = needle.encode("utf-8")
    existing = [p for p in paths if p.exists()]
    if not existing:
        return ResidueReport(
            scanned=False, found=False, detail="no store files exist on disk"
        )

    names = tuple(p.name for p in existing)
    for path in existing:
        try:
            if target in path.read_bytes():
                return ResidueReport(
                    scanned=True,
                    found=True,
                    where=path.name,
                    detail=(
                        "the retired value is readable in the store's own file; "
                        "the API reporting it deleted does not make it gone"
                    ),
                    files_scanned=names,
                )
        except OSError as error:
            return ResidueReport(
                scanned=False,
                found=False,
                detail=f"could not read {path.name}: {error}",
                files_scanned=names,
            )

    return ResidueReport(scanned=True, found=False, files_scanned=names)
