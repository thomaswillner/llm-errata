# Threat Model

What this design defends against, what it does not, and which failures it can
only make visible rather than prevent.

The distinction that runs through the whole document: a signature establishes
**who attested to which bytes**. It establishes nothing about whether the
attestation is true. Everything downstream of that sentence is either a
mitigation or an admitted limit.

## Actors

| Actor | Holds | Trusted for |
|---|---|---|
| Owner | The signing key for a memory root | Issuing errata. Nothing else. |
| Importer | Local derived state, and its own signing key | Repairing what it can see, and reporting what it cannot |
| Store | Some part of the importer's state | Nothing. A store's own report is evidence about the store's API, not about its substrate |
| Relying party | Published verification keys | Deciding what a receipt is worth |

## Defended

| Threat | Mitigation | Where |
|---|---|---|
| Forged erratum | Ed25519 over a canonical serialisation; the feed is refused, not the entry | `errata.verify_feed` |
| Tampering after signing | The signature covers every semantic field; `signature` is excluded from its own preimage | `Erratum.signable` |
| Replay of a retired state | Monotonic sequence; a lower sequence is a rollback and refused | `errata.verify_feed` |
| Same-view conflict or splice | Different signed event content at one sequence is remembered and refused when one importer sees it, including across separate observe calls | `errata.verify_feed`, `Importer.observe` |
| Suppressed erratum | A sequence gap is refused: the missing entry may be the one retiring the state about to be served | `errata.verify_feed` |
| Erasure smuggling content back | An erasure carrying a replacement is refused | `errata._check_shape` |
| Signature malleability | Non-canonical scalars (`S >= L`) rejected, so a receipt cannot be altered and still verify | `ed25519.verify` |
| Repair that destroys retained memory | Preservation probe | `controller._run_triad` |
| Repair that adds the new value and keeps serving the old | Negative probe | `controller._run_triad` |
| Half-repaired state being served | Quarantine completes before any rebuild; an interrupted repair leaves state gated | `controller.repair` |
| Stale export undoing a repair | A re-import at or below the applied sequence is refused | `controller.reimport` |
| Resuming as an authentication bypass | `resume` re-runs `observe`; it relaxes nothing | `controller.repair` |
| Silent partial coverage | A required store that is not `verified` prevents aggregate success | `receipts.aggregate_coverage` |
| Empty walk presented as complete | Enumeration without explicit root-specific lineage-completeness evidence is signed as `unknown`, even when the adapter returns zero artifacts or claims `verified` | `controller._lineage_limitation`, `controller._attest` |
| Erased value surviving in evidence | Receipts carry no digest of erased content; low-entropy propositions cannot be safely committed to, so nothing is committed | `signing.commitment` |

## Not defended, and why

**Owner split-view equivocation.** Two importers can receive different,
correctly signed events at the same sequence and each can hold a locally
monotone, gap-free feed. No importer can detect an event it never received.
Every receipt therefore states that it authenticates only that importer's
accepted feed view. Establishing global owner non-equivocation requires an
external witness, gossip protocol, or append-only transparency log; none is
implemented by this repository.

**A lying importer.** An importer that signs `verified` over a repair it never
performed produces a receipt that verifies. Nothing in this design detects it.
The signature identifies who to disbelieve, which is the whole of what it
offers. Mitigations are outside the contract: owner-issued spot probes, an
independent verifier, or a transparency log that makes a false claim durable
and attributable.

**A store whose substrate contradicts its API.**
[Ghost Vectors](https://arxiv.org/abs/2606.18497v1) demonstrates that
soft-deleted embeddings remain reconstructible from HNSW index files in
ChromaDB, FAISS and Weaviate after the API reports the record gone. An adapter
that reports `verified` on the strength of a delete response is honest and
wrong. This is the sharpest open problem in the design: **coverage honesty
still has no independent adversary**, and an adapter is trusted to characterise
itself. The controller now refuses to infer lineage completeness from an empty
enumeration, but a dishonest adapter can still falsely attest that its
root-specific lineage authority is complete.

**Unregistered copies.** The closure is *known* because lineage is written at
derivation time. Prose copied by a human, a screenshot, a backup, a provider
log, a model's weights: all permanently outside it. `unknown` is the correct
report and it is not a formality.

**Semantic re-derivation.** A retired proposition may be reconstructible from
what was legitimately retained.
[Reclaim Evaluation](https://arxiv.org/abs/2606.25449) shows the converse
failure too: a summary that kept a conclusion and dropped its source is not
merely hard to correct but measured at 0.00 recovery across every model tested.
Under this proposal's own definitions that is `failed`, not `partial`.

**Probe identifiability.** Anytime-valid statistics can bound the error rate of
whatever is measured. Nothing established says the measured quantity moves if
and only if a repair happened. See `HARD_PROBLEMS.md`.

**Traffic analysis and metadata.** Polling an errata endpoint reveals that an
importer holds a root. Payloads may be encrypted per importer; the fact of the
subscription is harder to hide.

**Key compromise and rotation.** Not implemented. An owner whose key is stolen
can have arbitrary errata issued in their name, and every conforming importer
will act on them. Rotation, revocation, and delegated authority are Phase 2.

**Denial of service.** An owner can issue errata faster than importers can
repair. Nothing rate-limits or prioritises.

## Cryptographic caveats

The bundled Ed25519 is a reference implementation: correct against the RFC 8032
vectors, and **not constant-time**. Python integer arithmetic cannot be. It is
appropriate where signing keys are not attacker-facing. A deployment must
substitute a qualified production `Signer`; no caller changes. The current
candidate assessment in
[`docs/CRYPTOGRAPHY_QUALIFICATION.md`](docs/CRYPTOGRAPHY_QUALIFICATION.md)
does not yet qualify either reviewed backend or pass readiness gate G3.

## Reporting

Security findings go through the private channel in
[SECURITY.md](SECURITY.md), not a public issue. A demonstration that an
importer can report `verified` while its substrate retains the retired value is
the most valuable report this project can receive.
