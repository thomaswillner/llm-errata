"""Adapter-conformance corpus and validator controls.

These tests use public validator seams. The external candidate fixture is not
imported or copied: each expectation is derived from the LLM Errata contract.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from prototype.conformance import (
    ConformanceInputError,
    PropositionObservation,
    ReferenceConformanceAdapter,
    ReferenceConformanceBinding,
    TracingAdapter,
    compare_complete_outcome,
    compare_proposition_multiplicity,
    load_corpus,
    load_binding_factory,
    run_validator_anti_vacuity_controls,
    validate_adapter_conformance,
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

    def test_noncanonical_corpus_path_is_refused_for_execution(self) -> None:
        path = self.changed_corpus(lambda value: None)
        with self.assertRaisesRegex(ConformanceInputError, "canonical checked-in"):
            load_corpus(path, ROOT, require_canonical_path=True)

    def test_normative_source_must_be_reachable_from_runtime_history(self) -> None:
        path = self.changed_corpus(
            lambda value: value["cases"][0]["normative"].__setitem__(
                "commit", "f" * 40
            )
        )
        with self.assertRaisesRegex(ConformanceInputError, "reachable"):
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

    def test_every_provenance_field_is_bound_to_the_accepted_contribution(self) -> None:
        expected = {
            "reported_by": "Rastislav Drahos / DanceNitra",
            "source_url": "https://github.com/DanceNitra/agora/tree/2ba1e299b3483b9038d03387345702427608b90b/contrib/llm-errata-adapter-conformance",
            "source_commit": "2ba1e299b3483b9038d03387345702427608b90b",
            "source_license": "MIT",
            "relationship": "interested-party: Inspeximus is a G4 adapter candidate",
            "ai_assistance": "Source commit discloses Claude Opus 5 co-authorship.",
            "implementation": "Independently authored in LLM Errata; external runner and fixture files were not copied or vendored.",
        }
        self.assertEqual(load_corpus(CORPUS, ROOT).provenance, expected)
        for field in expected:
            with self.subTest(field=field):
                path = self.changed_corpus(
                    lambda value, field=field: value["provenance"].__setitem__(
                        field, "plausible but wrong"
                    )
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

    def test_trace_window_can_exclude_fixture_and_observation_calls(self) -> None:
        class Adapter:
            def coverage(self, root: str) -> str:
                return root

        traced = TracingAdapter(Adapter())
        traced.coverage("fixture")
        traced.reset_calls()
        traced.coverage("controller")
        calls = traced.calls
        traced.coverage("observation")
        self.assertEqual(calls, ("coverage",))
        self.assertEqual(traced.calls, ("coverage", "coverage"))


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

    def test_json_scalar_types_must_match_exactly(self) -> None:
        for wrong in (1, 1.0):
            with self.subTest(wrong=wrong):
                expected = self.outcome()
                observed = self.outcome()
                observed["receipt"]["names_store"] = wrong
                self.assertIn(
                    f"receipt.names_store: expected True, got {wrong!r}",
                    compare_complete_outcome(expected, observed),
                )


class PropositionMultiplicity(unittest.TestCase):
    def test_reference_observations_use_stable_provider_local_ids_and_counts(self) -> None:
        observations = ReferenceConformanceAdapter().proposition_observations()
        self.assertEqual(
            observations,
            (
                PropositionObservation("fixture:budget", "budget", 2),
                PropositionObservation("fixture:diet", "diet", 2),
                PropositionObservation("fixture:pet", "pet", 1),
                PropositionObservation("fixture:quiet", "quiet", 2),
            ),
        )

    def test_text_equivalence_or_substrings_cannot_create_proposition_identity(self) -> None:
        adapter = ReferenceConformanceAdapter()
        before = adapter.proposition_observations()
        adapter._active["text-only-alias"] = (
            "prefix prefers quiet restaurants suffix; moderate budget-ish"
        )
        after = adapter.proposition_observations()
        self.assertEqual(compare_proposition_multiplicity(before, after), "known")

    def test_unavailable_identity_or_count_is_unknown(self) -> None:
        before = (PropositionObservation("fixture:quiet", "quiet", 2),)
        self.assertEqual(compare_proposition_multiplicity(before, None), "unknown")

    def test_exact_identity_count_increase_is_detected(self) -> None:
        before = (PropositionObservation("fixture:quiet", "quiet", 2),)
        after = (PropositionObservation("fixture:quiet", "quiet", 3),)
        self.assertEqual(compare_proposition_multiplicity(before, after), "increased")


class AdapterCases(unittest.TestCase):
    def test_reference_binding_passes_five_cases_and_exact_mutations(self) -> None:
        report = validate_adapter_conformance(
            CORPUS, ROOT, ReferenceConformanceBinding
        )
        self.assertTrue(report.passed, report.canonical_json())
        self.assertEqual(len(report.cases), 5)
        for result in report.cases:
            self.assertTrue(result.expectation_met, result.failures)
            self.assertTrue(result.positive_control_passed, result.missing_calls)
            self.assertTrue(result.mutation_control_passed, result.mutation_failures)

    def test_binding_execution_fault_is_invalid_evidence(self) -> None:
        class ExplodingBinding(ReferenceConformanceBinding):
            name = "exploding"

            def apply_mutation(self, case, importer, adapter, context) -> None:
                raise RuntimeError("mutation setup broke")

        with self.assertRaisesRegex(ConformanceInputError, "binding execution"):
            validate_adapter_conformance(CORPUS, ROOT, ExplodingBinding)

    def test_binding_execution_has_a_hard_timeout(self) -> None:
        class SlowBinding(ReferenceConformanceBinding):
            def build(self, case):
                time.sleep(0.1)
                return super().build(case)

        with patch("prototype.conformance.BINDING_TIMEOUT_SECONDS", 0.01):
            with self.assertRaisesRegex(ConformanceInputError, "timed out"):
                validate_adapter_conformance(CORPUS, ROOT, SlowBinding)

    def test_binding_constructor_has_a_hard_timeout(self) -> None:
        class SlowConstructorBinding(ReferenceConformanceBinding):
            def __init__(self):
                time.sleep(0.1)

        with patch("prototype.conformance.BINDING_TIMEOUT_SECONDS", 0.01):
            with self.assertRaisesRegex(ConformanceInputError, "timed out"):
                validate_adapter_conformance(CORPUS, ROOT, SlowConstructorBinding)

    def test_binding_metadata_has_a_hard_timeout(self) -> None:
        class SlowMetadataBinding(ReferenceConformanceBinding):
            @property
            def name(self):
                time.sleep(0.1)
                return "slow-metadata"

        with patch("prototype.conformance.BINDING_TIMEOUT_SECONDS", 0.01):
            with self.assertRaisesRegex(
                ConformanceInputError, "binding metadata timed out"
            ):
                validate_adapter_conformance(CORPUS, ROOT, SlowMetadataBinding)


class RuntimeSourceIdentity(unittest.TestCase):
    def test_report_binds_clean_runtime_commit_tree_and_binding_source(self) -> None:
        report = validate_adapter_conformance(CORPUS, ROOT, ReferenceConformanceBinding)
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        self.assertEqual(report.runtime_commit, commit)
        self.assertEqual(report.runtime_tree, tree)
        self.assertEqual(report.binding_source["path"], "prototype/conformance.py")
        self.assertRegex(report.binding_source["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(report.binding_source["commit"], commit)
        self.assertEqual(report.binding_source["tree"], tree)
        self.assertRegex(report.corpus_sha256, r"^[0-9a-f]{64}$")

    def test_external_binding_can_be_bound_to_its_own_clean_repository(self) -> None:
        with tempfile.TemporaryDirectory(prefix="errata-binding-") as directory:
            binding_root = Path(directory)
            source = binding_root / "binding.py"
            source.write_text("def factory():\n    return None\n", encoding="utf-8")
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Conformance Tests"),
                ("git", "add", "binding.py"),
                ("git", "commit", "-q", "-m", "binding"),
            ):
                subprocess.run(command, cwd=binding_root, check=True)
            namespace: dict[str, object] = {}
            exec(compile(source.read_text(), str(source), "exec"), namespace)
            factory = namespace["factory"]
            factory.__module__ = "binding"
            with patch("prototype.conformance.inspect.getsourcefile", return_value=str(source)):
                from prototype.conformance import _binding_source

                identity = _binding_source(factory, binding_root)
            self.assertEqual(identity["path"], "binding.py")
            self.assertRegex(identity["commit"], r"^[0-9a-f]{40}$")

    def test_sourceless_binding_factory_is_invalid_evidence(self) -> None:
        from prototype.conformance import _binding_source

        with self.assertRaisesRegex(ConformanceInputError, "clean Git repository"):
            _binding_source(dict, None)

    def test_binding_import_runtime_error_is_invalid_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="errata-binding-import-") as directory:
            root = Path(directory)
            (root / "broken.py").write_text(
                'raise RuntimeError("top-level failure")\n', encoding="utf-8"
            )
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Conformance Tests"),
                ("git", "add", "broken.py"),
                ("git", "commit", "-q", "-m", "binding"),
            ):
                subprocess.run(command, cwd=root, check=True)
            with patch("sys.path", [str(root), *sys.path]):
                with self.assertRaisesRegex(ConformanceInputError, "RuntimeError"):
                    with load_binding_factory("broken:factory", root):
                        pass

    def test_binding_import_has_a_hard_timeout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="errata-binding-import-") as directory:
            root = Path(directory)
            (root / "slow.py").write_text(
                "import time\ntime.sleep(0.1)\ndef factory():\n    return None\n",
                encoding="utf-8",
            )
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Conformance Tests"),
                ("git", "add", "slow.py"),
                ("git", "commit", "-q", "-m", "binding"),
            ):
                subprocess.run(command, cwd=root, check=True)
            with patch("sys.path", [str(root), *sys.path]), patch(
                "prototype.conformance.BINDING_TIMEOUT_SECONDS", 0.01
            ):
                with self.assertRaisesRegex(ConformanceInputError, "import timed out"):
                    with load_binding_factory("slow:factory", root):
                        pass

    def test_binding_executes_the_admitted_bytes_not_a_reopened_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="errata-binding-import-") as directory:
            root = Path(directory)
            source = root / "stable.py"
            source.write_text(
                'def factory():\n    return "ADMITTED"\n', encoding="utf-8"
            )
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Conformance Tests"),
                ("git", "add", "stable.py"),
                ("git", "commit", "-q", "-m", "binding"),
            ):
                subprocess.run(command, cwd=root, check=True)
            original_read = Path.read_bytes

            def substitute_after_read(path: Path) -> bytes:
                payload = original_read(path)
                if path.resolve() == source.resolve():
                    source.write_text(
                        'def factory():\n    return "SUBSTITUTED"\n', encoding="utf-8"
                    )
                return payload

            with patch("pathlib.Path.read_bytes", substitute_after_read):
                with self.assertRaisesRegex(ConformanceInputError, "dirty"):
                    with load_binding_factory("stable:factory", root) as (factory, _):
                        self.assertEqual(factory(), "ADMITTED")

    def test_preloaded_package_dependency_cannot_inject_unbound_behavior(self) -> None:
        with tempfile.TemporaryDirectory(prefix="errata-binding-package-") as directory:
            root = Path(directory)
            package = root / "bindingpkg"
            package.mkdir()
            (package / "__init__.py").write_text(
                "from .helper import VALUE\n"
                "def factory():\n"
                "    return VALUE\n",
                encoding="utf-8",
            )
            (package / "helper.py").write_text(
                'VALUE = "COMMITTED"\n', encoding="utf-8"
            )
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Conformance Tests"),
                ("git", "add", "bindingpkg"),
                ("git", "commit", "-q", "-m", "binding"),
            ):
                subprocess.run(command, cwd=root, check=True)
            cached = types.ModuleType("bindingpkg.helper")
            cached.VALUE = "CACHED-UNBOUND"
            prior = sys.modules.get("bindingpkg.helper")
            sys.modules["bindingpkg.helper"] = cached
            try:
                with load_binding_factory("bindingpkg:factory", root) as (factory, identity):
                    self.assertEqual(factory(), "COMMITTED")
                self.assertRegex(
                    identity["dependency_manifest_sha256"], r"^[0-9a-f]{64}$"
                )
            finally:
                if prior is None:
                    sys.modules.pop("bindingpkg.helper", None)
                else:
                    sys.modules["bindingpkg.helper"] = prior

    def test_dotted_binding_isolates_parent_and_sibling_module_cache(self) -> None:
        with tempfile.TemporaryDirectory(prefix="errata-binding-package-") as directory:
            root = Path(directory)
            package = root / "bindingpkg"
            package.mkdir()
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "subbinding.py").write_text(
                "from .helper import VALUE\n"
                "def factory():\n"
                "    return VALUE\n",
                encoding="utf-8",
            )
            (package / "helper.py").write_text(
                'VALUE = "COMMITTED"\n', encoding="utf-8"
            )
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Conformance Tests"),
                ("git", "add", "bindingpkg"),
                ("git", "commit", "-q", "-m", "binding"),
            ):
                subprocess.run(command, cwd=root, check=True)
            cached_parent = types.ModuleType("bindingpkg")
            cached_parent.__path__ = [str(package)]
            cached_helper = types.ModuleType("bindingpkg.helper")
            cached_helper.VALUE = "CACHED-UNBOUND"
            prior_parent = sys.modules.get("bindingpkg")
            prior_helper = sys.modules.get("bindingpkg.helper")
            sys.modules["bindingpkg"] = cached_parent
            sys.modules["bindingpkg.helper"] = cached_helper
            try:
                with load_binding_factory(
                    "bindingpkg.subbinding:factory", root
                ) as (factory, identity):
                    self.assertEqual(factory(), "COMMITTED")
                    self.assertIsNot(sys.modules["bindingpkg"], cached_parent)
                    self.assertIsNot(sys.modules["bindingpkg.helper"], cached_helper)
                self.assertIs(sys.modules["bindingpkg"], cached_parent)
                self.assertIs(sys.modules["bindingpkg.helper"], cached_helper)
            finally:
                if prior_parent is None:
                    sys.modules.pop("bindingpkg", None)
                else:
                    sys.modules["bindingpkg"] = prior_parent
                if prior_helper is None:
                    sys.modules.pop("bindingpkg.helper", None)
                else:
                    sys.modules["bindingpkg.helper"] = prior_helper
            self.assertRegex(
                identity["dependency_manifest_sha256"], r"^[0-9a-f]{64}$"
            )

    def test_lazy_dependency_import_remains_isolated_for_factory_lifetime(self) -> None:
        with tempfile.TemporaryDirectory(prefix="errata-binding-package-") as directory:
            root = Path(directory)
            package = root / "bindingpkg"
            package.mkdir()
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "subbinding.py").write_text(
                "def factory():\n"
                "    from .helper import VALUE\n"
                "    return VALUE\n",
                encoding="utf-8",
            )
            (package / "helper.py").write_text(
                'VALUE = "COMMITTED"\n', encoding="utf-8"
            )
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "tests@example.invalid"),
                ("git", "config", "user.name", "Conformance Tests"),
                ("git", "add", "bindingpkg"),
                ("git", "commit", "-q", "-m", "binding"),
            ):
                subprocess.run(command, cwd=root, check=True)
            cached_parent = types.ModuleType("bindingpkg")
            cached_parent.__path__ = [str(package)]
            cached_helper = types.ModuleType("bindingpkg.helper")
            cached_helper.VALUE = "CACHED-UNBOUND"
            saved = {name: sys.modules.get(name) for name in ("bindingpkg", "bindingpkg.helper")}
            sys.modules["bindingpkg"] = cached_parent
            sys.modules["bindingpkg.helper"] = cached_helper
            try:
                with load_binding_factory(
                    "bindingpkg.subbinding:factory", root
                ) as (factory, identity):
                    self.assertEqual(factory(), "COMMITTED")
                self.assertRegex(identity["dependency_manifest_sha256"], r"^[0-9a-f]{64}$")
            finally:
                for name, module in saved.items():
                    if module is None:
                        sys.modules.pop(name, None)
                    else:
                        sys.modules[name] = module

    def test_dirty_runtime_tree_is_refused_before_binding_execution(self) -> None:
        with tempfile.TemporaryDirectory(prefix="errata-dirty-source-") as directory:
            source_root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=source_root, check=True)
            marker = source_root / "tracked.txt"
            marker.write_text("clean\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=source_root, check=True)
            subprocess.run(
                [
                    "git", "-c", "user.name=LLM Errata Tests",
                    "-c", "user.email=tests@example.invalid",
                    "commit", "-q", "-m", "fixture",
                ],
                cwd=source_root,
                check=True,
            )
            marker.write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(ConformanceInputError, "dirty"):
                validate_adapter_conformance(
                    CORPUS, source_root, ReferenceConformanceBinding
                )

    def test_git_timeout_is_invalid_source_evidence(self) -> None:
        with patch(
            "prototype.conformance.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["git"], 5),
        ):
            with self.assertRaisesRegex(ConformanceInputError, "timed out"):
                load_corpus(CORPUS, ROOT)


class AntiVacuity(unittest.TestCase):
    def test_all_declared_validator_attacks_are_rejected(self) -> None:
        corpus = load_corpus(CORPUS, ROOT)
        controls = run_validator_anti_vacuity_controls(corpus, ROOT)
        self.assertEqual(
            [item.control_id for item in controls],
            [
                "empty-receipt-must-fail",
                "no-op-feed-verification-must-fail",
                "constant-unknown-aggregator-must-fail",
            ],
        )
        self.assertTrue(all(item.passed for item in controls), controls)
        self.assertEqual(
            [item.observed_failure for item in controls],
            [
                "receipt is vacuous",
                "accepted feed is incomplete",
                "semantic verdict diversity is missing",
            ],
        )

    def test_permissive_receipt_validator_makes_empty_receipt_control_fail(self) -> None:
        corpus = load_corpus(CORPUS, ROOT)
        controls = run_validator_anti_vacuity_controls(
            corpus, ROOT, receipt_validator=lambda value: (),
        )
        self.assertFalse(controls[0].passed)

    def test_permissive_production_receipt_schema_makes_control_fail(self) -> None:
        corpus = load_corpus(CORPUS, ROOT)
        with patch("prototype.receipts.receipt_acceptance_errors", return_value=()):
            controls = run_validator_anti_vacuity_controls(corpus, ROOT)
        self.assertFalse(controls[0].passed)

    def test_no_op_feed_verifier_makes_acceptance_control_fail(self) -> None:
        corpus = load_corpus(CORPUS, ROOT)
        controls = run_validator_anti_vacuity_controls(
            corpus, ROOT, feed_verifier=lambda errata, **kwargs: list(errata),
        )
        self.assertFalse(controls[1].passed)

    def test_unrelated_gap_exception_cannot_satisfy_feed_control(self) -> None:
        corpus = load_corpus(CORPUS, ROOT)

        def crash(*args, **kwargs):
            raise RuntimeError("unrelated gap in logging")

        controls = run_validator_anti_vacuity_controls(
            corpus, ROOT, feed_verifier=crash,
        )
        self.assertFalse(controls[1].passed)

    def test_constant_unknown_semantic_runner_makes_diversity_control_fail(self) -> None:
        from prototype.semantic import SemanticCoverage

        class ConstantUnknownRunner:
            def run(self, probes, config, verifier):
                return type("Report", (), {"coverage": SemanticCoverage.UNKNOWN})()

        corpus = load_corpus(CORPUS, ROOT)
        controls = run_validator_anti_vacuity_controls(
            corpus, ROOT, semantic_runner_factory=ConstantUnknownRunner,
        )
        self.assertFalse(controls[2].passed)

if __name__ == "__main__":
    unittest.main()
