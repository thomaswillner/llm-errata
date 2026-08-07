# Roadmap

This roadmap turns LLM Errata from a researched concept into a falsifiable interoperability experiment. It deliberately starts with files and deterministic controls before introducing network services, model integrations, or standards work.

## Guiding rule

Build the smallest system capable of disproving the idea.

The first implementation does not need vendor adoption, a universal memory ontology, or a production cryptographic infrastructure. It must demonstrate that one post-export change can be propagated, quarantined, repaired, tested, and honestly attested across heterogeneous stores.

## Phase 0 — Public challenge

**Status:** current phase

Objectives:

- publish the concept, research record, and feature-collision matrix;
- solicit missing prior art and corrections;
- distinguish documented capabilities from inference;
- narrow or retire the claim if the complete feature conjunction already exists;
- define implementation-neutral terminology for root, erratum, importer, known descendant, repair triad, coverage result, and receipt.

Exit gate:

- no documented public collision has been found that requires all four elements together;
- the operation and coverage semantics survive external review;
- at least one credible implementation path remains materially simpler than manual correction across tools.

## Phase 1 — File-backed proof

Build one local controller with no external service dependency.

### Canonical project shape

```text
prototype/
  identity/
    owner.pub
    importer.pub
  feeds/
    errata.jsonl
  registry/
    importers.yaml
    lineage.jsonl
  adapters/
    markdown/
    vector/
    opaque/
  fixtures/
    sources/
    stores/
  tests/
    cases.yaml
    conformance/
  receipts/
  snapshots/
  index.md
  log.md
```

### Required adapters

1. **Markdown adapter:** exact root-to-file and root-to-block lineage; deterministic quarantine and rebuild.
2. **Vector adapter:** local vector entries with root and derivation metadata; deletion or rebuild of affected entries.
3. **Opaque adapter:** simulates a store that can acknowledge an erratum but cannot enumerate or mutate all relevant state.

The opaque adapter is not a toy edge case. It is the control that proves the aggregate status cannot become green merely because observable adapters passed.

### Required scenarios

| Scenario | Required behavior |
|---|---|
| Correction | Retire a proposition that was wrong, rebuild descendants, and avoid preserving false history. |
| Supersession | Preserve the old proposition only for its valid historical interval and activate the new state. |
| Erasure | Remove or gate the target without copying its value into the receipt. |
| Mixed-source summary | Rebuild from retained inputs rather than deleting unrelated memory. |
| Feed rollback | Reject a lower sequence or conflicting checkpoint. |
| Stale reimport | Prevent an old export from recontaminating the repaired state. |
| Unknown store | Produce a non-success aggregate result even when all executable tests pass. |
| Interrupted repair | Keep affected retrieval quarantined and resume without exposing partially repaired state. |

### Phase 1 acceptance criteria

- quarantine is observable before any rebuild begins;
- every known descendant receives an explicit disposition;
- negative, positive, and preservation tests are independently recorded;
- a mixed artifact retains unrelated inputs;
- a stale export cannot silently restore the retired state;
- an `unknown`, `partial`, or `failed` required store prevents aggregate success;
- receipts bind the erratum plus deterministic pre-repair and post-repair state roots;
- tests run without an API key; model-graded probes are optional and clearly separated;
- the complete demo is reproducible from a clean checkout.

Kill or redesign the concept if exact lineage cannot survive even the controlled mixed-summary case, quarantine requires destructive deletion, or the receipt cannot communicate uncertainty without becoming meaningless.

## Phase 2 — Conformance surface

Only after the file-backed proof passes:

1. Define a compact, deterministic schema for errata and receipts.
2. Publish JSON Schema or CDDL plus canonical examples.
3. Implement a CLI as the primary control plane:

   ```text
   errata export
   errata publish
   errata pull
   errata plan
   errata quarantine
   errata repair
   errata test
   errata attest
   errata audit
   ```

