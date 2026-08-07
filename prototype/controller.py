"""The importer: observe, quarantine, rebuild, test, attest.

The ordering is the contract. Quarantine is fast and happens first, across
every declared retrieval gate, before any slow rebuild work starts. If a
rebuild then fails, the affected state is already gated, so an interrupted
repair fails closed rather than serving a half-repaired profile.

The journal records that ordering as observable events, because "we quarantine
before we repair" is otherwise an assertion about code that nobody outside the
repository can check.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Sequence

from prototype.adapters import CannotEnumerate
from prototype.errata import Erratum, FeedError, Operation, RootRegistry, verify_feed
from prototype.lineage import LineageLedger
from prototype.receipts import Receipt, aggregate_coverage
from prototype.signing import Signer, VerificationKey, commitment
from prototype.strategies import InterruptedRepair, RebuildStrategy, RepairStrategy


class Phase(str, Enum):
    OBSERVE = "observe"
    QUARANTINE_BEGIN = "quarantine-begin"
    QUARANTINE_COMPLETE = "quarantine-complete"
    REBUILD_BEGIN = "rebuild-begin"
    REBUILD_COMPLETE = "rebuild-complete"
    TEST = "test"
    ATTEST = "attest"
    REFUSED = "refused"


@dataclass(frozen=True)
class JournalEvent:
    phase: Phase
    detail: dict[str, Any] = field(default_factory=dict)


class Importer:
    def __init__(
        self,
        name: str,
        *,
        ledger: LineageLedger,
        adapters: Sequence[Any],
        signer: Signer,
        owner: VerificationKey,
        roots: RootRegistry,
        strategy: RepairStrategy | None = None,
    ) -> None:
        self.name = name
        self.ledger = ledger
        self.adapters = list(adapters)
        self.signer = signer
        self.owner = owner
        self.roots = roots
        self.strategy: RepairStrategy = strategy or RebuildStrategy()
        self.journal: list[JournalEvent] = []
        self.last_sequence = 0
        self._applied: dict[str, int] = {}

    # -- accessors -----------------------------------------------------

    @property
    def markdown(self) -> Any:
        return self.adapter("markdown")

    @property
    def vector(self) -> Any:
        return self.adapter("vector")

    def adapter(self, name: str) -> Any:
        for adapter in self.adapters:
            if adapter.name == name:
                return adapter
        raise KeyError(name)

    def use_strategy(self, strategy: RepairStrategy) -> None:
        self.strategy = strategy

    def state_root(self) -> str:
        """A deterministic commitment over everything this importer can see.

        Stores that cannot be enumerated contribute nothing, which is itself
        honest: the state root covers the inspectable boundary and no more, and
        the receipt says so in `limitations`.
        """

        parts = [
            f"{artifact.artifact_id}={artifact.content}"
            for artifact in sorted(
                self.ledger.artifacts(), key=lambda item: item.artifact_id
            )
        ]
        for adapter in self.adapters:
            snapshot = getattr(adapter, "snapshot", None)
            if snapshot is None:
                continue
            for key, value in sorted(snapshot().items()):
                parts.append(f"{adapter.name}:{key}={value}")
        return commitment(*parts)

    # -- the loop ------------------------------------------------------

    def observe(self, erratum: Erratum) -> Erratum:
        try:
            accepted = verify_feed(
                [erratum],
                owner=self.owner,
                roots=self.roots,
                last_sequence=self.last_sequence,
            )
        except FeedError:
            self.journal.append(
                JournalEvent(Phase.REFUSED, {"erratum": erratum.erratum_id})
            )
            raise
        self.journal.append(
            JournalEvent(
                Phase.OBSERVE,
                {"erratum": erratum.erratum_id, "sequence": erratum.sequence},
            )
        )
        return accepted[0]

    def repair(self, erratum: Erratum, *, resume: bool = False) -> Receipt:
        # `resume` records that this is a second attempt. It does NOT relax
        # authentication: an interrupted repair is a reason to re-check the
        # input, not to trust it. An earlier version skipped `observe` on
        # resume, which let an unsigned erratum from anyone produce a signed
        # receipt. The sequence check still passes on a genuine resume because
        # an interrupted attempt never reached attest, so `last_sequence` did
        # not advance.
        validated = self.observe(erratum)
        if resume:
            self.journal.append(
                JournalEvent(Phase.OBSERVE, {"resumed": erratum.erratum_id})
            )

        pre_state_root = self.state_root()
        root = validated.target_root

        gated, unenumerable = self._quarantine(root)

        self.journal.append(JournalEvent(Phase.REBUILD_BEGIN, {"root": root}))
        self.strategy.apply(self, validated, gated)
        self.journal.append(JournalEvent(Phase.REBUILD_COMPLETE, {"root": root}))

        triad = self._run_triad(validated)
        self.journal.append(JournalEvent(Phase.TEST, dict(triad)))

        receipt = self._attest(validated, pre_state_root, unenumerable, triad)
        self.last_sequence = validated.sequence
        self._applied[root] = validated.sequence
        self.journal.append(
            JournalEvent(Phase.ATTEST, {"aggregate": receipt.aggregate.value})
        )
        return receipt

    def _quarantine(self, root: str) -> tuple[dict[str, list[str]], list[str]]:
        """Gate every known descendant everywhere, before any rebuild starts."""

        self.journal.append(JournalEvent(Phase.QUARANTINE_BEGIN, {"root": root}))
        gated: dict[str, list[str]] = {}
        unenumerable: list[str] = []
        for adapter in self.adapters:
            try:
                descendants = adapter.enumerate(root)
            except CannotEnumerate:
                acknowledge = getattr(adapter, "acknowledge", None)
                if acknowledge is not None:
                    acknowledge(root)
                unenumerable.append(adapter.name)
                gated[adapter.name] = []
                continue
            adapter.quarantine(descendants)
            gated[adapter.name] = list(descendants)
        self.journal.append(JournalEvent(Phase.QUARANTINE_COMPLETE, gated))
        return gated, unenumerable

    def _attest(
        self,
        erratum: Erratum,
        pre_state_root: str,
        unenumerable: Sequence[str],
        triad: dict[str, str],
    ) -> Receipt:
        root = erratum.target_root
        # IDEA.md: "A store absent from the root's required scope is omitted
        # rather than congratulated as 'not applicable.'" Omission is the only
        # honest way to leave a store out; there is no `not-applicable` result,
        # because there is no way to distinguish it from an unchecked one.
        stores = {
            adapter.name: adapter.coverage(root)
            for adapter in self.adapters
            if getattr(adapter, "required", True)
        }
        receipt = Receipt(
            importer=self.name,
            erratum_id=erratum.erratum_id,
            sequence=erratum.sequence,
            target_root=root,
            operation=erratum.operation.value,
            pre_state_root=pre_state_root,
            post_state_root=self.state_root(),
            stores=stores,
            dispositions={
                adapter.name: adapter.dispositions(root) for adapter in self.adapters
            },
            triad=triad,
            aggregate=aggregate_coverage(stores, triad),
            limitations=[
                f"{name}: store exposes no enumeration interface, so its coverage "
                "is unknown and no repair elsewhere changes that"
                for name in unenumerable
            ],
            history_retained=erratum.operation is Operation.SUPERSEDE,
            adapter_versions={adapter.name: "0.1.0" for adapter in self.adapters},
        )
        return replace(receipt, signature=self.signer.sign(receipt.signable()))

    # -- probes --------------------------------------------------------

    def _run_triad(self, erratum: Erratum) -> dict[str, str]:
        """Negative, positive when applicable, and preservation.

        These are behavioural probes over a declared scope. They are evidence
        that the retired proposition did not surface in this sample, not proof
        that it can never surface again.
        """

        conditions = erratum.postconditions
        results: dict[str, str] = {}

        results["negative"] = "pass" if not self._recalls(conditions["negative"]) else "fail"

        if erratum.operation is not Operation.ERASE:
            results["positive"] = (
                "pass" if self._recalls(conditions["positive"]) else "fail"
            )

        results["preserve"] = (
            "pass"
            if all(self._recalls(term) for term in conditions["preserve"].split("|"))
            else "fail"
        )
        return results

    def _recalls(self, term: str) -> bool:
        for adapter in self.adapters:
            recall = getattr(adapter, "recall", None)
            if recall is None:
                continue
            for hit in recall(term):
                if term.lower() in hit.content.lower():
                    return True
        return False

    # -- stale reimport ------------------------------------------------

    def reimport(self, root: str, *, content: str, sequence: int) -> bool:
        """Accept a re-export of `root` only if it is at least as new as the
        last erratum this importer applied to it.

        Without this the whole repair is undone by the next sync: a stale
        export carries the retired proposition back in, and nothing notices,
        because an import looks like an import.
        """

        applied = self._applied.get(root)
        # `<=`, not `<`. The erratum at `applied` is the one that retired the
        # proposition, so an export stamped with that same sequence predates
        # the repair and carries the retired value back in.
        if applied is not None and sequence <= applied:
            self.journal.append(
                JournalEvent(
                    Phase.REFUSED,
                    {
                        "reimport": root,
                        "offered_sequence": sequence,
                        "applied_sequence": applied,
                        "reason": "stale export would restore a retired proposition",
                    },
                )
            )
            return False
        self.ledger.register_import(
            root, f"fact:reimport:{sequence}", store="markdown", content=content
        )
        return True


__all__ = ["Importer", "InterruptedRepair", "JournalEvent", "Phase"]
