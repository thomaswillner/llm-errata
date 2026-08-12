"""Provider-neutral, fail-closed semantic probe evidence."""

from __future__ import annotations

import hashlib
import json
import unittest

from prototype.semantic import (
    ObservationVerdict,
    ERASURE_NEGATIVE_PROBE_ID,
    ERASURE_PRESERVATION_PROBE_ID,
    ERASURE_PROMPT_TEMPLATE,
    ProbeKind,
    RecordedSemanticVerifier,
    SemanticCoverage,
    SemanticObservation,
    SemanticProbe,
    SemanticProbeReport,
    SemanticProbeRunner,
    VerifierConfig,
)
from prototype.errata import Operation


CONFIG = VerifierConfig(
    provider="synthetic-provider",
    model="synthetic-model-1",
    prompt_template_version="2026-08-12",
    sampling={"temperature": 0},
    seed=7,
)


def probe(
    probe_id: str, kind: ProbeKind, *, required: bool = True, operation: Operation = Operation.CORRECT
) -> SemanticProbe:
    return SemanticProbe(
        probe_id=(
            ERASURE_NEGATIVE_PROBE_ID if kind is ProbeKind.NEGATIVE else ERASURE_PRESERVATION_PROBE_ID
        ) if operation is Operation.ERASE else probe_id,
        kind=kind,
        operation=operation,
        scope="declared-store-set-v1" if operation is Operation.ERASE else "current-answer-sample",
        prompt_template=(
            ERASURE_PROMPT_TEMPLATE
            if operation is Operation.ERASE
            else f"synthetic-{kind.value}-prompt"
        ),
        required=required,
    )


def observation(
    probe_id: str, verdict: ObservationVerdict, *, config: VerifierConfig = CONFIG
) -> SemanticObservation:
    return SemanticObservation(
        probe_id=probe_id,
        verdict=verdict,
        config_digest=config.digest,
        observed_at="2026-08-12T09:00:00Z",
        response_digest=hashlib.sha256(probe_id.encode("utf-8")).hexdigest(),
    )


class VerifierConfiguration(unittest.TestCase):
    def test_configuration_digest_is_canonical_across_mapping_order(self) -> None:
        reordered = VerifierConfig(
            provider="synthetic-provider",
            model="synthetic-model-1",
            prompt_template_version="2026-08-12",
            sampling={"temperature": 0, "top_p": 1},
            seed=7,
        )
        ordered = VerifierConfig(
            provider="synthetic-provider",
            model="synthetic-model-1",
            prompt_template_version="2026-08-12",
            sampling={"top_p": 1, "temperature": 0},
            seed=7,
        )
        self.assertEqual(reordered.digest, ordered.digest)
        self.assertEqual(len(reordered.digest), 64)

    def test_nested_sampling_is_detached_from_caller_and_serialized_copy(self) -> None:
        supplied = {"nested": {"temperature": 0}, "stops": ["END"]}
        config = VerifierConfig("p", "m", "v", supplied)
        digest = config.digest
        supplied["nested"]["temperature"] = 1
        emitted = config.to_dict()
        emitted["sampling"]["nested"]["temperature"] = 2
        self.assertEqual(config.digest, digest)
        self.assertEqual(config.to_dict()["sampling"]["nested"]["temperature"], 0)


