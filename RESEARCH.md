# LLM Errata: Public Research and Decision Record

**Research cutoff:** 2026-08-01

**Status:** Public prior-art screening for a concept proposal

**Conclusion:** Novel synthesis with a narrow, apparently unimplemented conformance gap

This file records the research question, sources, search strategy, candidate eliminations, surviving claim, and ways to disprove it. It is a reproducible decision record, not a transcript of private reasoning. It does not claim patentability, a “world first,” or freedom to operate.

## Research question

The broad question was:

> What recurring problem could affect millions of LLM users, remain important as AI systems become more portable, and still have a technically specific gap after comparison with public products, implementations, papers, standards, and patents?

The question that survived screening was narrower:

> As of 2026-08-01, did any reviewed public implementation or normative profile require an importer of exported AI memory to receive later errata, quarantine and repair the memory's locally derived descendants, verify the repair behaviorally, and return a signed, coverage-aware result to the root owner?

The screened result is **LLM Errata**:

> **Verified descendant repair after an AI-memory update crosses a system boundary.**

The exact surviving feature conjunction is:

1. **Post-export update delivery.** A previously exported memory root remains addressable through an authenticated, monotonically sequenced correction, supersession, or erasure channel.
2. **Importer-side descendant quarantine and repair.** After validating an erratum, the importer blocks the root and its known local derivation closure before recall, then retires or rebuilds affected summaries, embeddings, profile fields, graph nodes, caches, and downstream exports from still-valid inputs.
3. **Three-way behavioral verification.** The importer tests that the retired belief is absent, the replacement is active when applicable, and unrelated memory survives. LLM Errata calls these the negative, positive, and preservation checks.
4. **Signed, coverage-aware callback.** The importer returns a receipt bound to the erratum and pre-/post-repair state roots, identifies the stores inspected, reports surfaces it cannot observe as `unknown`, and cannot claim aggregate success while a required store remains unresolved.

The claim is about the **complete conjunction**. None of its individual mechanisms is claimed as new.

## Why the problem can reach mass scale

