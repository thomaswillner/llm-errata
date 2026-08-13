# LLM Errata

An idea file for making corrections follow AI memory after it has been copied.

| Field | Value |
|---|---|
| Author | Thomas Rainer Willner |
| Version | 0.1.0 |
| Status | Public concept proposal / Request for Comment |
| Published | 2026-08-01 |

This document is meant to be pasted into a coding agent and built collaboratively. It follows the compact, inspectable spirit of Andrej Karpathy's [LLM Wiki idea file](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), but proposes a different system.

> **An imported memory is a dependency, not a copy.** When its source changes, the importer should quarantine its known descendants, rebuild them from valid inputs, and report anything it could not verify.

> **If an AI accepts a memory, it should also accept responsibility for its future errata.**

**Research status, 2026-08-01:** novel synthesis with a narrow, apparently unimplemented conformance gap—not a claim of patentability, a “world first,” or freedom to operate. The broad ideas around it already exist. The candidate that survived the research loop is specifically **verified descendant repair after an AI-memory update crosses a system boundary**.

## Author's premise

I work at the intersection of enterprise AI, identity security, and governance. Identity practitioners already understand that provisioning without lifecycle control creates lasting risk. AI-memory portability is developing the same structural weakness: systems are defining how memory is issued and transferred without defining what every importer must do when that memory changes.

LLM Errata applies lifecycle accountability to imported AI memory. This is an independent proposal and does not represent the position of my employer or any organization referenced here.

## Start with one ordinary failure

In January, Alice tells her personal assistant that she is vegetarian. She exports its memory to a travel planner and a work-event assistant. Each importer turns the fact into its own summary, embedding, profile field, and prompt cache.

In August, Alice says the preference has ended. The original assistant updates itself, but the two importers still hold the January snapshot and its derivatives. Alice now has to remember which tools remember the wrong thing, find every relevant setting, and hope an old chat or cache does not recreate it.

LLM Errata changes the contract:

1. The exported memory carries a stable root ID, an owner key, and an errata endpoint.
2. Alice publishes one signed **supersession** for that root.
3. Each importer blocks the root and its known descendants from recall immediately.
4. Each importer rebuilds mixed artifacts from still-valid inputs.
5. Each importer checks that the old belief stopped appearing, the new state works, and unrelated preferences survived.
6. Each importer returns an honest receipt. The work assistant, unable to inspect a vendor-owned cache, reports `unknown`; it does not claim success.

The user sees one verified importer and one unresolved importer. “Notice delivered” is no longer confused with “memory repaired.”

## Why this is a mass-user problem

