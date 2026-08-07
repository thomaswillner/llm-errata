"""Repair strategies.

`RebuildStrategy` is the conforming one. The other three are the
non-conforming repairs the repair triad exists to catch, modelled as real
strategies rather than as test hacks:

- `WipeStrategy` — delete everything instead of rebuilding. The retired
  proposition is certainly gone, and so is unrelated retained memory.
  Preservation catches it.
- `AppendOnlyStrategy` — add the replacement, leave the old value retrievable.
  The positive probe passes. Negative catches it.
- `InterruptingStrategy` — fail part-way through the rebuild, to show that an
  interrupted repair leaves state gated rather than half-served.

ROADMAP.md requires "at least one intentionally nonconforming importer" in the
Phase 3 experiment. These are the Phase 1 version of that: a conformance suite
where nothing can fail has not tested anything.
"""

from __future__ import annotations

from typing import Protocol

from prototype.errata import Erratum, Operation


class InterruptedRepair(Exception):
    """A rebuild failed part-way. Affected state stays quarantined."""


class RepairStrategy(Protocol):  # pragma: no cover - structural type
    name: str

    def apply(
        self, importer: object, erratum: Erratum, gated: dict[str, list[str]]
    ) -> None: ...


class RebuildStrategy:
    """Retire the retired root, rebuild every mixed descendant from the inputs
    that survive plus the replacement."""

    name = "rebuild"

    def apply(self, importer, erratum: Erratum, gated: dict[str, list[str]]) -> None:
        """Retire what the erratum invalidates, rebuild what merely mixed it.

        Store-agnostic on purpose. An earlier version keyed on the literal
        names "markdown" and "vector", so a third store was gated and then
        never repaired: it stayed quarantined, the positive probe failed, and
        the aggregate came back `failed` for a repair that had simply not been
        attempted. Adding a store must not require editing this file.
        """

        ledger = importer.ledger
        replacement = erratum.replacement
        # Only a supersession retains the old value, and only as scoped
        # history. `valid_from` is the instant it stopped being true.
        superseded_at = (
            erratum.valid_from if erratum.operation is Operation.SUPERSEDE else None
        )

        def source_of(adapter, item: str) -> str:
            resolve = getattr(adapter, "source_artifact", None) or getattr(
                adapter, "source_of", None
            )
            return resolve(item) if resolve else item

        # Pass one: retire everything that descends directly from the root, so
        # pass two knows which inputs are no longer valid.
        retired: set[str] = set()
        for store, items in gated.items():
            adapter = importer.adapter(store)
            for item in items:
                source = source_of(adapter, item)
                if source in ledger.artifact_ids() and ledger.artifact(source).inputs:
                    continue
                try:
                    adapter.retire(item, superseded_at=superseded_at)
                except TypeError:
                    adapter.retire(item)
                retired.add(source)

        # Pass two: rebuild the mixed artifacts from what survived.
        for store, items in gated.items():
            adapter = importer.adapter(store)
            for item in items:
                source = source_of(adapter, item)
                if source in retired:
                    continue
                adapter.rebuild(
                    item,
                    inputs=ledger.valid_inputs(source, retired=retired),
                    replacement=replacement,
                )


class WipeStrategy:
    """Non-conforming: solve the problem by destroying the profile."""

    name = "wipe"

    def apply(self, importer, erratum: Erratum, gated: dict[str, list[str]]) -> None:
        for artifact in importer.ledger.artifacts():
            if artifact.store == "markdown":
                importer.markdown.retire(artifact.artifact_id)
        for entry_id in gated.get("vector", []):
            importer.vector.retire(entry_id)


class AppendOnlyStrategy:
    """Non-conforming: append the replacement and un-gate the old value."""

    name = "append-only"

    def apply(self, importer, erratum: Erratum, gated: dict[str, list[str]]) -> None:
        for artifact_id in gated.get("markdown", []):
            importer.markdown.release(artifact_id)
            importer.markdown.mark_rebuilt(artifact_id)
        derived = [
            item
            for item in gated.get("markdown", [])
            if importer.ledger.artifact(item).inputs
        ]
        for artifact_id in derived:
            existing = importer.ledger.artifact(artifact_id).content
            importer.ledger.set_content(
                artifact_id, f"{existing}; {erratum.replacement}"
            )
        for entry_id in gated.get("vector", []):
            importer.vector.release(entry_id)
            importer.vector.mark_rebuilt(entry_id)


class InterruptingStrategy:
    """Non-conforming by accident: the process dies mid-rebuild."""

    name = "interrupt"

    def apply(self, importer, erratum: Erratum, gated: dict[str, list[str]]) -> None:
        ledger = importer.ledger
        markdown_ids = gated.get("markdown", [])
        raw = [item for item in markdown_ids if not ledger.artifact(item).inputs]
        for artifact_id in raw:
            importer.markdown.retire(artifact_id)
        derived = [item for item in markdown_ids if ledger.artifact(item).inputs]
        if derived:
            raise InterruptedRepair(
                f"rebuild of {derived[0]} failed; affected state remains quarantined"
            )