OpenAI reported more than [800 million weekly ChatGPT users](https://openai.com/index/the-state-of-enterprise-ai-2025-report/) by December 2025. Its separate [consumer-use study](https://openai.com/index/how-people-are-using-chatgpt/) found that practical guidance, information seeking, and writing were dominant uses. A [2026 Glean survey of 6,000 digital workers](https://www.glean.com/work-ai-institute/reports/work-ai-index) reported that, among its respondents who use AI, 77% used multiple AI tools each week and 33% used four or more.

These samples cannot be multiplied together as if they measured the same population. They establish direction and scale: large populations use LLMs for persistent, practical work, and many users spread that work across tools.

The operational burden already appears inside single products. OpenAI's [Memory FAQ](https://help.openai.com/en/articles/8590148-memory-faq) explains that its memory summary is not exhaustive and that fully removing remembered information can require deleting all sources where it appears; retained chats can cause a memory to be recreated. LLM Errata does not treat this as criticism of one product. It uses the example to expose the harder cross-system question: what happens after a memory has been copied into independently operated assistants and transformed into new local artifacts?

## Concept and presentation precedent

The compact “idea file” presentation is inspired by Andrej Karpathy's [LLM Wiki idea file](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): a self-contained Markdown document that can be handed to a coding agent and iterated in public. That is a presentation precedent, not a claim that LLM Errata extends or implements LLM Wiki.

## Scope and definitions

### Included

- Personal and enterprise LLM memory that can be exported or synchronized across independently operated runtimes.
- Corrections to facts, temporal supersessions, and erasure requests.
- Raw memories and local derivatives such as summaries, reflections, embeddings, vector entries, knowledge graphs, prompt caches, profiles, and re-exports.
- Authentic update delivery, provenance, quarantine, dependency-aware repair, conformance testing, and bounded receipts.
- Publicly accessible material available or published by the cutoff date.

### Excluded

- General model-weight unlearning except where it clarifies the boundary between parametric and runtime memory.
- A claim that behavioral probes can mathematically prove semantic absence.
- A new base memory interchange format. Existing formats may carry LLM Errata roots and events.
- Legal conclusions about whether a particular deployment satisfies GDPR, the EU AI Act, CCPA, or any other law.
- Patentability, infringement, validity, claim construction, and freedom-to-operate conclusions.

### Key terms

- **Root:** A stable, opaque identifier for an exported memory object or source bundle.
- **Descendant:** A local artifact with recorded derivation from a root, directly or transitively.
- **Known derivation closure:** Every descendant reachable through the importer's registered lineage. It does not imply unknown copies have been discovered.
- **Correction:** The prior proposition was wrong for some or all of its asserted interval.
- **Supersession:** The prior proposition was valid and later ceased to be current.
- **Erasure:** The proposition must no longer be retained or used within the declared scope.
- **Coverage-aware receipt:** An attestation that states both what was checked and what remained outside the verified boundary.

## Source hierarchy

The screening gave more evidentiary weight to primary and normative sources than to summaries or marketing comparisons:

1. **Normative specifications and standards:** IETF/RFC and Internet-Drafts, W3C Recommendations, C2PA specifications, and published protocol specifications.
2. **First-party implementations and repositories:** public source repositories, implementation documentation, conformance suites, and project READMEs.
3. **Primary research:** papers and preprints describing agent memory, portability, dependency-aware unlearning, provenance, retention, and verification.
4. **First-party product documentation:** used to identify implemented product boundaries and explicit limitations.
5. **Patent documents:** used as a targeted mechanism-collision screen, not as a legal opinion.
6. **Adoption and user-control evidence:** used to assess scale and user burden, not technical novelty.

Mutable repositories and product pages were reviewed as available at the cutoff. Their current content may change; a formal release should pin repository commits or archive snapshots.

## Representative query families

The search broadened first and then combined mechanisms. Representative query families included:

- `portable AI memory protocol`, `cross-agent memory format`, `LLM memory export import`, `signed AI context interchange`
- `AI memory correction`, `memory supersession tombstone`, `LLM memory incremental diff`, `post-export memory update`
- `agent memory provenance derived summaries`, `dependency graph memory deletion`, `rebuild embeddings after correction`
- `verified forgetting LLM agent`, `memory erasure receipt`, `residue scan stale memory`, `reappearance test`
- `cross-recipient deletion notification receipt`, `SCITT lifecycle amendment deletion`, `signed downstream deletion acknowledgement`
- `credential status refresh revocation`, `signed provenance update manifest`, `derived asset update`
- combined searches such as `AI memory descendant repair receipt`, `correction callback pre state post state`, and `negative positive preservation memory repair test`
- patent-keyword combinations around `propagated deletion`, `derived dataset rebuild`, `provenance graph deletion`, `memory correction`, and `receipt`

The search was not restricted to these literal strings. Synonyms and combinations were used across general web search, paper indexes, standards repositories, source-code repositories, and patent search.

## Candidate loop and elimination record

The decision rule was conservative: discard a candidate when a close public implementation or normative design already covered its central contribution. Narrow only when the remaining boundary could be stated as a falsifiable feature conjunction.

| Candidate | Evidence that collided with it | Decision |
|---|---|---|
| Personal LLM wiki | Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) already establishes a strong file-native, agent-maintained personal knowledge pattern. | Rejected as the substantive idea; retained only as the presentation model. |
| Portable AI memory | [Portable Agent Memory](https://arxiv.org/html/2605.11032v1) defines signed, provenance-verifiable transfer through a Merkle-DAG; [Portable AI Memory v1](https://portable-ai-memory.org/spec/v1.0/) defines lifecycle status and incremental exports; [EngramSpec](https://engramspec.org/) defines signed cross-runtime context, corrections, and incremental diffs; [ApertoMemory draft-02](https://datatracker.ietf.org/doc/draft-ferro-apertomemory/02/) defines a signed and encrypted portable format. | Rejected. Portability and authenticated interchange are active, well-populated areas. |
| Memory makefile or derivation graph | [W3C PROV](https://www.w3.org/TR/prov-dm/) standardizes derivation relations; [Portable Agent Memory](https://arxiv.org/html/2605.11032v1) applies a provenance DAG to portable memories; [TMLS Agent Memory and State](https://www.tmls.nyc/research/agent-memory-state) follows provenance to invalidate and recompute derived artifacts. | Rejected. Lineage and rebuild graphs are established mechanisms. |
| Verified forgetting | [Inspeximus](https://github.com/DanceNitra/inspeximus) implements lineage-aware erasure, residue checks, echo guards, and content-free signed receipts; [Agentic Unlearning](https://arxiv.org/html/2602.17692v1) uses a dependency graph, blocklist, and deletion of derived artifacts; [MaRS](https://arxiv.org/html/2512.12856v1) models provenance-aware retention and subgraph erasure; the [long-term-memory security survey](https://arxiv.org/html/2604.16548v1) explicitly calls for cross-substrate deletion and reappearance tests. | Rejected as a broad claim. The local deletion and testing primitives already exist. |
| Temporal contradiction ledger | [Portable AI Memory v1](https://portable-ai-memory.org/spec/v1.0/) has `superseded`, `retracted`, and related lifecycle states; [EngramSpec](https://engramspec.org/) includes corrections and belief evolution; [Inspeximus](https://github.com/DanceNitra/inspeximus) exposes keyed supersession, timelines, and revert. | Rejected. Temporal validity and correction history are not the gap. |
| Self-correcting local memory | [Shomei](https://shomei.ai/how-it-works/) ties recall to sources and policy, records lifecycle operations, and exposes bounded receipts; [Inspeximus](https://github.com/DanceNitra/inspeximus) implements correction and erasure controls; [TMLS](https://www.tmls.nyc/research/agent-memory-state) describes provenance-led local recomputation. | Rejected. The unresolved boundary is between independent importers, not inside one governed store. |
| Signed post-export update feed | [EngramSpec](https://engramspec.org/) provides a live context endpoint and incremental diffs with tombstones; [Portable AI Memory v1](https://portable-ai-memory.org/spec/v1.0/) supports incremental updates and retractions; [vCon Lifecycle using SCITT](https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01) records cross-recipient lifecycle events; the [IAB Data Deletion Request Framework](https://github.com/InteractiveAdvertisingBureau/Data-Subject-Rights/blob/main/Data%20Deletion%20Request%20Framework.md) propagates signed requests and acknowledgements down a recipient chain; [W3C Verifiable Credentials](https://www.w3.org/TR/vc-data-model-2.0/#refreshing), [Bitstring Status List](https://www.w3.org/TR/vc-bitstring-status-list/), and [C2PA 2.4](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html) supply adjacent status, refresh, revocation, and update-manifest patterns. | Rejected. Authenticated update delivery and acknowledgement already have multiple precedents. |
| **Verified cross-importer descendant repair** | No reviewed source required the complete four-feature conjunction. See [PRIOR_ART.md](PRIOR_ART.md) for the feature-by-feature record. | **Survived, narrowly.** |

## The strongest collisions

### Transport: EngramSpec

[EngramSpec](https://engramspec.org/) is the closest AI-memory transport collision. Its public specification describes signed envelopes, corrections, expiry, pull-based incremental diffs with tombstones, conformance tiers, and a reference implementation. Its own limitations identify the absence of a webhook/push model in v0.1. The distinction is not “Engram lacks corrections.” It plainly has them. The remaining screened boundary is what an importer must do to **locally derived artifacts after accepting a change**, how that behavior is tested, and what evidence is returned.

### Cross-recipient control plane: vCon Lifecycle and SCITT

The individual [vCon Lifecycle using SCITT Internet-Draft](https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01) is the closest formal lifecycle-control collision. It defines a workflow for recording distribution, amendments, consent changes, deletion, and recipient acknowledgement across security boundaries. [SCITT RFC 9943](https://datatracker.ietf.org/doc/rfc9943/) supplies signed statements, transparency services, and inclusion receipts.

The distinction is not that these systems lack cross-recipient events or receipts. The individual vCon draft explicitly covers them. The reviewed draft leaves actual workflow implementations to applications and does not normatively define AI-memory descendant quarantine, reconstruction of mixed summaries or vectors, the negative-positive-preservation test triad, or a repair receipt bound to pre-/post-repair importer state.

### Governed local memory: Shomei and Inspeximus

[Shomei](https://shomei.ai/how-it-works/) documents source-linked recall, policy-checked use, lifecycle events, explicit coverage boundaries, and narrow receipts. The reviewed [HTTP API](https://shomei.ai/docs/http-api/) and [governance documentation](https://shomei.ai/docs/governance-and-receipts/) add correction/update, lineage, erasure-cascade, pending external deletion, and signed-receipt detail. Shomei also states that its receipts do not certify deletion by systems it does not govern.

[Inspeximus](https://github.com/DanceNitra/inspeximus) is a strong open-source local collision: keyed supersession, `echo_guard`, revert, lineage-aware retraction, residue scans, preservation checks, and signed content-free erasure receipts are publicly described. These mechanisms apply to explicitly keyed or successfully extractor-keyed assertions; its README reports that raw conversational prose is rarely keyed reliably and supersession therefore mostly does not fire there. Its documented scope is its own store, not every vector index, prompt log, backup, or independently operated importer.

LLM Errata does not claim these local controls as new. It profiles their missing cross-importer contract.

### Dependency-aware deletion and rebuild

[TMLS Agent Memory and State](https://www.tmls.nyc/research/agent-memory-state) explicitly describes following provenance from a source event to consolidated facts, graph edges, and vector entries, then recomputing consolidations. [Agentic Unlearning](https://arxiv.org/html/2602.17692v1) models raw memories, summaries, reflections, graph entities, and vectors as a dependency structure; it blocklists targets at retrieval, traverses the closure, and preserves shared artifacts. [MaRS](https://arxiv.org/html/2512.12856v1) uses a provenance-aware graph with retention, summary, deletion, and audit semantics.

These works establish that dependency-aware invalidation, deletion, and regeneration are not new. The candidate contribution is to make such repair an **interoperable importer duty after a cross-boundary erratum** and to return bounded evidence to the issuer.

### Generic provenance, status, and downstream deletion

- [W3C PROV-DM](https://www.w3.org/TR/prov-dm/) supplies a general derivation vocabulary.
- [W3C Verifiable Credentials Data Model 2.0](https://www.w3.org/TR/vc-data-model-2.0/#refreshing) and [Bitstring Status List 1.0](https://www.w3.org/TR/vc-bitstring-status-list/) supply refresh, revocation, suspension, and status patterns.
- [C2PA 2.4](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html) supplies signed provenance and update manifests for assets.
- The [IAB deletion framework](https://github.com/InteractiveAdvertisingBureau/Data-Subject-Rights/blob/main/Data%20Deletion%20Request%20Framework.md) supplies signed request propagation and acknowledgement while expressly leaving recipient action out of scope.
- [SCITT RFC 9943](https://datatracker.ietf.org/doc/rfc9943/) supplies transparency receipts for registered signed statements, not proof that an application performed semantic repair.

These are suitable building blocks. None is displaced by LLM Errata.

### Derived-data patent collision

[US10956406B2, “Propagated deletion of database records and derived data”](https://patents.google.com/patent/US10956406B2/en), describes traversing relationships and rebuilding derived datasets after raw data is deleted, including awareness of exported data. This is a material collision with any broad claim to provenance-based propagated rebuild.

It is one reason the proposal does **not** claim invention of derived-data deletion or rebuild. The patent review was a keyword and mechanism screen only; it was not a claim chart, legal opinion, or freedom-to-operate analysis.

## Decision and defensible claim

The strongest defensible public wording is:

> **LLM Errata proposes a vendor-neutral conformance contract requiring post-export update delivery, importer-side quarantine and repair of the known descendant closure, negative-positive-preservation verification, and a signed coverage-aware callback bound to the erratum and pre-/post-repair state. No reviewed public implementation or normative profile was found to require that complete conjunction as of 2026-08-01.**

The following formulations are not supported by this research:

- “Nobody has tackled correction of AI memory.”
- “This is the first portable AI-memory protocol.”
- “This invents dependency-aware deletion, rebuild, provenance, signed receipts, or behavioral forgetting tests.”
- “The research proves no equivalent private or unpublished system exists.”
- “The concept is patentable, non-infringing, or free to operate.”

## Falsifiers and update policy

The prior-art conclusion should be revised or withdrawn if a dated public source demonstrates, in one implementation or normative profile, all of the following:

1. An update channel reaches prior importers of an exported AI-memory root after the initial transfer.
2. A valid event causes pre-repair quarantine and traversal of the importer's local descendant closure across relevant stores.
3. Mixed descendants are rebuilt or retired while unrelated memory is preserved.
4. Conformance requires negative, positive when applicable, and preservation checks.
5. The importer returns a signed callback bound to the triggering event and pre-/post-repair state, with explicit `partial`, `unknown`, or `failed` coverage where full verification is impossible.

Partial matches should be added to [PRIOR_ART.md](PRIOR_ART.md), not concealed. A future implementation that closes the whole gap would not make the user problem disappear; it would invalidate the claim that the conformance boundary remained unimplemented.

The product hypothesis should also be reconsidered if:

- common importers will not preserve stable root IDs and errata endpoints;
- lineage is routinely severed during summarization, embedding, or export;
- quarantine latency cannot be kept below the next recall opportunity;
- behavioral probes cannot distinguish repair from ordinary model variance;
- receipt verification becomes more expensive than the user value it protects; or
- vendors standardize equivalent semantics through another profile.

## Limitations

Internet research cannot prove a negative. The search may have missed:

- private systems and unpublished work;
- non-English or poorly indexed material;
- rapidly changing repositories and documentation;
- product capabilities not described publicly;
- recent patent applications not yet published;
- equivalent mechanisms described with different terminology.

Several reviewed sources were drafts or preprints. In particular, the vCon Lifecycle document was an individual Internet-Draft at the cutoff, not an IETF-endorsed standard. EngramSpec and Portable AI Memory are project specifications, not standards merely because they use normative language. Product documentation describes represented behavior but is not equivalent to independent verification.

Behavioral tests are bounded evidence, not proofs of semantic absence. Cryptographic signatures authenticate who attested to bytes; they do not establish that the attestation is truthful or complete. Unknown stores, severed lineage, backups, provider logs, model weights, and external copies must remain outside the verified boundary unless directly inspected.

## AI-assisted research disclosure

The concept was developed under the author's direction using AI-assisted web research, source comparison, candidate generation, adversarial prior-art review, and drafting. The public claim was deliberately narrowed when close work was found. The author is responsible for reviewing the cited evidence, accepting or changing the proposal, and maintaining corrections to this research record.

AI assistance does not make the search exhaustive and does not replace independent technical or legal review.

## Source index

### Portable memory and AI-memory governance

- [Portable Agent Memory](https://arxiv.org/html/2605.11032v1)
- [Portable AI Memory specification v1.0](https://portable-ai-memory.org/spec/v1.0/)
- [EngramSpec](https://engramspec.org/)
- [ApertoMemory draft-02](https://datatracker.ietf.org/doc/draft-ferro-apertomemory/02/)
- [Shomei overview](https://shomei.ai/how-it-works/)
- [Shomei HTTP API](https://shomei.ai/docs/http-api/)
- [Shomei governance and receipts](https://shomei.ai/docs/governance-and-receipts/)
- [Inspeximus](https://github.com/DanceNitra/inspeximus)

### Dependency-aware memory, unlearning, and security

- [TMLS: Agent Memory and State](https://www.tmls.nyc/research/agent-memory-state)
- [Agentic Unlearning](https://arxiv.org/html/2602.17692v1)
- [MaRS / Forgetful but Faithful](https://arxiv.org/html/2512.12856v1)
- [Survey on the Security of Long-Term Memory in LLM Agents](https://arxiv.org/html/2604.16548v1)

### Cross-recipient lifecycle, provenance, status, and receipts

- [vCon Lifecycle Management using SCITT, draft-01](https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01)
- [SCITT RFC 9943](https://datatracker.ietf.org/doc/rfc9943/)
- [IAB Data Deletion Request Framework](https://github.com/InteractiveAdvertisingBureau/Data-Subject-Rights/blob/main/Data%20Deletion%20Request%20Framework.md)
- [W3C PROV-DM](https://www.w3.org/TR/prov-dm/)
- [W3C Verifiable Credentials Data Model 2.0: Refreshing](https://www.w3.org/TR/vc-data-model-2.0/#refreshing)
- [W3C Bitstring Status List 1.0](https://www.w3.org/TR/vc-bitstring-status-list/)
- [C2PA Technical Specification 2.4](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html)

### Patent screen

- [US10956406B2: Propagated deletion of database records and derived data](https://patents.google.com/patent/US10956406B2/en)

### Scale and user-control evidence

- [OpenAI: The state of enterprise AI, 2025 report](https://openai.com/index/the-state-of-enterprise-ai-2025-report/)
- [OpenAI: How people are using ChatGPT](https://openai.com/index/how-people-are-using-chatgpt/)
- [OpenAI Memory FAQ](https://help.openai.com/en/articles/8590148-memory-faq)
- [Glean Work AI Index](https://www.glean.com/work-ai-institute/reports/work-ai-index)
