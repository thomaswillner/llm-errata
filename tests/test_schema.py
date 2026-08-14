"""The wire schema, and the validator that enforces it.

The adversarial review of the plan raised the obvious objection: the same author
wrote the schema and the validator, so a matching pair of mistakes cancels out
and every test still passes. `OfficialTestSuite` below breaks that circle by
running cases vendored from the JSON-Schema-Test-Suite, which neither this
repository's schemas nor its validator had any hand in writing.

Cases whose schema uses a keyword the validator does not implement are skipped
and counted. The count is asserted to be a minority, so "skip everything" is not
a way to pass.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from prototype import schema
from prototype.adapters import Coverage
from prototype.scenario import DIET, build_importer
from prototype.signing import DemoSigner
from prototype.errata import Erratum, FeedError, Operation, OwnerKeySchedule, RootRegistry, verify_feed
from tests.test_regressions import supersede


REPO_ROOT = Path(__file__).resolve().parents[1]
SUITE = REPO_ROOT / "spec" / "vendor" / "json-schema-test-suite"
VECTORS = REPO_ROOT / "spec" / "vectors"

OWNER = DemoSigner(b"owner-secret")


def _uses_only_supported(node: object) -> bool:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"properties", "patternProperties", "$defs"}:
                if not all(_uses_only_supported(v) for v in value.values()):
                    return False
                continue
            if key not in schema.SUPPORTED_KEYWORDS:
                return False
            if not _uses_only_supported(value):
                return False
        return True
    if isinstance(node, list):
        return all(_uses_only_supported(item) for item in node)
    return True


class ValidatorRefusesWhatItCannotCheck(unittest.TestCase):
    def test_an_unsupported_keyword_raises_rather_than_being_ignored(self) -> None:
        # A validator that skips keywords it does not implement accepts
        # instances the published schema rejects, which is worse than having no
        # validator: implementers would build against a contract nobody
        # enforces.
        with self.assertRaises(schema.SchemaError) as raised:
            schema.validate({"a": 1}, {"type": "object", "unevaluatedProperties": False})
        self.assertIn("unevaluatedProperties", str(raised.exception))

    def test_an_unresolvable_ref_raises(self) -> None:
        with self.assertRaises(schema.SchemaError):
            schema.validate({}, {"$ref": "#/$defs/missing"})

    def test_a_remote_ref_is_refused(self) -> None:
        with self.assertRaises(schema.SchemaError):
            schema.validate({}, {"$ref": "https://example.invalid/x.json"})


class OfficialTestSuite(unittest.TestCase):
    """Cases written by the JSON Schema project, not by this repository."""

    def test_the_suite_is_vendored(self) -> None:
        self.assertTrue(SUITE.is_dir(), "official test suite is missing")
        self.assertGreater(len(list(SUITE.glob("*.json"))), 20)

    def test_every_supported_case_agrees_with_the_official_expectation(self) -> None:
        checked = skipped = 0
        failures: list[str] = []
        for path in sorted(SUITE.glob("*.json")):
            for group in json.loads(path.read_text(encoding="utf-8")):
                if not _uses_only_supported(group["schema"]):
                    skipped += len(group["tests"])
                    continue
                for case in group["tests"]:
                    try:
                        errors = schema.validate(case["data"], group["schema"])
                    except schema.SchemaError:
                        skipped += 1
                        continue
                    checked += 1
                    if bool(errors) == case["valid"]:
                        failures.append(
                            f"{path.name}: {group['description']} / "
                            f"{case['description']}: expected "
                            f"valid={case['valid']}, got errors={errors}"
                        )
        self.assertEqual(failures, [], "\n".join(failures[:15]))
        self.assertGreater(checked, 200, "too few official cases actually ran")
        self.assertLess(
            skipped,
            checked,
            "more official cases were skipped than checked; the supported "
            "keyword set is too narrow to claim conformance",
        )


class PublishedSchemas(unittest.TestCase):
    def test_both_schemas_load(self) -> None:
        for name in ("erratum", "receipt"):
            self.assertIsInstance(schema.load(name), dict)

    def test_an_unknown_schema_name_raises(self) -> None:
        with self.assertRaises(schema.SchemaError):
            schema.load("nonexistent")

    def test_receipt_state_roots_require_full_sha256_width(self) -> None:
        receipt_schema = schema.load("receipt")
        state_root = receipt_schema["$defs"]["stateRoot"]
        self.assertEqual(state_root["pattern"], "^[0-9a-f]{64}$")


class ConformanceVectors(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(
            (VECTORS / "manifest.json").read_text(encoding="utf-8")
        )

    def test_every_manifest_entry_has_a_file(self) -> None:
        for entry in self.manifest["vectors"]:
            self.assertTrue(
                (VECTORS / entry["file"]).is_file(), f"missing {entry['file']}"
            )

    def test_every_vector_file_is_in_the_manifest(self) -> None:
        listed = {entry["file"] for entry in self.manifest["vectors"]} | set(
            self.manifest["stateful_vectors"]
        )
        on_disk = {p.name for p in VECTORS.glob("*.json")} - {"manifest.json"}
        self.assertEqual(on_disk - listed, set(), "vectors not listed in the manifest")

    def test_each_vector_validates_exactly_as_the_manifest_says(self) -> None:
        for entry in self.manifest["vectors"]:
            with self.subTest(vector=entry["file"]):
                instance = json.loads(
                    (VECTORS / entry["file"]).read_text(encoding="utf-8")
                )
                errors = schema.validate(instance, schema.load(entry["schema"]))
                if entry["valid"]:
                    self.assertEqual(errors, [], f"{entry['file']} should validate")
                else:
                    self.assertNotEqual(
                        errors, [], f"{entry['file']} should have been rejected"
                    )
                    self.assertTrue(
                        any(entry["rejected_by"] in e for e in errors),
                        f"{entry['file']} was rejected, but not by "
                        f"{entry['rejected_by']!r}: {errors}",
                    )

    def test_the_invalid_vectors_are_not_all_rejected_for_one_reason(self) -> None:
        # If every invalid vector tripped the same keyword, the suite would be
        # testing one rule and claiming to test many.
        reasons = {
            entry["rejected_by"]
            for entry in self.manifest["vectors"]
            if not entry["valid"]
        }
        self.assertGreaterEqual(len(reasons), 4, reasons)


class StatefulProtocolVectors(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = json.loads(
            (VECTORS / "protocol-manifest.json").read_text(encoding="utf-8")
        )

    def _event(self, record: dict[str, object], signers: dict[str, DemoSigner]) -> Erratum:
        operation = Operation(record["operation"])
        postconditions = {"negative": "retired label", "preserve": "retained label"}
        replacement = None
        if operation is not Operation.ERASE:
            replacement = "replacement label"
            postconditions["positive"] = "replacement label"
        event = Erratum(
            erratum_id=record["erratum_id"],
            sequence=record["sequence"],
            target_root=record["target_root"],
            operation=operation,
            valid_from="2026-08-12T00:00:00Z",
            replacement=replacement,
            postconditions=postconditions,
        )
        return signers[record["signer"]].sign_erratum(event)

    def test_feed_vectors_execute_named_stateful_rules(self) -> None:
        for case in self.protocol["feed_cases"]:
            with self.subTest(case=case["id"]):
                signers = {
                    key_id: DemoSigner(seed.encode(), key_id=key_id)
                    for key_id, seed in case["keys"].items()
                }
                schedule = OwnerKeySchedule(tuple(
                    (activation["sequence"], signers[activation["key_id"]].public)
                    for activation in case["schedule"]
                ))
                events = [self._event(record, signers) for record in case["events"]]
                if case["outcome"] == "accept":
                    self.assertEqual(len(verify_feed(
                        events, owner=schedule, roots=RootRegistry(case["roots"])
                    )), len(events))
                else:
                    with self.assertRaisesRegex(FeedError, case["error_contains"]):
                        verify_feed(
                            events, owner=schedule, roots=RootRegistry(case["roots"])
                        )

    def test_split_view_vector_accepts_each_view_but_proves_no_global_consistency(self) -> None:
        for case in self.protocol["split_view_cases"]:
            with self.subTest(case=case["id"]):
                signers = {
                    key_id: DemoSigner(seed.encode(), key_id=key_id)
                    for key_id, seed in case["keys"].items()
                }
                schedule = OwnerKeySchedule(tuple(
                    (activation["sequence"], signers[activation["key_id"]].public)
                    for activation in case["schedule"]
                ))
                accepted_views = [
                    verify_feed(
                        [self._event(record, signers) for record in view],
                        owner=schedule,
                        roots=RootRegistry(case["roots"]),
                    )
                    for view in case["views"]
                ]
                self.assertEqual([len(view) for view in accepted_views], [1, 1])
                self.assertNotEqual(
                    accepted_views[0][0].erratum_id,
                    accepted_views[1][0].erratum_id,
                )
                self.assertEqual(
                    case["outcome"],
                    "accept-each-view-with-global-non-equivocation-unproven",
                )

    def test_confidentiality_vector_keeps_forbidden_value_out_of_evidence(self) -> None:
        case = self.protocol["confidentiality_case"]
        importer = build_importer(OWNER)
        receipt = importer.repair(OWNER.sign_erratum(Erratum(
            erratum_id="err_confidential_erase",
            sequence=1,
            target_root=case["target_root"],
            operation=Operation.ERASE,
            valid_from="2026-08-12T00:00:00Z",
            postconditions={"negative": case["negative_probe"], "preserve": "quiet restaurants|moderate budget"},
        )))
        evidence = json.dumps(receipt.to_dict(), sort_keys=True)
        self.assertNotIn(case["forbidden_value"], evidence)

    def test_every_receipt_field_mutation_breaks_signature_binding(self) -> None:
        fields = json.loads(
            (VECTORS / "receipt-binding-mutations.json").read_text(encoding="utf-8")
        )["fields"]
        receipt = build_importer(OWNER).repair(supersede())
        payload = receipt.to_dict()
        for field in fields:
            with self.subTest(field=field):
                mutated = dict(payload)
                mutated[field] = fields[field]
                rebuilt = receipt.__class__(
                    importer=mutated["importer"], erratum_id=mutated["erratum_id"],
                    sequence=mutated["sequence"], target_root=mutated["target_root"],
                    operation=mutated["operation"], pre_state_root=mutated["pre_state_root"],
                    post_state_root=mutated["post_state_root"],
                    stores={k: Coverage(v) for k, v in mutated["stores"].items()},
                    dispositions=mutated["dispositions"], triad=mutated["triad"],
                    aggregate=Coverage(mutated["aggregate"]),
                    limitations=mutated["limitations"], history_retained=mutated["history_retained"],
                    adapter_versions=mutated["adapter_versions"], signature=payload["signature"],
                )
                self.assertFalse(rebuilt.verify(OWNER.public))


class TheProtoypeAgreesWithItsOwnSchema(unittest.TestCase):
    def test_a_signed_erratum_validates(self) -> None:
        payload = supersede().signable()
        self.assertEqual(schema.validate(payload, schema.load("erratum")), [])

    def test_an_emitted_receipt_validates(self) -> None:
        receipt = build_importer(OWNER).repair(supersede())
        self.assertEqual(schema.validate(receipt.to_dict(), schema.load("receipt")), [])

    def test_a_receipt_from_every_aggregate_validates(self) -> None:
        for include_opaque in (True, False):
            with self.subTest(opaque=include_opaque):
                receipt = build_importer(
                    OWNER, include_opaque=include_opaque
                ).repair(supersede())
                self.assertEqual(
                    schema.validate(receipt.to_dict(), schema.load("receipt")), []
                )


if __name__ == "__main__":
    unittest.main()
