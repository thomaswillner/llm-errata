# Prior Art and Feature-Collision Matrix

**Research cutoff:** 2026-08-01. **Supplementary screen:** 2026-08-07, recorded in [HARD_PROBLEMS.md](HARD_PROBLEMS.md); four rows added below and marked with their date.

This document tests the bounded LLM Errata claim against its closest public predecessors. It distinguishes a complete collision from a system that implements one or more of the same mechanisms.

It is a public technical comparison, not a patentability search, claim chart, legal opinion, or proof that an equivalent private system does not exist.

## The feature conjunction being tested

The proposal survives only if the following four requirements are evaluated together:

| ID | Requirement |
|---|---|
| A | **Post-export update delivery:** an authenticated correction, supersession, or erasure reaches an importer after the original memory transfer. |
| B | **Descendant quarantine and repair:** the importer blocks the root and its known local derivation closure before recall, then retires or rebuilds affected descendants. |
| C | **Repair triad:** conformance tests the negative, positive when applicable, and preservation postconditions. |
| D | **Authenticated, coverage-truthful callback:** D1 authenticates the importer and signed receipt bytes; D2 requires the signed stores, aggregate, and limitations to match the declared required scope, including incomplete or unknown coverage. |

No individual mechanism is claimed as new.

## How to read the matrix

- **Yes:** the reviewed public source documents or implements the materially matching feature.
- **Partial:** the source contains an adjacent or narrower mechanism, but not the complete LLM Errata requirement.
- **No requirement found:** the reviewed source did not document the feature. This does not prove it cannot exist elsewhere.
- **Proposed:** the feature is part of LLM Errata's design; it is not evidence of an implementation.

## Collision matrix

