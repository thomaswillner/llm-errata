"""The Phase 1 demo, runnable from a clean checkout.

    python3 -m prototype.demo

No network, no API key, no dependencies. It exits non-zero, on purpose: the
repair succeeds everywhere it can be observed, and the aggregate result is
still not `verified`, because one required store cannot show its work.

That failure is the deliverable. A demo where everything passes proves only
that the demo was designed to pass.
"""

from __future__ import annotations

import sys

from prototype.adapters import Coverage
from prototype.controller import Phase
from prototype.errata import Erratum, Operation
from prototype.receipts import Receipt
from prototype.scenario import DIET, build_importer
from prototype.signing import DemoSigner


OWNER = DemoSigner(b"owner-secret")

RULE = "─" * 72


def heading(text: str) -> None:
    print(f"\n{text}\n{RULE}")


def supersession() -> Erratum:
    return OWNER.sign_erratum(
        Erratum(
            erratum_id="err_01JZ",
            sequence=1,
            target_root=DIET,
            operation=Operation.SUPERSEDE,
            valid_from="2026-08-01T00:00:00Z",
            replacement="eats meat again",
            postconditions={
                "negative": "vegetarian",
                "positive": "eats meat again",
                "preserve": "quiet restaurants|moderate budget",
            },
        )
    )


def show_recall(importer, label: str) -> None:
    print(f"  {label}")
    for adapter in importer.adapters:
        recall = getattr(adapter, "recall", None)
        if recall is None:
            continue
        hits = recall("vegetarian")
        rendered = ", ".join(hit.artifact_id for hit in hits) if hits else "(nothing)"
        print(f"    {adapter.name:<14} {rendered}")


def show_receipt(receipt: Receipt) -> None:
    print(f"  erratum          {receipt.erratum_id}  sequence {receipt.sequence}")
    print(f"  operation        {receipt.operation}")
    print(f"  pre-state root   {receipt.pre_state_root}")
    print(f"  post-state root  {receipt.post_state_root}")
    print("  stores")
    for name, coverage in receipt.stores.items():
        print(f"    {name:<14} {coverage.value}")
    print("  repair triad")
    for leg, result in receipt.triad.items():
        print(f"    {leg:<14} {result}")
    print(f"  aggregate        {receipt.aggregate.value.upper()}")
    for limitation in receipt.limitations:
        print(f"  limitation       {limitation}")


def main() -> int:
    importer = build_importer(OWNER)
    erratum = supersession()

    heading("1. Before the erratum")
    print("  One root, 'is vegetarian', copied into three stores and mixed into a")
    print("  summary alongside two unrelated preferences.")
    show_recall(importer, "recall('vegetarian') returns:")

    heading("2. Repair")
    receipt = importer.repair(erratum)
    for event in importer.journal:
        detail = ""
        if event.phase is Phase.QUARANTINE_COMPLETE:
            detail = "  ".join(
                f"{store}={len(items)}" for store, items in event.detail.items()
            )
        elif event.phase is Phase.TEST:
            detail = "  ".join(f"{k}={v}" for k, v in event.detail.items())
        print(f"  {event.phase.value:<20} {detail}".rstrip())
    print()
    print("  Quarantine completes before the first rebuild begins. That ordering is")
    print("  why an interrupted repair fails closed instead of serving half-repaired")
    print("  state.")

    heading("3. After the erratum")
    show_recall(importer, "recall('vegetarian') returns:")
    print(f"  rebuilt summary  {importer.markdown.content('summary:dining')}")
    print("  The summary was rebuilt from the two retained inputs plus the")
    print("  replacement. It was not deleted, and the replacement was not appended")
    print("  to the old text.")

    heading("4. Receipt")
    show_receipt(receipt)

    heading("Result")
    if receipt.aggregate is Coverage.VERIFIED:
        print("  UNEXPECTED: the aggregate is verified.")
        print("  Every required store reported verified coverage, which should be")
        print("  impossible while the opaque store is in scope. Investigate before")
        print("  trusting any other result from this run.")
        return 1

    print(f"  Aggregate is {receipt.aggregate.value.upper()}, not VERIFIED.")
    print()
    print("  Both inspectable stores were fully repaired and all three probes")
    print("  passed. One required store exposes no interface adequate to show its")
    print("  own state, so this importer reports what it does not know.")
    print()
    print("  This is the behaviour the proposal is actually asking vendors to")
    print("  adopt, and it is the reason it is a hard sell: coverage honesty is a")
    print("  machine for generating 'we cannot verify this' about your own product.")
    print()
    print("  Exit code 2: the repair is incomplete, and saying so is the point.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
