from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from prototype.checkpoints import (
    AdapterCheckpoint,
    CheckpointError,
    CheckpointStore,
    QuarantineCheckpoint,
)


class CheckpointModel(unittest.TestCase):
    def checkpoint(self) -> QuarantineCheckpoint:
        return QuarantineCheckpoint.create(
            erratum_id="err_0001",
            sequence=1,
            target_root="mem_01HX",
            pre_state_root="a" * 64,
            adapters=(
                AdapterCheckpoint("prompt_cache", True, (), "unknown", "opaque"),
                AdapterCheckpoint("sqlite", True, ("fact:diet", "summary:dining"), "verified", None),
            ),
            created_at="2026-08-12T10:00:00Z",
        )

    def test_digest_is_deterministic_literal_sha256(self) -> None:
        checkpoint = self.checkpoint()
        self.assertEqual(len(checkpoint.checkpoint_digest), 64)
        self.assertEqual(checkpoint.canonical_digest(), checkpoint.checkpoint_digest)
        self.assertEqual(QuarantineCheckpoint.from_dict(checkpoint.to_dict()), checkpoint)

    def test_content_mutation_is_rejected(self) -> None:
        payload = self.checkpoint().to_dict()
        payload["target_root"] = "mem_other"
        with self.assertRaisesRegex(CheckpointError, "digest"):
            QuarantineCheckpoint.from_dict(payload)

    def test_consumption_preserves_quarantine_identity(self) -> None:
        checkpoint = self.checkpoint()
        consumed = checkpoint.with_consumed("2026-08-12T11:00:00Z")
        self.assertEqual(consumed.checkpoint_digest, checkpoint.checkpoint_digest)
        self.assertTrue(consumed.consumed)

    def test_duplicate_or_unsorted_artifacts_are_rejected(self) -> None:
        for artifacts in (("b", "a"), ("a", "a")):
            with self.subTest(artifacts=artifacts), self.assertRaises(CheckpointError):
                AdapterCheckpoint("sqlite", True, artifacts, "verified", None)

    def test_unsafe_erratum_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(CheckpointError, "erratum"):
            replace(self.checkpoint(), erratum_id="../escape")

    def test_truncated_pre_state_root_is_rejected(self) -> None:
        with self.assertRaisesRegex(CheckpointError, "pre-state root"):
            replace(self.checkpoint(), pre_state_root="a" * 32)


class CheckpointPersistence(unittest.TestCase):
    def test_atomic_round_trip_and_consumption(self) -> None:
        checkpoint = CheckpointModel().checkpoint()
        with tempfile.TemporaryDirectory() as temp:
            store = CheckpointStore(Path(temp))
            path = store.write(checkpoint)
            self.assertEqual(store.load(path), checkpoint)
            consumed = store.consume(path, "2026-08-12T11:00:00Z")
            self.assertTrue(consumed.consumed)
            self.assertEqual(json.loads(path.read_text())["consumed"], True)

    def test_invalid_json_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "0001-err_0001.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(CheckpointError, "JSON"):
                CheckpointStore(Path(temp)).load(path)


if __name__ == "__main__":
    unittest.main()