| Public work | A: update delivery | B: descendant repair | C: repair triad | D: signed coverage callback | Assessment |
|---|---|---|---|---|---|
| [EngramSpec](https://engramspec.org/) | **Yes/Partial:** live correction endpoint and pull-based incremental diffs with tombstones; no webhook/push model in v0.1 | No requirement found for quarantine and repair of importer-local summaries, vectors, graphs, or caches | No requirement found | No repair callback found | **Strongest AI-memory transport collision.** It substantially eliminates “portable corrections” as the novel idea, but not importer-local repair conformance. |
| [vCon Lifecycle using SCITT](https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01) with [SCITT RFC 9943](https://datatracker.ietf.org/doc/rfc9943/) | **Yes:** lifecycle events and acknowledgments across recipients | No AI-memory descendant-repair requirement; workflow implementation is left to applications | No | **Partial:** acknowledgments and SCITT inclusion receipts, not a semantic-repair coverage receipt | **Strongest formal control-plane collision.** It proves that cross-recipient lifecycle events and transparent receipts are not new. |
| [Shomei](https://shomei.ai/how-it-works/) ([API](https://shomei.ai/docs/http-api/), [governance](https://shomei.ai/docs/governance-and-receipts/)) | **Partial:** governed correction/update inside the Shomei boundary; no reviewed persistent post-export importer subscription/callback obligation | **Yes locally:** derived lineage, erasure cascades, and explicit external-delete-pending states | **Partial:** bounded governance evidence, but no reviewed mandatory negative + positive + preservation profile for each importer | **Partial:** signed, bounded governance receipts, but not the complete cross-importer callback | **Strongest governed-memory product collision.** It establishes local lineage, lifecycle, honest coverage, and receipts. |
| [Inspeximus](https://github.com/DanceNitra/inspeximus) | **Partial:** local keyed correction/supersession and erasure channel | **Yes locally, within declared lineage:** `retract_lineage` demotes a root and its recorded descendants from default recall, retains them as superseded with `needs_rederivation`, and `rederive` can rebuild against the correction | **Partial:** stale-value and preservation-oriented checks; no reviewed mandatory replacement-activation triad across independent stores | **Partial:** signed content-free erasure evidence; current `erasure_audit` demotes known unresolved derivation holes but still cannot prove subject-specific completeness after a correct content-free cascade, and there is no cross-importer callback | **Strongest open-source local correction collision.** It substantially implements quarantine-then-rebuild inside one store. Its documented limit remains recorded lineage and its own boundary, not prior independent importers. |
| [MemoRepair](https://arxiv.org/abs/2605.07242v1) | No cross-system delivery | **Yes, as an explicit contract:** descendants withdrawn before repair, republication restricted to validated predecessor-closed successors; invalidated-memory exposure cut from 69.8–94.3% to 0% *given complete influence provenance* | **Partial:** validated republication, no preservation test | No | **Strongest requirement-B collision found.** It independently arrives at quarantine-before-repair. Added 2026-08-07; post-dates the original cutoff. |
| [Governed Evolving Memory](https://arxiv.org/abs/2605.26252v1) | No | **Partial:** formal correctness conditions for dependency consistency and provenance preservation | No | No | Argues record-level stores cannot satisfy those conditions. |
| [Always-On Agents / AOEP-v0](https://arxiv.org/abs/2606.30306v1) | No | Governance obligations scored, not implemented | **Partial:** a deterministic evaluation contract scoring state mutation and recovery rather than answer quality | No | **Closest conformance-protocol collision.** |
| [memorywire](https://arxiv.org/abs/2606.01138v3) | **Partial:** vendor-neutral wire format with forget and expire operations | No | No | No | Relevant to the vendor-neutral framing, not to importer repair. |
| [TMLS Agent Memory and State](https://www.tmls.nyc/research/agent-memory-state) | No cross-importer update channel | **Yes as an architecture pattern:** provenance-led invalidation and recomputation of derived facts, graph edges, and vectors | Partial regression guidance | No | Eliminates provenance-led rebuild as the novel mechanism. |
| [Agentic Unlearning](https://arxiv.org/html/2602.17692v1) | No cross-vendor post-export delivery | **Yes for unlearning:** blocks targets and traverses dependencies across raw memory, summaries, reflections, graphs, and vectors | Partial negative/preservation objectives; not benign replacement activation | No callback to an origin | Eliminates dependency-aware deletion/unlearning as the central invention. |
| [MaRS](https://arxiv.org/html/2512.12856v1) | No cross-importer delivery | **Yes for erasure:** typed provenance graph, propagation, and summary regeneration | Partial erasure and utility evaluation | No | Establishes graph-based retention, deletion, regeneration, and audit semantics. |
| [Portable Agent Memory](https://arxiv.org/html/2605.11032v1) | **Partial:** signed portable memory and rehydration, not the complete later-erratum obligation | Provenance/Merkle-DAG primitives, but no reviewed importer repair profile | No | No | Eliminates signed, provenance-verifiable portability as the novel contribution. |
| [Portable AI Memory v1](https://portable-ai-memory.org/spec/v1.0/) | **Partial:** exported objects, incremental deltas, merge rules, and `superseded`/`retracted` states | No normative local descendant cascade found | No | No | Signatures are optional and do not imply authentication of every bundle field; portability and lifecycle status are not the remaining gap. |
| [ApertoMemory draft-02](https://datatracker.ietf.org/doc/draft-ferro-apertomemory/02/) | No; synchronization is stated to be out of scope | No | No | No | Supplies signed and encrypted provider-independent memory objects, not their post-import repair lifecycle. |
| [W3C PROV-DM](https://www.w3.org/TR/prov-dm/) | No | **Partial:** generic derivation and invalidation vocabulary | No | No | Establishes provenance primitives; it does not define an AI-memory repair protocol. |
| [W3C VC refresh](https://www.w3.org/TR/vc-data-model-2.0/#refreshing) and [Bitstring Status List](https://www.w3.org/TR/vc-bitstring-status-list/) | **Partial:** issuer-controlled refresh and status mechanisms | No | No | No | Establishes refresh, revocation, suspension, and status patterns for exported credentials. |
| [C2PA 2.4](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html) | **Partial:** signed update manifests and revocation information | Provenance for assets, not importer-local semantic memory repair | No | No | Establishes signed provenance/update patterns in another domain. |
| [IAB Data Deletion Request Framework](https://github.com/InteractiveAdvertisingBureau/Data-Subject-Rights/blob/main/Data%20Deletion%20Request%20Framework.md) | **Yes for deletion:** signed downstream request propagation | Recipient deletion action is not an AI-memory descendant-rebuild contract | No positive replacement or preservation triad | **Partial:** acknowledgments, not a pre-/post-state semantic repair receipt | Eliminates signed downstream deletion propagation as the novel idea. |
| [US10956406B2](https://patents.google.com/patent/US10956406B2/en) | Partial awareness of source and exported data changes | **Yes/Partial:** traversal and rebuild of derived datasets after source deletion | No AI-memory behavioral triad | No cross-importer coverage callback | Material patent collision with any broad claim to invention of propagated derived-data deletion or rebuild. |
| **LLM Errata** | **Proposed** | **Proposed** | **Proposed** | **Proposed** | The claim is the conformance conjunction, not any individual cell. |

## Detailed findings

### EngramSpec: the closest AI-memory transport collision

The reviewed [EngramSpec](https://engramspec.org/) materials describe:

- a cross-runtime context protocol;
- full context retrieval and runtime-submitted corrections;
- incremental diffs with tombstones;
- Ed25519-signed server envelopes;
- expiry handling, discovery, conformance tiers, and a live reference implementation.

The site also records material v0.1 limits: client-side signature verification is planned for v0.2 and the synchronization model is pull-only, without webhooks. Those qualifications matter.

EngramSpec means LLM Errata cannot credibly claim that nobody has built cross-runtime memory corrections or incremental correction sync. The reviewed material did not additionally require an importing runtime to enumerate and quarantine its own derivation closure, rebuild local mixed artifacts, execute the repair triad, and return a coverage-aware repair callback.

### vCon Lifecycle and SCITT: the closest formal control plane

The May 2026 [vCon Lifecycle using SCITT](https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01) document is an active **individual Internet-Draft**, not an IETF-endorsed standard. It proposes SCITT-ledger events for distribution, receipt, amendments, consent changes, deletion, expiry, and acknowledgments across vCon recipients. It explicitly says actual workflow implementations are left to implementers and applications.

[SCITT RFC 9943](https://datatracker.ietf.org/doc/rfc9943/) defines transparent signed statements and verifiable inclusion receipts. A SCITT receipt establishes registration or inclusion of a signed statement. It does not prove that an application repaired summaries, removed vector entries, rebuilt prompt material, or changed model behavior.

LLM Errata therefore profiles a downstream application boundary the reviewed draft does not normatively specify. It does not replace the vCon or SCITT control plane.

### Shomei and Inspeximus: the closest local systems

Shomei's [overview](https://shomei.ai/how-it-works/), [HTTP API](https://shomei.ai/docs/http-api/), and [governance documentation](https://shomei.ai/docs/governance-and-receipts/) describe source-linked and policy-gated recall, correction/update operations, derived-artifact lineage, erasure cascades, bounded receipts, and external deletion states that remain pending when completion cannot be established.

That is a substantial collision with any claim that lineage-aware correction, honest coverage, or signed receipts are new. The reviewed material did not establish a persistent obligation for every independently operated prior importer to receive an erratum and return the complete repair-triad callback.

Inspeximus publicly describes keyed supersession, an `echo_guard`, revert,
lineage-aware retraction, residue scans, preservation behavior, and content-free
signed erasure receipts. At pinned commit
[`4c711f2982911841d86d7ac1989b0ffb866dc891`](https://github.com/DanceNitra/inspeximus/tree/4c711f2982911841d86d7ac1989b0ffb866dc891),
`retract_lineage(subject)` demotes the subject and every descendant reachable
through recorded `derived_from` taint to superseded state, removes them from
default recall, retains them for `include_superseded`, and marks them
`needs_rederivation`; `rederive(subject)` rebuilds eligible descendants against
the corrected root. That is a stronger requirement-B collision than the
previous comparison to `forget_subject` and should be treated as local
quarantine-then-rebuild, not merely deletion.

The earlier pinned documentation described `erasure_audit()` returning
`coverage{records, with_declared_lineage, undeclared_derived, declared_ratio}`
and allowed a nonzero incomplete ratio to return `no_declared_residue`. The
maintainer accepted that finding and changed commit
[`36611027a463a8e526e23baf2d6bb8d9797b67ac`](https://github.com/DanceNitra/inspeximus/commit/36611027a463a8e526e23baf2d6bb8d9797b67ac): known unresolved derivation holes
now return `partially_audited`, and the audit reports
`subject_reachable_records`. The maintainer also found that zero subject reach
cannot gate success because a correct content-free cascade can erase the same
evidence needed to distinguish “nothing was declared” from “everything was
erased.” That residual limit is material.

The same conflict-disclosed review found a mirror defect in LLM Errata: an
adapter could enumerate an empty set without proving root-specific lineage
completeness and still receive `verified`. The earlier sentence claiming this
repository's aggregation was categorically stricter was therefore false. The
reference controller now maps that unsupported empty walk to `unknown`, while
preserving the four public coverage results. Both projects still trust their
own adapter or store instrumentation and neither result is independent
certification. The maintainer's 0.0000 dogfood ratio remains interested-party
testimony, not independently reproduced evidence.

These mechanisms apply to explicitly keyed or successfully extractor-keyed
assertions and recorded lineage. The documented scope is one store, not every
vector index, prompt log, backup, or independently operated importer.

LLM Errata does not claim to improve or replace these local systems. It proposes the conformance boundary between an origin and multiple importers.

### MemoRepair: the closest requirement-B collision

[MemoRepair](https://arxiv.org/abs/2605.07242v1) (2026-05-08) was found in the 2026-08-07 supplementary screen, after the original cutoff. It is the strongest single result against any broad reading of requirement B, and it should be read before the older dependency-aware-rebuild sources below.

It defines a repair contract in which invalidated descendants are withdrawn *before* repair and republication is restricted to validated, predecessor-closed successors. That is the same ordering this proposal calls quarantine-before-repair, arrived at independently. It reports invalidated-memory exposure falling from 69.8–94.3% to 0%, conditional on complete influence provenance, and reports that dropping 1% of influence edges yields 17.7% leaked invalidated state.

Two consequences, and they pull in opposite directions:

- Quarantine-before-repair is no longer distinctive. It should not be presented as a contribution of this proposal.
- The 1%-to-17.7% amplification is the strongest quantitative support yet for the rule that a required store left unresolved must prevent a green aggregate. Incomplete lineage does not degrade gracefully.

MemoRepair has no cross-boundary delivery to a prior importer, no preservation test, and no receipt, so requirements A, the preservation leg of C, and D still hold.

### Dependency-aware rebuild is established

[TMLS Agent Memory and State](https://www.tmls.nyc/research/agent-memory-state), [Agentic Unlearning](https://arxiv.org/html/2602.17692v1), and [MaRS](https://arxiv.org/html/2512.12856v1) independently establish that provenance-guided invalidation, dependency traversal, blocking, deletion, regeneration, and shared-artifact preservation are active areas with concrete mechanisms.

The [long-term-memory security survey](https://arxiv.org/html/2604.16548v1) likewise identifies compression lineage, cross-substrate forgetting, and reappearance testing as important memory-security problems. A future LLM Errata implementation should reuse and compare these techniques; it must not present them as inventions of this proposal.

### Generic update, status, and provenance patterns are established

[W3C PROV-DM](https://www.w3.org/TR/prov-dm/), [W3C Verifiable Credentials](https://www.w3.org/TR/vc-data-model-2.0/#refreshing), the [W3C Bitstring Status List](https://www.w3.org/TR/vc-bitstring-status-list/), [C2PA 2.4](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html), and the [IAB deletion framework](https://github.com/InteractiveAdvertisingBureau/Data-Subject-Rights/blob/main/Data%20Deletion%20Request%20Framework.md) demonstrate that derivation, invalidation, refresh, revocation, signed update manifests, downstream requests, and acknowledgments are mature cross-domain primitives.

LLM Errata's opportunity is a memory-specific composition with strict importer behavior and honest semantic coverage, not a reinvention of those primitives.

## Strongest defensible novelty statement

> **LLM Errata proposes a vendor-neutral conformance contract requiring post-export update delivery, importer-side quarantine and repair of the known descendant closure, negative-positive-preservation verification, and a signed coverage-aware callback bound to the erratum and pre-/post-repair state. No reviewed public implementation or normative profile was found to require that complete conjunction as of 2026-08-01.**

This is a **novel synthesis with a narrow, apparently unimplemented conformance gap**. The public evidence does not support claims of a world first, patentability, non-infringement, legal priority, or freedom to operate.

## What would invalidate the claim

A complete collision should identify one dated public implementation or normative profile that requires all of the following:

1. later updates reach prior importers of an exported AI-memory root;
2. a valid event causes quarantine of the root and the importer's known local descendant closure before recall;
3. descendants are rebuilt or retired without destroying unrelated retained memory;
4. conformance requires negative, positive when applicable, and preservation tests;
5. the importer returns an authenticated callback bound to the erratum and pre-/post-repair state, while a separate coverage-truthfulness check requires explicit incomplete or unknown coverage.

When such evidence appears, this repository should record it, narrow or withdraw the novelty statement, and preserve the correction in [CHANGELOG.md](CHANGELOG.md). The correct response to a complete collision is not semantic argument—it is an erratum to LLM Errata itself.

## Source-status notes

- **Standards status:** SCITT is an RFC. The cited vCon Lifecycle document and ApertoMemory are Internet-Drafts. An Internet-Draft is work in progress and is not an IETF standard merely because it appears on the IETF Datatracker.
- **Project specifications:** EngramSpec and Portable AI Memory are public project specifications, not standards solely because they use normative language.
- **Research maturity:** several cited papers are preprints and should be treated accordingly.
- **Mutable documentation:** product sites and repositories may change after the cutoff. Future releases should pin material versions or commits when practicable.
- **Patent boundary:** Google Patents status and keyword similarity are discovery signals, not legal conclusions. Counsel would need to perform any professional patent or freedom-to-operate analysis.
- **Evidence boundary:** “No requirement found” means no such requirement was located in the reviewed material; it does not assert that an undocumented capability is impossible.