4. Define an adapter interface for enumeration, quarantine, reconstruction, verification, and coverage reporting.
5. Publish conformance vectors for signatures, sequencing, key rotation, concurrent events, invalid targets, receipt binding, and confidentiality.
6. Add model-assisted semantic probes only behind a provider-neutral interface with deterministic fixtures and recorded verifier configuration.

Phase 2 is successful when two independently implemented adapters can consume the same erratum and produce receipts that a third-party validator evaluates consistently.

## Phase 3 — Interoperability experiment

Run one user-controlled root across at least three independently operated runtimes or memory systems.

Measure:

- time from observation to quarantine;
- proportion of known descendants addressed;
- stale-behavior rate across declared negative probes;
- replacement activation across positive probes;
- collateral retention across preservation probes;
- stale-reimport resistance;
- proportion of opaque coverage honestly reported;
- operator effort and user-visible friction.

The experiment must include at least one intentionally nonconforming importer and one system whose coverage is genuinely incomplete. A demonstration in which every component is designed to pass cannot validate the honesty requirement.

## Phase 4 — Compatibility profiles

Do not invent another base memory format unless implementation evidence makes it unavoidable. Evaluate profiles over existing building blocks:

- [EngramSpec](https://engramspec.org/) for cross-runtime context and incremental corrections;
- [Portable AI Memory v1](https://portable-ai-memory.org/spec/v1.0/) or [ApertoMemory](https://datatracker.ietf.org/doc/draft-ferro-apertomemory/02/) for exported memory objects;
- [vCon Lifecycle using SCITT](https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01) and [SCITT](https://datatracker.ietf.org/doc/rfc9943/) for transparent lifecycle statements and acknowledgments;
- [W3C PROV](https://www.w3.org/TR/prov-dm/) or equivalent local structures for derivation relationships.

Compatibility analysis must distinguish what each source normatively specifies from what LLM Errata would add. A SCITT inclusion receipt, for example, must never be described as proof that an importer completed semantic repair.

## Phase 5 — Standards decision

Choose a standards path only after working interoperability evidence exists.

Possible outcomes:

1. a small conformance profile layered on an existing transport;
2. an extension proposal to an active memory format;
3. an implementation convention with no formal standard;
4. retirement because a better native lifecycle mechanism has emerged.

Committee formation is not a success metric. Demonstrable repair, coverage honesty, user control, and adoption are.

## Security gates

Every phase must account for:

- issuer authorization and delegated authority;
- key rotation, recovery, and compromise;
- feed rollback and equivocation;
- poisoned or instruction-bearing payloads;
- denial of service through excessive repair events;
- privacy leakage through identifiers, polling, registrations, and receipts;
- confidential replacement delivery;
- receipts that do not retain erased content;
- compromised importers issuing false attestations;
- severed lineage, inaccessible stores, backups, provider logs, and model weights;
- separation between cryptographic authenticity and semantic evidence.

No phase may convert `unknown` coverage into `verified` for presentation purposes.

## Product-level falsifiers

Reconsider or abandon LLM Errata if evidence shows that:

1. users and vendors do not preserve stable import identity or return addresses;
2. lineage through ordinary summarization is too expensive or unreliable for meaningful coverage;
3. quarantine causes greater harm than temporary refusal or loss of personalization;
4. semantic repair probes cannot be distinguished from ordinary model variance;
5. a user-controlled canonical memory service solves the same problem more simply without unacceptable concentration or lock-in;
6. an existing public protocol evolves to implement the full conjunction before this work reaches interoperability.

## Definition of a credible 1.0

Version 1.0 requires all of the following:

- an openly documented erratum and receipt profile;
- at least two independent implementations;
- correction, supersession, and erasure conformance suites;
- deterministic structural validation and scoped behavioral evidence;
- explicit coverage semantics with no silent success;
- threat model and privacy analysis;
- key lifecycle and delegated-authorization rules;
- a demonstrated downstream-forwarding path;
- public documentation of failures and unsupported substrates;
- a refreshed prior-art review.

Until then, LLM Errata remains an experimental conformance proposal.
