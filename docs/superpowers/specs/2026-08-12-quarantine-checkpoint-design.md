# Quarantine Checkpoint Design

**Date:** 2026-08-12

**Status:** Approved for Phase 2 implementation

## Purpose

Make the CLI's quarantine-before-repair guarantee durable and independently
inspectable. `errata quarantine` authenticates exactly the next pending erratum,
gates the complete known descendant closure across every declared retrieval
adapter, and writes an atomic checkpoint. `errata repair` refuses to mutate
state without the matching unconsumed checkpoint.

The existing `Importer.repair()` method remains the Phase 1 in-process atomic
composition. The explicit checkpoint is required at the Phase 2 CLI boundary;
this change does not weaken or silently replace the in-process API.

## Checkpoint model

`prototype/checkpoints.py` owns a strict immutable `QuarantineCheckpoint` model
and its persistence. A checkpoint binds:

- schema version `1`;
- erratum ID and sequence;
- target root;
- inspectable pre-state root;
- every gated artifact grouped by adapter;
- every declared adapter, its required flag, and its coverage limitation;
- creation timestamp;
- consumed state and optional consumption timestamp; and
- a canonical SHA-256 checkpoint digest.

The digest is computed over canonical JSON with sorted object keys, compact
separators, UTF-8 encoding, and the `checkpoint_digest` field omitted. Lists
retain semantic order. The consumed fields are excluded from the identity
digest so consumption does not change which quarantine operation the
checkpoint proves; atomic persistence still protects their current value.

Checkpoint paths are deterministic:
`checkpoints/<sequence:04d>-<erratum-id>.json`. Erratum IDs are already schema
constrained; path construction additionally rejects separators and traversal.

## Quarantine command

`errata quarantine` performs one bounded operation:

1. load the signed feed and identify exactly the next sequence after the
   workspace's last applied sequence;
2. authenticate that erratum with the configured owner verification key and
   root registry;
3. reject a sequence gap, invalid target, missing lineage root, replay, or an
   existing consumed checkpoint;
4. capture the inspectable pre-state root;
5. enumerate the target's known descendant closure through each adapter;
6. gate every enumerable descendant before reporting completion;
7. record required opaque or non-enumerable stores as `unknown`, with no gated
   artifacts and an explicit limitation;
8. persist the checkpoint atomically using a same-directory temporary file,
   file flush and `fsync`, `os.replace`, and directory `fsync`; and
9. print the checkpoint path and digest.

If any enumerable retrieval adapter fails to gate its complete returned set,
the command fails closed and does not publish a successful checkpoint. State
already gated by an interrupted attempt remains gated; rerunning the command
re-authenticates the erratum and may replace only an identical unconsumed
checkpoint after the current state is reconciled against its bound pre-state.

Opaque required stores do not make quarantine appear complete. They remain
`unknown` and flow into the eventual receipt limitations.

## Repair command

`errata repair` processes exactly the next pending erratum and requires the
deterministic checkpoint path. Before rebuild it:

1. re-authenticates the signed erratum;
2. validates the checkpoint schema and recomputes its canonical digest;
3. verifies erratum ID, sequence, target root, pre-state root, adapter inventory,
   gated artifact set, coverage limitations, and unconsumed state;
4. confirms every recorded enumerable artifact is still gated and rejects
   workspace or target drift; and
5. starts rebuild only after all checks pass.

Missing, malformed, replayed, consumed, wrong-target, wrong-sequence,
wrong-pre-state, digest-mismatched, adapter-drifted, or ungated checkpoints are
refused without rebuild, receipt, or applied-sequence advancement.

Repair uses the checkpoint's already-gated artifact map and opaque-store
limitations. It does not run quarantine a second time. It runs rebuild, the
repair triad, signed attest, receipt writeback, and applied-state writeback in
that order. Only after both durable writebacks succeed is the checkpoint marked
consumed atomically. A failure before consumption retains the unconsumed
checkpoint and gated state for safe resume.

Because receipt or applied-state writeback can fail between their two durable
operations, repair reconciliation must be idempotent: an existing byte-identical
receipt is accepted, and applied state may advance only to the same target and
sequence. Contradictory durable state is refused.

## Workspace and controller boundaries

`Workspace` owns checkpoint paths and atomic file operations. `Importer` gains
focused public operations for authenticated quarantine and repair from an
already validated checkpoint. Private adapter details remain inside the
controller; CLI code orchestrates persistence, not repair semantics.

The checkpoint records adapter names, required flags, gated artifact IDs, and
limitations. An adapter added, removed, renamed, or changed from optional to
required between quarantine and repair is material drift and blocks repair.

## CLI behavior

- `errata quarantine`: exit `0` after a durable valid checkpoint; exit `1` for
  authentication, sequencing, target, gating, checkpoint, or state failure.
- `errata repair`: exit `0` only for aggregate `verified`; exit `2` for an
  honestly completed `partial` or `unknown` repair; exit `1` when checkpoint or
  repair admission fails.
- `errata pull` continues to report unapplied feed entries.
- `make cli-demo` invokes `quarantine` before `repair`.

The command never accepts a caller-supplied checkpoint path. Deterministic
workspace resolution prevents substituting evidence from another target.

## Security and recovery properties

- Signed input is authenticated both before gating and before rebuild.
- A checkpoint is target-, sequence-, state-, adapter-, and artifact-bound.
- Canonical digests detect content mutation, not filesystem metadata changes.
- Atomic replacement prevents a partially written checkpoint from authorizing
  repair.
- Consumption is last, so interrupted rebuild or writeback remains resumable.
- Replay and cross-target substitution fail closed.
- Opaque coverage never becomes verified.
- Checkpoints contain artifact identifiers and commitments, not erased values.

This remains a reference implementation. Production deployment still requires
audited constant-time cryptography, hardened filesystem ownership and locking,
operator authentication, and independent review.

## Test contract

Strict TDD covers:

- exactly-next authenticated erratum selection;
- complete descendant gating before checkpoint persistence;
- deterministic canonical digest and atomic round trip;
- opaque required adapter recorded as `unknown`;
- missing, malformed, mutated, consumed, replayed, wrong-target,
  wrong-sequence, pre-state-drifted, adapter-drifted, and ungated checkpoint
  refusal;
- repair starting only from a matching checkpoint;
- checkpoint retained after interrupted rebuild or writeback;
- checkpoint consumed only after receipt and applied-state durability;
- correction, supersession, and erasure behavior;
- negative, positive, and preservation triad preservation; and
- CLI demo ordering.

All fixtures remain synthetic and `make check` remains offline and
standard-library-only.
