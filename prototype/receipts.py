"""Coverage-aware repair receipts.

A receipt states two different kinds of thing and must never blur them:

- **Structural evidence** — these registered descendants were enumerated and
  given a disposition, the event sequence was intact, rebuilt artifacts used
  authorised inputs.
- **Behavioural evidence** — the retired proposition did not reappear in a
  declared sample, the replacement activated, collateral facts survived.

Neither is a proof of semantic absence, and the signature is evidence about
neither: it authenticates who attested to which bytes. `limitations` is where
the receipt says what it could not see, and aggregation is where that refusal
becomes binding.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Sequence

from prototype.adapters import Coverage
from prototype.schema import load as load_schema, validate as validate_schema
from prototype.signing import VerificationKey


def receipt_acceptance_errors(value: object) -> tuple[str, ...]:
    """Return production receipt-acceptance errors, including non-vacuity."""

    if not isinstance(value, dict) or not value:
        return ("receipt is vacuous",)
    return tuple(validate_schema(value, load_schema("receipt")))


def aggregate_coverage(
    stores: Mapping[str, Coverage], triad: Mapping[str, str]
) -> Coverage:
    """Aggregate success requires every required store to be `verified`.

    The rule follows the worked example in IDEA.md, where three verified stores
    plus one unobservable prompt cache aggregate to `partial` even though every
    executed probe passed. `partial` means some relevant state was handled and
    coverage was incomplete; `unknown` is reserved for the case where nothing
    was handled at all, so that the two remain distinguishable in a receipt.

    There is deliberately no path from a set of passing probes to a verified
    aggregate while any required store is unresolved. That asymmetry is the
    point: an importer that cannot inspect a store reports what it does not
    know rather than what it hopes.
    """

    if any(result != "pass" for result in triad.values()):
        return Coverage.FAILED
    if not stores:
        return Coverage.UNKNOWN

    results = set(stores.values())
    if Coverage.FAILED in results:
        return Coverage.FAILED
    if results == {Coverage.VERIFIED}:
        return Coverage.VERIFIED
    if not (results & {Coverage.VERIFIED, Coverage.PARTIAL}):
        return Coverage.UNKNOWN
    return Coverage.PARTIAL


@dataclass(frozen=True)
class Receipt:
    importer: str
    erratum_id: str
    sequence: int
    target_root: str
    operation: str
    pre_state_root: str
    post_state_root: str
    stores: Mapping[str, Coverage]
    dispositions: Mapping[str, Mapping[str, str]]
    triad: Mapping[str, str]
    aggregate: Coverage
    limitations: Sequence[str]
    history_retained: bool
    adapter_versions: Mapping[str, str] = field(default_factory=dict)
    signature: str | None = None

    def signable(self) -> dict[str, Any]:
        return {
            "importer": self.importer,
            "erratum_id": self.erratum_id,
            "sequence": self.sequence,
            "target_root": self.target_root,
            "operation": self.operation,
            "pre_state_root": self.pre_state_root,
            "post_state_root": self.post_state_root,
            "stores": {name: value.value for name, value in self.stores.items()},
            "dispositions": {
                store: dict(items) for store, items in self.dispositions.items()
            },
            "triad": dict(self.triad),
            "aggregate": self.aggregate.value,
            "limitations": list(self.limitations),
            "history_retained": self.history_retained,
            "adapter_versions": dict(self.adapter_versions),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.signable()
        payload["signature"] = self.signature
        return payload

    def verify(self, key: VerificationKey) -> bool:
        if self.signature is None:
            return False
        return key.verify(self.signable(), self.signature)

    def with_aggregate(self, aggregate: Coverage) -> Receipt:
        """Used by tests to forge a better-looking result. The signature was
        taken over the honest value, so the forgery fails verification."""

        return replace(self, aggregate=aggregate)
