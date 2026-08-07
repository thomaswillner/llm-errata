"""The Phase 1 fixture: one root copied into three stores.

Deliberately the smallest arrangement that can fail in each of the ways the
proposal cares about:

- `fact:diet` is the root under erratum.
- `fact:venue` and `fact:budget` are retained memory that must survive.
- `summary:dining` mixes all three, so a repair that deletes it destroys
  retained memory and a repair that leaves it destroys the correction.
- `vec:diet` descends from the root alone and must be retired.
- `vec:dining` descends from the mixed summary and must be rebuilt.
- `vec:pet` is unrelated and must be untouched.
- `prompt_cache` is opaque and can only ever report unknown.

All fixture data is synthetic. AGENTS.md forbids real personal, customer,
employer, or credential material in fixtures.
"""

from __future__ import annotations

from prototype.adapters import MarkdownAdapter, OpaqueAdapter, VectorAdapter
from prototype.controller import Importer
from prototype.errata import RootRegistry
from prototype.lineage import LineageLedger
from prototype.signing import DemoSigner, Signer
from prototype.strategies import RepairStrategy


DIET = "mem_01HX"
VENUE = "mem_02KP"
BUDGET = "mem_03RS"
PET = "mem_09ZZ"

IMPORTER_SECRET = b"importer-secret"


def build_ledger() -> LineageLedger:
    ledger = LineageLedger()
    ledger.register_import(
        DIET, "fact:diet", store="markdown", content="is vegetarian"
    )
    ledger.register_import(
        VENUE, "fact:venue", store="markdown", content="prefers quiet restaurants"
    )
    ledger.register_import(
        BUDGET, "fact:budget", store="markdown", content="moderate budget"
    )
    ledger.register_import(PET, "fact:pet", store="markdown", content="has a cat")
    ledger.register_derivation(
        "summary:dining",
        store="markdown",
        inputs=("fact:diet", "fact:venue", "fact:budget"),
        content="is vegetarian; prefers quiet restaurants; moderate budget",
    )
    return ledger


def build_importer(
    owner: Signer,
    *,
    strategy: RepairStrategy | None = None,
    include_opaque: bool = True,
) -> Importer:
    ledger = build_ledger()
    markdown = MarkdownAdapter(ledger)
    vector = VectorAdapter(ledger)
    vector.index("vec:diet", source="fact:diet", text="is vegetarian")
    vector.index(
        "vec:dining",
        source="summary:dining",
        text="is vegetarian; prefers quiet restaurants; moderate budget",
    )
    vector.index("vec:pet", source="fact:pet", text="has a cat")

    adapters: list[object] = [markdown, vector]
    if include_opaque:
        adapters.append(OpaqueAdapter(name="prompt_cache"))

    return Importer(
        "travel-planner",
        ledger=ledger,
        adapters=adapters,
        signer=DemoSigner(IMPORTER_SECRET),
        owner=owner.public,
        roots=RootRegistry({DIET, VENUE, BUDGET, PET}),
        strategy=strategy,
    )
