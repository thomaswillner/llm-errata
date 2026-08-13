"""The errata feed is the trust boundary. Everything downstream assumes an
erratum that reached the controller was authorised, in order, and unambiguous.

These tests are written against the invariants in IDEA.md: "Importers reject
invalid signatures, rollback, sequence gaps, conflicting events, and ambiguous
targets."
"""

from __future__ import annotations

import unittest

from prototype.errata import (
    Erratum,
    FeedError,
    Operation,
    OwnerKeySchedule,
    RootRegistry,
    read_feed,
    verify_feed,
)
from prototype.signing import DemoSigner


OWNER = DemoSigner(b"owner-secret")
IMPOSTOR = DemoSigner(b"not-the-owner")
OWNER_V1 = DemoSigner(b"owner-v1", key_id="owner-v1")
OWNER_V2 = DemoSigner(b"owner-v2", key_id="owner-v2")

ROOTS = RootRegistry({"mem_01HX", "mem_02KP"})


def erratum(sequence: int, **overrides: object) -> Erratum:
    fields: dict[str, object] = {
        "erratum_id": f"err_{sequence:04d}",
        "sequence": sequence,
        "target_root": "mem_01HX",
        "operation": Operation.SUPERSEDE,
        "valid_from": "2026-08-01T00:00:00Z",
        "replacement": "eats meat again",
        "postconditions": {
            "negative": "no vegetarian-only assumption",
            "positive": "current diet uses the replacement",
            "preserve": "quiet restaurants and budget remain active",
        },
    }
    fields.update(overrides)
    return Erratum(**fields)  # type: ignore[arg-type]


class FeedAcceptsWellFormedEvents(unittest.TestCase):
    def test_a_signed_sequential_feed_verifies(self) -> None:
        signed = [OWNER.sign_erratum(erratum(n)) for n in (1, 2, 3)]
        accepted = verify_feed(signed, owner=OWNER.public, roots=ROOTS)
        self.assertEqual([item.sequence for item in accepted], [1, 2, 3])

    def test_round_trips_through_jsonl(self) -> None:
        signed = [OWNER.sign_erratum(erratum(n)) for n in (1, 2)]
        lines = "\n".join(item.to_json() for item in signed)
        self.assertEqual(
            [item.erratum_id for item in read_feed(lines)],
            ["err_0001", "err_0002"],
        )

    def test_key_rotation_uses_the_key_active_for_each_sequence(self) -> None:
        schedule = OwnerKeySchedule(((1, OWNER_V1.public), (2, OWNER_V2.public)))
        signed = [
            OWNER_V1.sign_erratum(erratum(1)),
            OWNER_V2.sign_erratum(erratum(2)),
        ]
        accepted = verify_feed(signed, owner=schedule, roots=ROOTS)
        self.assertEqual([item.signing_key_id for item in accepted], ["owner-v1", "owner-v2"])

    def test_rotated_out_key_cannot_sign_a_later_sequence(self) -> None:
        schedule = OwnerKeySchedule(((1, OWNER_V1.public), (2, OWNER_V2.public)))
        signed = [
            OWNER_V1.sign_erratum(erratum(1)),
            OWNER_V1.sign_erratum(erratum(2)),
        ]
        with self.assertRaisesRegex(FeedError, "active key"):
            verify_feed(signed, owner=schedule, roots=ROOTS)


