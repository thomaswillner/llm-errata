"""Adapter-conformance corpus and validator controls.

These tests use public validator seams. The external candidate fixture is not
imported or copied: each expectation is derived from the LLM Errata contract.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from prototype.conformance import (
    ConformanceInputError,
    TracingAdapter,
    compare_complete_outcome,
    load_corpus,
)


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


class TargetTracing(unittest.TestCase):
    def test_only_calls_through_wrapped_target_are_recorded(self) -> None:
        class Adapter:
            name = "target"

            def coverage(self, root: str) -> str:
                return root

        adapter = Adapter()
        traced = TracingAdapter(adapter)

        def coverage(root: str) -> str:
            return root

        coverage("unrelated")
        self.assertEqual(traced.calls, ())
        self.assertEqual(traced.coverage("root"), "root")
        self.assertEqual(traced.calls, ("coverage",))
        self.assertIs(traced.target, adapter)

    def test_attribute_reads_do_not_count_as_method_calls(self) -> None:
        class Adapter:
            name = "target"

        traced = TracingAdapter(Adapter())
        self.assertEqual(traced.name, "target")
        self.assertEqual(traced.calls, ())


class CompleteComparison(unittest.TestCase):
    def outcome(self) -> dict[str, object]:
        return {
            "checkpoint": "verified",
            "aggregate": "verified",
            "triad": {
                "negative": "pass",
                "positive": "pass",
                "preserve": "pass",
            },
            "store": {
                "multiplicity": "known",
                "erased_absent": None,
                "preserved_present": True,
                "unrelated_present": True,
            },
            "receipt": {
                "names_store": True,
                "non_trivial": True,
                "forbidden_absent": None,
            },
        }

    def test_exact_outcome_passes(self) -> None:
        value = self.outcome()
        self.assertEqual(compare_complete_outcome(value, value), ())

    def test_extra_aggregate_and_triad_failures_are_rejected(self) -> None:
        expected = self.outcome()
        observed = self.outcome()
        observed["aggregate"] = "failed"
        observed["triad"] = {
            "negative": "pass",
            "positive": "fail",
            "preserve": "pass",
        }
        failures = compare_complete_outcome(expected, observed)
        self.assertIn("aggregate: expected 'verified', got 'failed'", failures)
        self.assertIn("triad.positive: expected 'pass', got 'fail'", failures)

    def test_missing_or_extra_fields_are_rejected(self) -> None:
        expected = self.outcome()
        observed = self.outcome()
        del observed["receipt"]["names_store"]
        observed["store"]["unexpected"] = True
        failures = compare_complete_outcome(expected, observed)
        self.assertIn("receipt.names_store: missing", failures)
        self.assertIn("store.unexpected: unexpected", failures)

if __name__ == "__main__":
    unittest.main()
