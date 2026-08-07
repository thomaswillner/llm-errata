"""The on-disk layout the CLI operates over.

ROADMAP.md sketches this shape, and it is deliberately ordinary files: a feed
that is append-only because it is a log, a registry that is append-only because
lineage is written at derivation time, and receipts that are one file each
because they are evidence and evidence does not get edited in place.

The owner's signing key lives here too, which is fine for a demonstration and
wrong for anything else: in a real deployment the owner and the importer are
different parties on different machines, and the whole point is that the
importer holds only the public key.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prototype.errata import Erratum
from prototype.lineage import LineageLedger
from prototype.receipts import Receipt
from prototype.signing import Ed25519Signer, VerificationKey


class Workspace:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    # -- paths ---------------------------------------------------------

    @property
    def feed_path(self) -> Path:
        return self.root / "feeds" / "errata.jsonl"

    @property
    def lineage_path(self) -> Path:
        return self.root / "registry" / "lineage.jsonl"

    @property
    def receipts_dir(self) -> Path:
        return self.root / "receipts"

    @property
    def store_path(self) -> Path:
        return self.root / "store.sqlite3"

    @property
    def config_path(self) -> Path:
        return self.root / "config.json"

    @property
    def applied_path(self) -> Path:
        return self.root / "registry" / "applied.json"

    def exists(self) -> bool:
        return self.config_path.is_file()

    # -- setup ---------------------------------------------------------

    def initialise(self) -> None:
        for directory in ("feeds", "registry", "receipts", "identity"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        self.feed_path.touch()
        self.lineage_path.touch()
        if not self.applied_path.exists():
            self.applied_path.write_text("{}\n", encoding="utf-8")

        owner_seed = self.root / "identity" / "owner.seed"
        importer_seed = self.root / "identity" / "importer.seed"
        # Deterministic seeds keep the demonstration reproducible. A deployment
        # generates them, keeps the owner's on the owner's machine, and never
        # writes either one next to the data it protects.
        if not owner_seed.exists():
            owner_seed.write_text("demo-owner-seed\n", encoding="utf-8")
        if not importer_seed.exists():
            importer_seed.write_text("demo-importer-seed\n", encoding="utf-8")

        (self.root / "identity" / "owner.pub").write_text(
            self.owner_signer().public.to_hex() + "\n", encoding="utf-8"
        )
        (self.root / "identity" / "importer.pub").write_text(
            self.importer_signer().public.to_hex() + "\n", encoding="utf-8"
        )
        if not self.config_path.exists():
            self.config_path.write_text(
                json.dumps({"importer": "importer-1", "opaque_store": True}, indent=2)
                + "\n",
                encoding="utf-8",
            )

    def config(self) -> dict[str, Any]:
        if not self.config_path.is_file():
            return {}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    # -- identity ------------------------------------------------------

    def owner_signer(self) -> Ed25519Signer:
        seed = (self.root / "identity" / "owner.seed").read_bytes().strip()
        return Ed25519Signer(seed, key_id="owner")

    def importer_signer(self) -> Ed25519Signer:
        seed = (self.root / "identity" / "importer.seed").read_bytes().strip()
        return Ed25519Signer(seed, key_id="importer")

    def owner_verification_key(self) -> VerificationKey:
        return self.owner_signer().public

    def importer_verification_key(self) -> VerificationKey:
        return self.importer_signer().public

    # -- lineage -------------------------------------------------------

    def add_import(self, root: str, artifact_id: str, content: str) -> None:
        self._append_lineage(
            {"kind": "import", "root": root, "artifact_id": artifact_id,
             "content": content, "store": "sqlite"}
        )

    def add_derivation(
        self, artifact_id: str, inputs: tuple[str, ...], content: str
    ) -> None:
        self._append_lineage(
            {"kind": "derivation", "artifact_id": artifact_id,
             "inputs": list(inputs), "content": content, "store": "sqlite"}
        )

    def _append_lineage(self, record: dict[str, Any]) -> None:
        with self.lineage_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def load_lineage(self) -> LineageLedger:
        ledger = LineageLedger()
        if not self.lineage_path.is_file():
            return ledger
        for line in self.lineage_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record["kind"] == "import":
                ledger.register_import(
                    record["root"], record["artifact_id"],
                    store=record["store"], content=record["content"],
                )
            else:
                ledger.register_derivation(
                    record["artifact_id"], store=record["store"],
                    inputs=tuple(record["inputs"]), content=record["content"],
                )
        return ledger

    # -- feed ----------------------------------------------------------

    def append_erratum(self, erratum: Erratum) -> None:
        with self.feed_path.open("a", encoding="utf-8") as handle:
            handle.write(erratum.to_json() + "\n")

    def next_sequence(self) -> int:
        if not self.feed_path.is_file():
            return 1
        lines = [l for l in self.feed_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        return len(lines) + 1

    # -- applied state -------------------------------------------------

    def applied(self) -> dict[str, int]:
        if not self.applied_path.is_file():
            return {}
        return json.loads(self.applied_path.read_text(encoding="utf-8"))

    def record_applied(self, root: str, sequence: int) -> None:
        state = self.applied()
        state[root] = sequence
        self.applied_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def last_applied_sequence(self) -> int:
        values = self.applied().values()
        return max(values) if values else 0

    # -- receipts ------------------------------------------------------

    def write_receipt(self, receipt: Receipt) -> Path:
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        path = self.receipts_dir / f"{receipt.sequence:04d}-{receipt.erratum_id}.json"
        path.write_text(
            json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def all_receipts(self) -> list[tuple[str, dict[str, Any]]]:
        if not self.receipts_dir.is_dir():
            return []
        return [
            (p.name, json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(self.receipts_dir.glob("*.json"))
        ]

    def latest_receipt(self) -> dict[str, Any] | None:
        receipts = self.all_receipts()
        return receipts[-1][1] if receipts else None
