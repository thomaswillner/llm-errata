"""Adapter-conformance corpus and validator controls.

These tests use public validator seams. The external candidate fixture is not
imported or copied: each expectation is derived from the LLM Errata contract.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from prototype.conformance import ConformanceInputError, load_corpus


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "spec" / "adapter-conformance.json"


class CorpusValidation(unittest.TestCase):
    def changed_corpus(self, change) -> Path:
        payload = json.loads(CORPUS.read_text(encoding="utf-8"))
        change(payload)
        directory = tempfile.TemporaryDirectory(prefix="errata-corpus-")
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "corpus.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_checked_in_corpus_binds_immutable_normative_sources(self) -> None:
        corpus = load_corpus(CORPUS, ROOT)
        self.assertEqual(corpus.schema_version, 1)
        self.assertEqual(
            corpus.normative_target.commit,
            "ac4468faf73c2cc7949dd29b2a2a151f5bd23116",
        )
        self.assertEqual(len(corpus.cases), 5)
        self.assertEqual(len(corpus.validator_controls), 3)

    def test_wrong_surface_digest_is_refused(self) -> None:
        path = self.changed_corpus(
            lambda value: value["normative_target"].__setitem__("surface_digest", "0" * 64)
        )
        with self.assertRaisesRegex(ConformanceInputError, "surface digest"):
            load_corpus(path, ROOT)

    def test_new_current_surface_files_do_not_change_historical_manifest(self) -> None:
        corpus = load_corpus(CORPUS, ROOT)
        self.assertEqual(
            corpus.normative_target.surface_digest,
            "7e0d6c88c1ca3a87743ac70ba2a3dfea0b350d112d2d3c59a3c6cbb537568f12",
        )

    def test_quotation_drift_is_refused(self) -> None:
        path = self.changed_corpus(
            lambda value: value["cases"][0]["normative"].__setitem__(
                "quote", "Missing lineage is always verified."
            )
        )
        with self.assertRaisesRegex(ConformanceInputError, "quotation"):
            load_corpus(path, ROOT)

    def test_partial_expected_outcome_is_refused(self) -> None:
        def remove_aggregate(value) -> None:
            del value["cases"][0]["expected"]["aggregate"]

        with self.assertRaisesRegex(ConformanceInputError, "expected outcome"):
            load_corpus(self.changed_corpus(remove_aggregate), ROOT)

    def test_empty_provenance_is_refused(self) -> None:
        path = self.changed_corpus(
            lambda value: value["provenance"].__setitem__("source_url", "")
        )
        with self.assertRaisesRegex(ConformanceInputError, "provenance"):
            load_corpus(path, ROOT)


if __name__ == "__main__":
    unittest.main()