OpenAI reported more than [800 million weekly ChatGPT users](https://openai.com/index/the-state-of-enterprise-ai-2025-report/) by December 2025. A separate [OpenAI/NBER consumer-use study](https://openai.com/index/how-people-are-using-chatgpt/) found that practical guidance, information seeking, and writing dominate ordinary usage—not just disposable experiments.

People are also spreading work across assistants. In a 2026 survey of 6,000 digital workers, [Glean reported](https://www.glean.com/work-ai-institute/reports/work-ai-index) that, among its respondents who use AI, 77% used multiple AI tools each week and 33% used four or more. These populations are not directly interchangeable, but at this scale even a small affected fraction is millions of people.

Current correction controls expose the underlying burden. OpenAI's [Memory FAQ](https://help.openai.com/en/articles/8590148-memory-faq) says its memory summary is not exhaustive; fully removing something may require deleting every source in which it appears, including chats, archived chats, files, summaries, and connected apps; retained chats may cause a memory to be recreated. LLM Errata does not criticize that product-specific control. It asks what happens after the same memory has already crossed into independently operated tools.

This problem becomes more important as portable-memory formats mature. Portability solves **movement**. It does not, by itself, solve the lifecycle of the copies created by movement.

## The inversion: a correction is a state transition

Most memory APIs expose some variation of:

```text
remember(value)
recall(query)
delete(id)
```

Add a different primitive:

```text
repair(root, correct | supersede | erase, postconditions)
```

Deleting a sentence and adding another is insufficient. The old claim may already have influenced summaries, vectors, graph edges, recommendations, caches, or exports. The unit of work is therefore the root's **known derivation closure**, not merely its current text representation.

Every repair uses a three-way check—the **repair triad**:

1. **Negative:** the retired proposition did not reappear in the declared test scope.
2. **Positive:** the replacement influenced the cases in which it should.
3. **Preservation:** nearby facts that were not changed still worked.

Within an inspectable adapter scope, preservation also requires bounded
proposition multiplicity: repair must not increase active assertions of a
preserved proposition unless the erratum requires another assertion. The
adapter supplies stable provider-local proposition identity and count for the
synthetic conformance fixture. Text similarity is not identity; an adapter
that cannot expose this observation reports it as `unknown`.

Erasure has no positive replacement, but still needs negative and preservation checks. The triad defeats two cheap tricks: adding a new fact while still retrieving the old one, and “fixing” the problem by wiping the whole profile.

## Three operations, three meanings

### Correct

The earlier proposition was wrong for some or all of the interval it claimed to describe.

Example: “My office is in Paris” was a mistaken extraction of “My customer is in Paris.” The false history should not be preserved merely because it appeared first.

### Supersede

The earlier proposition was true, then stopped being true.

Example: “I am vegetarian” was true through July and false from August. Present-day recommendations use the new state; correctly scoped historical questions may retain the old one.

### Erase

The proposition must no longer be retained or used, whether or not it was true. A receipt must not preserve the secret it claims to erase.

Conflating these operations is dangerous: correction-as-supersession preserves a false claim, supersession-as-correction rewrites history, and erasure-as-update may retain sensitive content in an audit trail.

## Four parts

### 1. Roots and signed errata

Every exported fact, preference, event, procedure, or source bundle receives:

- an opaque, stable root ID;
- the owner's verification key;
- an errata endpoint or equivalent return address;
- a semantic scope and, when relevant, a validity interval.

Use stable IDs rather than pretending natural-language claims have universal hashes. An append-only, monotonically sequenced feed publishes authorized corrections, supersessions, and erasures. Importers reject invalid signatures, rollback, sequence gaps, conflicting events, and ambiguous targets. Payloads may be encrypted per importer; public metadata need not reveal the fact.

### 2. Importer lineage

At import time, an adapter records which local artifacts descend from each root:

- raw turns and files;
- extracted facts and profiles;
- summaries and reflections;
- embeddings and vector entries;
- knowledge-graph nodes and edges;
- cached context blocks;
- downstream exports.

Exact lineage is the primary mechanism. Semantic search may find unregistered residue, but approximate matches require review; they must not be silently mutated. An adapter that cannot enumerate a store says so.

### 3. Quarantine and rebuild engine

When a valid erratum arrives, the retrieval gate blocks the root and its known descendants **before** slow repair begins. The engine then retires, edits, or rebuilds each affected artifact.

If a summary mixes “vegetarian,” “quiet restaurants,” and “moderate budget,” the engine rebuilds it from the two retained inputs plus the replacement. It does not delete the whole summary or append a contradictory sentence. Build recipes may record inputs, model, prompt or template, tools, policy versions, and parameters. This improves auditability without promising bit-for-bit reproducibility from a nondeterministic model.

### 4. Repair receipts

After repair, the importer returns a signed receipt bound to:

- the erratum and its sequence number;
- the importer's pre-repair and post-repair state roots;
- the stores inspected and descendants addressed;
- the repair-triad tests and their results;
- adapter, model, and policy versions;
- unresolved stores and limitations.

The signature authenticates the importer and the bytes it attested. It does **not** prove the importer was truthful or that a language model can never express the retired idea again.

## The loop: observe → quarantine → rebuild → test → attest

1. **Observe.** Verify the owner, authorization, sequence, scope, and operation.
2. **Quarantine.** Deny the root and known descendants at every declared retrieval gate. If this cannot be done, fail closed for affected uses.
3. **Rebuild.** Traverse exact lineage, retire invalid artifacts, and reconstruct mixed artifacts from valid inputs.
4. **Test.** Run structural checks plus negative, positive, and preservation probes. Reintroduce stale exports to test recontamination.
5. **Attest.** Commit the repaired snapshot only when policy permits, then return a coverage-aware receipt.

An importer that re-exported the root must forward the erratum to its registered downstream importers or preserve the owner's endpoint. Otherwise the correction chain stops at the next copy.

Here is the semantic core, not a finished wire standard:

```yaml
erratum: err_01JZ
sequence: 42
target_root: mem_01HX
operation: supersede
valid_from: 2026-08-01T00:00:00Z
postconditions:
  negative: current meals do not assume vegetarian-only choices
  positive: current-diet answers use the replacement state
  preserve: quiet restaurants and budget remain active
receipt:
  bind: [erratum, pre_state_root, post_state_root]
  stores:
    profile: verified
    summary: verified
    vector_index: verified
    prompt_cache: unknown
  triad: {negative: pass, positive: pass, preserve: pass}
  overall: partial
```

The receipt is `partial` even though all executed probes passed: a required store was unobservable.

## Honest coverage

Use only four terminal coverage results:

| Result | Meaning |
|---|---|
| `verified` | The declared store was enumerated, repaired, and passed required checks. |
| `partial` | Some relevant state was handled, but coverage or verification was incomplete. |
| `unknown` | The store may contain relevant state but exposes no adequate interface. |
| `failed` | Relevant state was found and could not be safely repaired or quarantined. |

`pending` is a lifecycle state, not a successful coverage result. A store absent from the root's required scope is omitted rather than congratulated as “not applicable.” Aggregate success requires every required store to be `verified`.

Lineage supplies **structural evidence**: registered descendants were addressed, invalid retrieval keys were gated, rebuilt artifacts use authorized inputs, and the event sequence is intact. Probes supply **behavioral evidence**: the stale belief did not reappear in a declared sample, the replacement activated, and collateral facts survived.

Neither is a mathematical proof of semantic absence. Tests must record their scope, model, prompts, and uncertainty. Prefer deterministic inspection where possible and an independently configured verifier for model-graded behavior.

## Build the smallest convincing version

Use ordinary files first:

```text
llm-errata/
  AGENTS.md
  identity/owner.pub
  feeds/errata.jsonl
  registry/importers.yaml
  registry/lineage.jsonl
  adapters/{markdown,vector,opaque}/
  tests/{cases.yaml,conformance/}
  receipts/
  index.md
  log.md
```

`index.md` is the human-readable status page. `log.md` is append-only operational history. `AGENTS.md` tells the coding agent how to classify the three operations, request authorization, handle secrets, run tests, and refuse unsupported completeness claims.

The first demo should have one controller and three deliberately different stores:

1. a file-backed Markdown memory that exposes exact lineage;
2. an open-source vector store with retrievable metadata;
3. an opaque adapter that can only report `unknown`.

Export one root into all three. Derive a mixed summary and vector. Then run one correction, one temporal supersession, one erasure, a rollback attack, a mixed-source rebuild, and a stale reimport. The demo succeeds only if quarantine precedes repair, preserved facts survive, and the opaque adapter prevents a green aggregate result.

After the behavior works, publish a small schema, CLI, adapter contract, and conformance corpus. Compatibility should come from profiling existing primitives rather than inventing another base memory format.

## Invariants and boundaries

- **Authorization:** only the owner or an explicit delegate may issue an erratum. A forged correction is durable memory poisoning.
- **No notice-time recall:** once a valid erratum is observed, known stale descendants stay quarantined until policy allows a repaired snapshot.
- **No silent completeness:** missing lineage, inaccessible stores, backups, provider logs, model weights, screenshots, and copied prose with severed lineage remain `partial` or `unknown`.
- **No secret in evidence:** use content-free commitments; do not repeat erased values in receipts.
- **No semantic overclaim:** signatures authenticate statements; probes estimate behavior; neither proves total non-influence.
- **No accidental history rewrite:** validity intervals and the correct/supersede distinction are first-class.
- **No central surveillance requirement:** the feed can be a local Git repository, authenticated endpoint, or privacy-preserving sync service. Importer registration remains minimal and user-controlled.

Track four product metrics: stale-behavior rate, collateral retention, quarantine latency, and coverage honesty. Reconsider the idea if importers will not preserve root IDs and endpoints, lineage becomes too expensive through common summarization pipelines, semantic tests cannot beat model variance, or interoperable vendor synchronization supplies equivalent descendant-repair receipts first.

## What the research eliminated

The search deliberately broadened, collided, narrowed, and repeated. These adjacent ideas are already being tackled:

| Existing area | Representative public work | Why LLM Errata is narrower |
|---|---|---|
| Portable memory and governed context | [Portable Agent Memory](https://arxiv.org/html/2605.11032v1), [Portable AI Memory v1](https://portable-ai-memory.org/spec/v1.0/), [EngramSpec](https://engramspec.org/), [ApertoMemory draft-02](https://datatracker.ietf.org/doc/draft-ferro-apertomemory/02/) | Portable Agent Memory uses a Merkle-DAG protocol; Portable AI Memory defines exported objects, incremental deltas, and optional signatures; Aperto signs and encrypts objects but leaves synchronization out of scope. EngramSpec is the closest transport collision: signed cross-runtime context, a live correction endpoint, pull-based incremental diffs with tombstones, conformance tiers, and a reference implementation. None of the reviewed sources also requires descendant repair, the repair triad, and a coverage-aware callback. |
| Local correction and receipts | [Inspeximus](https://github.com/DanceNitra/inspeximus), [Shomei overview](https://shomei.ai/how-it-works/), [Shomei API](https://shomei.ai/docs/http-api/), [Shomei governance](https://shomei.ai/docs/governance-and-receipts/) | Shomei already offers source-linked, policy-gated recall; governed correction/update; derived-artifact lineage; erasure cascades; external-delete-pending states; and bounded, signed governance receipts. Inspeximus implements keyed correction, echo guards, revert, residue scans, and erasure evidence, but its README says raw conversational prose is rarely keyed reliably, so supersession mostly does not fire there. The remaining gap is the full cross-importer feature conjunction. |
| Dependency-aware unlearning and rebuild | [TMLS Agent Memory and State](https://www.tmls.nyc/research/agent-memory-state), [Agentic Unlearning](https://arxiv.org/html/2602.17692v1), [MaRS](https://arxiv.org/html/2512.12856v1), [W3C PROV](https://www.w3.org/TR/prov-dm/) | Derivation graphs, invalidation, erasure propagation, and regeneration are established. LLM Errata does not claim those mechanisms; it makes them an importer duty after a cross-boundary update. |
| Cross-recipient lifecycle notification | [vCon Lifecycle using SCITT](https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01), [SCITT architecture](https://datatracker.ietf.org/doc/rfc9943/), [IAB deletion framework](https://github.com/InteractiveAdvertisingBureau/Data-Subject-Rights/blob/main/Data%20Deletion%20Request%20Framework.md) | This is the strongest formal standards/control-plane collision. The individual vCon draft defines sent/received events, amendments, consent changes, deletion or expiry notifications, and recipient acknowledgments backed by SCITT inclusion receipts. Inclusion or acknowledgment does not establish repair of AI summaries, vectors, graphs, and behavior. |
| Revocation and provenance updates | [W3C credential status and refresh](https://www.w3.org/TR/vc-data-model-2.0/#refreshing), [W3C Bitstring Status List](https://www.w3.org/TR/vc-bitstring-status-list/), [C2PA 2.4](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html) | Exported objects can expose status, refresh, revocation, and signed update manifests. They do not impose AI-memory-specific descendant repair or the repair triad. |
| Derived-data deletion | [Palantir US10956406B2](https://patents.google.com/patent/US10956406B2/en) and long-term-memory security research ([survey](https://arxiv.org/html/2604.16548v1)) | Rebuilding derived data after source deletion and testing for reappearance are not new. The candidate is the interoperable semantic conformance profile, not either primitive. |
| **Remaining feature conjunction** | **No exact public implementation found in the reviewed sources required all four together** | **Post-export update delivery; importer-side quarantine and repair of the known descendant closure; negative, positive, and preservation tests; and an authenticated, coverage-truthful callback bound to the erratum and pre/post state.** |

The callback requirement contains two independent properties. **D1,
authenticity:** a valid signature binds the importer to the event, pre/post
state, stores, aggregate, and limitations. **D2, coverage truthfulness:** those
signed coverage claims match the declared required scope and do not upgrade
missing, opaque, skipped, or failed evidence.

Signature validity authenticates the importer and receipt bytes; it does not establish that the reported coverage is truthful.

Coverage truthfulness requires the signed stores, aggregate, and limitations to match the declared required scope without upgrading missing or opaque evidence.

An empty enumeration is not evidence of complete lineage. A required adapter
may report `verified` for an empty root scope only when it also establishes a
root-specific write-time or audited lineage authority; otherwise the signed
store result is `unknown` with a limitation.

A durable checkpoint records adapter-supplied quarantine coverage; final repair cannot upgrade a worse checkpoint result.

The published adapter contract must expose every controller and repair operation without hidden reference-ledger dependencies.

A receipt establishes the signed event accepted by one importer. Importer-local
sequence checks detect conflicts visible in that view, but cannot establish
global owner non-equivocation across split views without an external witnessed
or append-only log.

The broad candidates were rejected: “a personal LLM wiki,” “portable memory,” “a memory makefile,” “verified forgetting,” “a temporal contradiction ledger,” and “self-correcting memory.” A signed post-export update feed was also rejected: EngramSpec already provides cross-runtime corrections and incremental diffs, while vCon Lifecycle/SCITT and downstream-deletion frameworks cover event and acknowledgment control planes. The surviving combination is still a synthesis of known mechanisms, so its strongest defensible claim is product and conformance design—not fundamental invention.

The strongest AI-memory transport collision is [EngramSpec](https://engramspec.org/). The strongest formal standards/control-plane collision is the individual [vCon Lifecycle using SCITT draft](https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01), which records cross-recipient lifecycle events and acknowledgments backed by SCITT transparency receipts. LLM Errata profiles a boundary neither source normatively specifies: a notice reached an importer; now what must happen to the importer's locally derived AI memory, and what evidence must come back?

Likely building blocks include Portable AI Memory or Aperto for exported objects, vCon/SCITT for cross-boundary events, and PROV-like lineage. The proposed contribution is the missing conformance profile tying them together around quarantine, reconstruction, the repair triad, and honest substrate coverage.

## Research method and limits

The public search through 2026-08-01 covered official product documentation and adoption studies; papers and preprints on agent memory, unlearning, temporal belief revision, provenance, security, and portability; open-source and commercial memory systems; IETF, W3C, C2PA, and downstream-deletion standards; exact-phrase and mechanism-combination searches; and a targeted patent-keyword review. Candidate ideas were discarded whenever a close implementation or normative design appeared, and the survivor was red-teamed against its closest local and cross-recipient systems.

Internet research cannot prove a negative. Private systems, unpublished work, non-English material, poorly indexed repositories, and recent patent filings may have been missed. The patent review was not a claim chart, patentability opinion, or freedom-to-operate analysis. The correct conclusion is:

> **No exact public implementation or normative profile was found for the reviewed four-part conjunction—not “nobody has tackled this.”**

For the reproducible public decision record, query families, rejected-candidate ledger, and falsifiers, see [RESEARCH.md](RESEARCH.md). For the feature-level collision analysis, see [PRIOR_ART.md](PRIOR_ART.md).

## Authorship and research disclosure

The concept was developed under Thomas Rainer Willner's direction using AI-assisted research, candidate generation and rejection, drafting, prior-art comparison, fact-checking, and adversarial review. Thomas Rainer Willner is the publishing author and accepts responsibility for the final claims after completing the human review checklist in [PUBLISHING.md](PUBLISHING.md).