class Aggregation(unittest.TestCase):
    def setUp(self) -> None:
        self.probes = (
            probe("negative", ProbeKind.NEGATIVE),
            probe("positive", ProbeKind.POSITIVE),
            probe("preserve", ProbeKind.PRESERVATION),
        )

    def report_for(self, observations: tuple[SemanticObservation, ...]):
        return SemanticProbeRunner().run(
            self.probes, CONFIG, RecordedSemanticVerifier(observations)
        )

    def test_all_required_passing_observations_are_verified(self) -> None:
        report = self.report_for(
            tuple(observation(item.probe_id, ObservationVerdict.PASS) for item in self.probes)
        )
        self.assertEqual(report.coverage, SemanticCoverage.VERIFIED)
        self.assertEqual(report.limitations, ())

    def test_required_failure_is_failed(self) -> None:
        report = self.report_for(
            (
                observation("negative", ObservationVerdict.FAIL),
                observation("positive", ObservationVerdict.PASS),
                observation("preserve", ObservationVerdict.PASS),
            )
        )
        self.assertEqual(report.coverage, SemanticCoverage.FAILED)

    def test_required_failure_takes_precedence_over_other_limitations(self) -> None:
        report = self.report_for((
            observation("negative", ObservationVerdict.FAIL),
            observation("positive", ObservationVerdict.PASS),
        ))
        self.assertEqual(report.coverage, SemanticCoverage.FAILED)

    def test_duplicate_required_failure_is_invalid_and_unknown(self) -> None:
        report = self.report_for((
            observation("negative", ObservationVerdict.FAIL),
            observation("negative", ObservationVerdict.PASS),
            observation("positive", ObservationVerdict.PASS),
            observation("preserve", ObservationVerdict.PASS),
        ))
        self.assertEqual(report.coverage, SemanticCoverage.UNKNOWN)

    def test_inconclusive_or_error_required_observations_are_unknown(self) -> None:
        for verdict in (ObservationVerdict.INCONCLUSIVE, ObservationVerdict.ERROR):
            with self.subTest(verdict=verdict):
                report = self.report_for(
                    (
                        observation("negative", verdict),
                        observation("positive", ObservationVerdict.PASS),
                        observation("preserve", ObservationVerdict.PASS),
                    )
                )
                self.assertEqual(report.coverage, SemanticCoverage.UNKNOWN)
                self.assertTrue(report.limitations)

    def test_missing_duplicate_and_configuration_drift_are_unknown(self) -> None:
        drifted = VerifierConfig(
            provider="other-provider",
            model="synthetic-model-1",
            prompt_template_version="2026-08-12",
            sampling={"temperature": 0},
        )
        cases = {
            "missing": (
                observation("negative", ObservationVerdict.PASS),
                observation("positive", ObservationVerdict.PASS),
            ),
            "duplicate": (
                observation("negative", ObservationVerdict.PASS),
                observation("negative", ObservationVerdict.PASS),
                observation("positive", ObservationVerdict.PASS),
                observation("preserve", ObservationVerdict.PASS),
            ),
            "drift": (
                observation("negative", ObservationVerdict.PASS, config=drifted),
                observation("positive", ObservationVerdict.PASS),
                observation("preserve", ObservationVerdict.PASS),
            ),
        }
        for name, records in cases.items():
            with self.subTest(case=name):
                report = self.report_for(records)
                self.assertEqual(report.coverage, SemanticCoverage.UNKNOWN)
                self.assertTrue(report.limitations)

    def test_unexpected_or_only_optional_evidence_cannot_verify_coverage(self) -> None:
        unexpected = self.report_for(
            (
                observation("negative", ObservationVerdict.PASS),
                observation("positive", ObservationVerdict.PASS),
                observation("preserve", ObservationVerdict.PASS),
                observation("unrelated", ObservationVerdict.PASS),
            )
        )
        with self.assertRaises(ValueError):
            SemanticProbeRunner().run(
                (probe("optional", ProbeKind.NEGATIVE, required=False),),
                CONFIG,
                RecordedSemanticVerifier((observation("optional", ObservationVerdict.PASS),)),
            )
        self.assertEqual(unexpected.coverage, SemanticCoverage.UNKNOWN)


