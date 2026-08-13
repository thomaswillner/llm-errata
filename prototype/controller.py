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
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Sequence

from prototype.adapters import CannotEnumerate, Coverage, StoreAdapter
from prototype.checkpoints import (
    AdapterCheckpoint,
    CheckpointError,
    QuarantineCheckpoint,
)
from prototype.errata import (
    Erratum,
    FeedError,
    Operation,
    RootRegistry,
    event_fingerprint,
    verify_feed,
)
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
        adapters: Sequence[StoreAdapter],
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
        self._observed_sequences: dict[int, tuple[str, str]] = {}

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
        fingerprint = event_fingerprint(erratum)
        prior = self._observed_sequences.get(erratum.sequence)
        if prior is not None and prior[1] != fingerprint:
            self.journal.append(
                JournalEvent(Phase.REFUSED, {"erratum": erratum.erratum_id})
            )
            raise FeedError(
                f"sequence {erratum.sequence} conflict in this importer view: "
                f"{prior[0]!r} and {erratum.erratum_id!r} carry different signed events"
            )
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
        self._observed_sequences.setdefault(
            erratum.sequence, (erratum.erratum_id, fingerprint)
        )
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
        checkpoint = self.quarantine(erratum)
        if resume:
            self.journal.append(
                JournalEvent(Phase.OBSERVE, {"resumed": erratum.erratum_id})
            )
        return self.repair_quarantined(erratum, checkpoint)

    def quarantine(self, erratum: Erratum) -> QuarantineCheckpoint:
        """Authenticate and gate one erratum without beginning its rebuild."""

        validated = self.observe(erratum)
        pre_state_root = self.state_root()
        root = validated.target_root
        gated, checkpoint_coverage, coverage_limitations = self._quarantine(root)
        records = []
        for adapter in sorted(self.adapters, key=lambda item: item.name):
            limitation = coverage_limitations.get(adapter.name)
            records.append(
                AdapterCheckpoint(
                    name=adapter.name,
                    required=bool(getattr(adapter, "required", True)),
                    artifact_ids=tuple(sorted(gated[adapter.name])),
                    coverage=checkpoint_coverage[adapter.name].value,
                    limitation=limitation,
                )
            )
        return QuarantineCheckpoint.create(
            erratum_id=validated.erratum_id,
            sequence=validated.sequence,
            target_root=root,
            pre_state_root=pre_state_root,
            adapters=tuple(records),
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )

    def repair_quarantined(
        self, erratum: Erratum, checkpoint: QuarantineCheckpoint
    ) -> Receipt:
        """Re-authenticate and repair only state proven gated by a checkpoint."""

        validated = self.observe(erratum)
        self._validate_checkpoint(validated, checkpoint)

        root = validated.target_root
        gated = {
            record.name: list(record.artifact_ids) for record in checkpoint.adapters
        }
        coverage_limitations = {
            record.name: record.limitation
            for record in checkpoint.adapters
            if record.limitation is not None
        }
        checkpoint_coverage = {
            record.name: Coverage(record.coverage)
            for record in checkpoint.adapters
        }

        self.journal.append(JournalEvent(Phase.REBUILD_BEGIN, {"root": root}))
        self.strategy.apply(self, validated, gated)
        self.journal.append(JournalEvent(Phase.REBUILD_COMPLETE, {"root": root}))

        triad = self._run_triad(validated)
        self.journal.append(JournalEvent(Phase.TEST, dict(triad)))

        receipt = self._attest(
            validated,
            checkpoint.pre_state_root,
            checkpoint_coverage,
            coverage_limitations,
            triad,
        )
        self.last_sequence = validated.sequence
        self._applied[root] = validated.sequence
        self.journal.append(
            JournalEvent(Phase.ATTEST, {"aggregate": receipt.aggregate.value})
        )
        return receipt

    def _validate_checkpoint(
        self, erratum: Erratum, checkpoint: QuarantineCheckpoint
    ) -> None:
        if checkpoint.consumed:
            raise CheckpointError("checkpoint is already consumed")
        if (
            checkpoint.erratum_id != erratum.erratum_id
            or checkpoint.sequence != erratum.sequence
            or checkpoint.target_root != erratum.target_root
        ):
            raise CheckpointError("checkpoint erratum binding does not match")
        if checkpoint.pre_state_root != self.state_root():
            raise CheckpointError("checkpoint pre-state root does not match current state")

        records = {record.name: record for record in checkpoint.adapters}
        adapters = {adapter.name: adapter for adapter in self.adapters}
        if set(records) != set(adapters):
            raise CheckpointError("checkpoint adapter inventory has drifted")
        for name, adapter in adapters.items():
            record = records[name]
            if record.required != bool(getattr(adapter, "required", True)):
                raise CheckpointError(f"checkpoint adapter requirement drifted: {name}")
            try:
                current = tuple(sorted(adapter.enumerate(erratum.target_root)))
            except CannotEnumerate:
                if (
                    record.artifact_ids
                    or record.coverage != "unknown"
                    or record.limitation != self._opaque_limitation(name)
                ):
                    raise CheckpointError(f"checkpoint opaque coverage drifted: {name}")
                continue
            current_limitation = self._lineage_limitation(adapter, erratum.target_root)
            expected_coverage, current_limitation = self._checkpoint_coverage(
                adapter, erratum.target_root, current_limitation
            )
            if (
                record.coverage != expected_coverage.value
                or record.limitation != current_limitation
            ):
                raise CheckpointError(f"checkpoint adapter coverage drifted: {name}")
            if record.artifact_ids != current:
                raise CheckpointError(f"checkpoint gated artifact set drifted: {name}")
            if not all(adapter.is_quarantined(item) for item in current):
                raise CheckpointError(f"checkpoint artifact is no longer gated: {name}")

    @staticmethod
    def _opaque_limitation(name: str) -> str:
        return (
            f"{name}: store exposes no enumeration interface, so its coverage "
            "is unknown and no repair elsewhere changes that"
        )

    @staticmethod
    def _lineage_limitation(adapter: StoreAdapter, root: str) -> str | None:
        """Return a binding limitation unless root-specific lineage is audited.

        Successful enumeration is not itself evidence that the enumeration
        source was complete. An adapter must explicitly bind its walk to a
        write-time or otherwise audited lineage authority. The method remains
        an adapter attestation, not proof against a dishonest adapter.
        """

        audit = getattr(adapter, "lineage_complete", None)
        try:
            complete = audit(root) is True if audit is not None else False
        except Exception:
            complete = False
        snapshot = getattr(adapter, "snapshot", None)
        if complete and callable(snapshot):
            return None
        if complete:
            return (
                f"{adapter.name}: adapter exposes no state snapshot for {root}; "
                "checkpoint and receipt state roots cannot bind its mutations"
            )
        return (
            f"{adapter.name}: enumeration returned a result but the adapter did "
            f"not establish complete root-specific lineage for {root}; empty or "
            "partial walks cannot become verified coverage"
        )

    @staticmethod
    def _feed_view_limitation() -> str:
        return (
            "receipt authenticates this importer's accepted feed view only; "
            "importer-local sequencing cannot establish global owner "
            "non-equivocation without an external witnessed or append-only log"
        )

    @staticmethod
    def _checkpoint_coverage(
        adapter: StoreAdapter, root: str, limitation: str | None
    ) -> tuple[Coverage, str | None]:
        """Read quarantine-phase coverage without inventing success.

        This is deliberately distinct from ``coverage(root)``, which evaluates
        final repair dispositions. Missing, raising, or malformed checkpoint
        evidence becomes ``unknown`` and is bound into the durable record.
        """

        report = getattr(adapter, "quarantine_coverage", None)
        try:
            result = report(root) if report is not None else Coverage.UNKNOWN
        except Exception:
            result = Coverage.UNKNOWN
        if not isinstance(result, Coverage):
            result = Coverage.UNKNOWN
        if report is None or result is Coverage.UNKNOWN:
            limitation = limitation or (
                f"{adapter.name}: adapter did not establish quarantine-phase "
                f"coverage for {root}"
            )
        if limitation is not None and result is Coverage.VERIFIED:
            result = Coverage.UNKNOWN
        return result, limitation

    def _quarantine(
        self, root: str
    ) -> tuple[dict[str, list[str]], dict[str, Coverage], dict[str, str]]:
        """Gate every known descendant everywhere, before any rebuild starts."""

        self.journal.append(JournalEvent(Phase.QUARANTINE_BEGIN, {"root": root}))
        gated: dict[str, list[str]] = {}
        checkpoint_coverage: dict[str, Coverage] = {}
        limitations: dict[str, str] = {}
        for adapter in self.adapters:
            try:
                descendants = adapter.enumerate(root)
            except CannotEnumerate:
                acknowledge = getattr(adapter, "acknowledge", None)
                if acknowledge is not None:
                    acknowledge(root)
                limitations[adapter.name] = self._opaque_limitation(adapter.name)
                gated[adapter.name] = []
                checkpoint_coverage[adapter.name] = Coverage.UNKNOWN
                continue
            lineage_limitation = self._lineage_limitation(adapter, root)
            adapter.quarantine(descendants)
            gated[adapter.name] = list(descendants)
            reported, limitation = self._checkpoint_coverage(
                adapter, root, lineage_limitation
            )
            checkpoint_coverage[adapter.name] = reported
            if limitation is not None:
                limitations[adapter.name] = limitation
        self.journal.append(JournalEvent(Phase.QUARANTINE_COMPLETE, gated))
        return gated, checkpoint_coverage, limitations

    def _attest(
        self,
        erratum: Erratum,
        pre_state_root: str,
        checkpoint_coverage: dict[str, Coverage],
        coverage_limitations: dict[str, str],
        triad: dict[str, str],
    ) -> Receipt:
        root = erratum.target_root
        # IDEA.md: "A store absent from the root's required scope is omitted
        # rather than congratulated as 'not applicable.'" Omission is the only
        # honest way to leave a store out; there is no `not-applicable` result,
        # because there is no way to distinguish it from an unchecked one.
        stores = {}
        for adapter in self.adapters:
            if not getattr(adapter, "required", True):
                continue
            reported = adapter.coverage(root)
            stores[adapter.name] = self._conservative_coverage(
                checkpoint_coverage[adapter.name], reported
            )
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
                *sorted(coverage_limitations.values()),
                self._feed_view_limitation(),
            ],
            history_retained=erratum.operation is Operation.SUPERSEDE,
            adapter_versions={adapter.name: "0.1.0" for adapter in self.adapters},
        )
        return replace(receipt, signature=self.signer.sign(receipt.signable()))

    @staticmethod
    def _conservative_coverage(
        checkpoint: Coverage, final: Coverage
    ) -> Coverage:
        """Final repair cannot erase an earlier coverage failure or limitation."""

        if Coverage.FAILED in {checkpoint, final}:
            return Coverage.FAILED
        rank = {
            Coverage.VERIFIED: 0,
            Coverage.PARTIAL: 1,
            Coverage.UNKNOWN: 2,
        }
        return max((checkpoint, final), key=rank.__getitem__)

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