class FeedRejectsForgeryAndReplay(unittest.TestCase):
    def test_a_forged_signature_is_rejected(self) -> None:
        signed = [OWNER.sign_erratum(erratum(1)), IMPOSTOR.sign_erratum(erratum(2))]
        with self.assertRaises(FeedError) as raised:
            verify_feed(signed, owner=OWNER.public, roots=ROOTS)
        self.assertIn("signature", str(raised.exception))

    def test_tampering_after_signing_is_rejected(self) -> None:
        signed = OWNER.sign_erratum(erratum(1))
        tampered = signed.replace(operation=Operation.ERASE)
        with self.assertRaises(FeedError) as raised:
            verify_feed([tampered], owner=OWNER.public, roots=ROOTS)
        self.assertIn("signature", str(raised.exception))

    def test_replaying_an_earlier_erratum_is_rejected_as_rollback(self) -> None:
        # The attack is resurrection: replay a genuine, correctly signed older
        # erratum so the importer reverts to a state that has since been
        # retired. The entry is identical, so this is rollback and not
        # equivocation — the two are refused for different reasons.
        signed = [OWNER.sign_erratum(erratum(n)) for n in (1, 2)]
        replayed = signed + [signed[0]]
        with self.assertRaises(FeedError) as raised:
            verify_feed(replayed, owner=OWNER.public, roots=ROOTS)
        self.assertIn("rollback", str(raised.exception))

    def test_a_new_event_at_an_older_sequence_is_rejected_as_conflict(self) -> None:
        signed = [OWNER.sign_erratum(erratum(n)) for n in (1, 2)]
        spliced = signed + [OWNER.sign_erratum(erratum(1, erratum_id="err_spliced"))]
        with self.assertRaises(FeedError) as raised:
            verify_feed(spliced, owner=OWNER.public, roots=ROOTS)
        self.assertIn("conflict", str(raised.exception))

    def test_a_sequence_gap_is_rejected(self) -> None:
        signed = [OWNER.sign_erratum(erratum(n)) for n in (1, 3)]
        with self.assertRaises(FeedError) as raised:
            verify_feed(signed, owner=OWNER.public, roots=ROOTS)
        self.assertIn("gap", str(raised.exception))

    def test_two_different_events_at_one_sequence_are_rejected(self) -> None:
        first = OWNER.sign_erratum(erratum(1))
        equivocation = OWNER.sign_erratum(erratum(1, erratum_id="err_other"))
        with self.assertRaises(FeedError) as raised:
            verify_feed([first, equivocation], owner=OWNER.public, roots=ROOTS)
        self.assertIn("conflict", str(raised.exception))

    def test_same_id_with_different_signed_content_is_also_a_conflict(self) -> None:
        first = OWNER.sign_erratum(erratum(1, erratum_id="err_same"))
        second = OWNER.sign_erratum(
            erratum(1, erratum_id="err_same", replacement="different state")
        )
        with self.assertRaisesRegex(FeedError, "conflict"):
            verify_feed([first, second], owner=OWNER.public, roots=ROOTS)


class FeedRejectsAmbiguousOrIllFormedTargets(unittest.TestCase):
    def test_an_unregistered_target_root_is_rejected(self) -> None:
        signed = [OWNER.sign_erratum(erratum(1, target_root="mem_unknown"))]
        with self.assertRaises(FeedError) as raised:
            verify_feed(signed, owner=OWNER.public, roots=ROOTS)
        self.assertIn("target", str(raised.exception))

    def test_supersession_without_a_replacement_is_rejected(self) -> None:
        signed = [OWNER.sign_erratum(erratum(1, replacement=None))]
        with self.assertRaises(FeedError) as raised:
            verify_feed(signed, owner=OWNER.public, roots=ROOTS)
        self.assertIn("replacement", str(raised.exception))

    def test_erasure_carrying_a_replacement_is_rejected(self) -> None:
        # Erasure has no positive replacement. Accepting one would let an
        # erasure smuggle content back in under a different operation.
        signed = [
            OWNER.sign_erratum(
                erratum(1, operation=Operation.ERASE, replacement="something")
            )
        ]
        with self.assertRaises(FeedError) as raised:
            verify_feed(signed, owner=OWNER.public, roots=ROOTS)
        self.assertIn("replacement", str(raised.exception))

    def test_erasure_needs_no_positive_postcondition(self) -> None:
        signed = [
            OWNER.sign_erratum(
                erratum(
                    1,
                    operation=Operation.ERASE,
                    replacement=None,
                    postconditions={
                        "negative": "the value never surfaces",
                        "preserve": "unrelated preferences still work",
                    },
                )
            )
        ]
        accepted = verify_feed(signed, owner=OWNER.public, roots=ROOTS)
        self.assertEqual(accepted[0].operation, Operation.ERASE)

    def test_correction_and_supersession_stay_distinct(self) -> None:
        # AGENTS.md forbids collapsing these. The feed carries the distinction
        # rather than inferring it from the presence of a validity interval.
        correction = OWNER.sign_erratum(erratum(1, operation=Operation.CORRECT))
        supersession = OWNER.sign_erratum(erratum(2, operation=Operation.SUPERSEDE))
        accepted = verify_feed(
            [correction, supersession], owner=OWNER.public, roots=ROOTS
        )
        self.assertEqual(
            [item.operation for item in accepted],
            [Operation.CORRECT, Operation.SUPERSEDE],
        )


if __name__ == "__main__":
    unittest.main()