class SerializationAndPrivacy(unittest.TestCase):
    def test_report_serialization_is_deterministic(self) -> None:
        probes = (
            probe("preserve", ProbeKind.PRESERVATION, operation=Operation.ERASE),
            probe("negative", ProbeKind.NEGATIVE, operation=Operation.ERASE),
        )
        observations = (
            observation("negative", ObservationVerdict.PASS),
            observation("preserve", ObservationVerdict.PASS),
        )
        report = SemanticProbeRunner().run(probes, CONFIG, RecordedSemanticVerifier(observations))
        self.assertEqual(
            report.canonical_json(),
            json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":")),
        )

    def test_erasure_report_does_not_disclose_retired_value(self) -> None:
        erased_value = "orchid-lantern-secret"
        erasure_probe = probe(
            ERASURE_NEGATIVE_PROBE_ID, ProbeKind.NEGATIVE, operation=Operation.ERASE
        )
        preservation_probe = probe(
            ERASURE_PRESERVATION_PROBE_ID, ProbeKind.PRESERVATION, operation=Operation.ERASE
        )
        report = SemanticProbeRunner().run(
            (erasure_probe, preservation_probe),
            CONFIG,
            RecordedSemanticVerifier(
                (
                    observation(ERASURE_NEGATIVE_PROBE_ID, ObservationVerdict.PASS),
                    observation(ERASURE_PRESERVATION_PROBE_ID, ObservationVerdict.PASS),
                )
            ),
        )
        self.assertNotIn(erased_value, report.canonical_json())

    def test_erasure_rejects_prompt_template_that_can_embed_a_retired_value(self) -> None:
        with self.assertRaises(ValueError):
            SemanticProbe(
                "erase-negative", ProbeKind.NEGATIVE, Operation.ERASE,
                "current-answer-sample", "Does it remember orchid-lantern-secret?",
            )

    def test_erasure_rejects_retired_prose_in_every_persisted_probe_string(self) -> None:
        erased = "orchid lantern secret"
        for field in ("probe_id", "scope", "prompt_template"):
            values = {
                "probe_id": "erase_negative",
                "scope": "erasure-scope-v1",
                "prompt_template": ERASURE_PROMPT_TEMPLATE,
            }
            values[field] = erased
            with self.subTest(field=field), self.assertRaises(ValueError):
                SemanticProbe(
                    values["probe_id"], ProbeKind.NEGATIVE, Operation.ERASE,
                    values["scope"], values["prompt_template"],
                )

    def test_erasure_rejects_caller_selected_protocol_identifiers(self) -> None:
        with self.assertRaises(ValueError):
            SemanticProbe(
                "other-safe-token", ProbeKind.NEGATIVE, Operation.ERASE,
                "declared-store-set-v1", ERASURE_PROMPT_TEMPLATE,
            )

    def test_report_parser_rejects_contradictory_coverage(self) -> None:
        probes = (
            probe("negative", ProbeKind.NEGATIVE),
            probe("positive", ProbeKind.POSITIVE),
            probe("preserve", ProbeKind.PRESERVATION),
        )
        report = SemanticProbeRunner().run(probes, CONFIG, RecordedSemanticVerifier((
            observation("negative", ObservationVerdict.PASS),
            observation("positive", ObservationVerdict.PASS),
            observation("preserve", ObservationVerdict.PASS),
        )))
        payload = report.to_dict()
        payload["coverage"] = "failed"
        with self.assertRaises(ValueError):
            SemanticProbeReport.from_dict(payload)

    def test_unexpected_erasure_observation_identifier_is_not_persisted(self) -> None:
        retired = "orchid-lantern-secret"
        probes = (
            probe("ignored", ProbeKind.NEGATIVE, operation=Operation.ERASE),
            probe("ignored", ProbeKind.PRESERVATION, operation=Operation.ERASE),
        )
        report = SemanticProbeRunner().run(probes, CONFIG, RecordedSemanticVerifier((
            observation(ERASURE_NEGATIVE_PROBE_ID, ObservationVerdict.PASS),
            observation(ERASURE_PRESERVATION_PROBE_ID, ObservationVerdict.PASS),
            observation(retired, ObservationVerdict.PASS),
        )))
        self.assertEqual(report.coverage, SemanticCoverage.UNKNOWN)
        self.assertEqual(len(report.observations), 2)
        self.assertIn("unexpected observation identifiers: 1", report.limitations)
        self.assertNotIn(retired, report.canonical_json())

    def test_report_parser_rejects_supplied_limitations_and_missing_triad(self) -> None:
        probes = (
            probe("negative", ProbeKind.NEGATIVE),
            probe("positive", ProbeKind.POSITIVE),
            probe("preserve", ProbeKind.PRESERVATION),
        )
        report = SemanticProbeRunner().run(probes, CONFIG, RecordedSemanticVerifier((
            observation("negative", ObservationVerdict.PASS),
            observation("positive", ObservationVerdict.PASS),
            observation("preserve", ObservationVerdict.PASS),
        )))
        payload = report.to_dict()
        payload["limitations"] = ["invented limitation"]
        with self.assertRaises(ValueError):
            SemanticProbeReport.from_dict(payload)
        payload = report.to_dict()
        payload["probes"].pop()
        with self.assertRaises(ValueError):
            SemanticProbeReport.from_dict(payload)


class RequiredTriadAndAdapterBoundaries(unittest.TestCase):
    def test_required_triads_and_operation_vocabulary_are_enforced(self) -> None:
        runner = SemanticProbeRunner()
        with self.assertRaises(ValueError):
            runner.run((probe("negative", ProbeKind.NEGATIVE),), CONFIG, ())
        with self.assertRaises(ValueError):
            runner.run((
                probe("negative", ProbeKind.NEGATIVE, operation=Operation.ERASE),
                probe("preserve", ProbeKind.PRESERVATION, operation=Operation.ERASE),
                probe("positive", ProbeKind.POSITIVE, operation=Operation.ERASE),
            ), CONFIG, ())
        with self.assertRaises(ValueError):
            SemanticProbe("bad", ProbeKind.NEGATIVE, "correct", "scope", "template")

    def test_provider_exception_and_malformed_result_are_unknown(self) -> None:
        class Explodes:
            def evaluate(self, probe, config):
                raise RuntimeError("provider down")
        class Malformed:
            def evaluate(self, probe, config):
                return "pass"
        probes = (
            probe("negative", ProbeKind.NEGATIVE), probe("positive", ProbeKind.POSITIVE),
            probe("preserve", ProbeKind.PRESERVATION),
        )
        for verifier in (Explodes(), Malformed()):
            report = SemanticProbeRunner().run(probes, CONFIG, verifier)
            self.assertEqual(report.coverage, SemanticCoverage.UNKNOWN)
            self.assertTrue(report.limitations)


class StrictParsing(unittest.TestCase):
    def test_observation_parser_rejects_free_form_output_and_bad_digest(self) -> None:
        payload = observation("negative", ObservationVerdict.PASS).to_dict()
        payload["raw_output"] = "pass because retired value was absent"
        with self.assertRaises(ValueError):
            SemanticObservation.from_dict(payload)
        payload.pop("raw_output")
        payload["response_digest"] = "not-a-sha256"
        with self.assertRaises(ValueError):
            SemanticObservation.from_dict(payload)
        payload["response_digest"] = observation(
            "negative", ObservationVerdict.PASS
        ).response_digest
        payload["observed_at"] = "not-a-timestamp"
        with self.assertRaises(ValueError):
            SemanticObservation.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
