# Hard Problems: Three Declared Out-of-Scope Items, Re-Screened

**Research date:** 2026-08-07

**Scope:** The three problems [RESEARCH.md](RESEARCH.md) places outside the LLM Errata claim, re-screened against public primary sources with emphasis on work published after the 2026-08-01 cutoff of this repository.

**Evidence boundary:** This is a screen of public sources. It cannot prove a negative. A verdict of `STILL OPEN` means no reviewed public work solved the problem, not that no solution exists.

## The three questions

| # | Question | Where the proposal excludes it |
|---|---|---|
| 1 | Can a retired proposition be shown unexpressible and unreconstructible, beyond behavioural sampling? | RESEARCH.md § Excluded; IDEA.md § Invariants, "No semantic overclaim" |
| 2 | Can exact provenance survive ordinary summarisation and embedding? | RESEARCH.md § Falsifiers, "lineage is routinely severed during summarization" |
| 3 | Can a behavioural probe separate a genuine repair from model nondeterminism? | RESEARCH.md § Falsifiers, "behavioral probes cannot distinguish repair from ordinary model variance" |

Every citation below was fetched and its title confirmed against the arXiv metadata API on 2026-08-07. Version numbers are the latest available on that date. Where a source is cited for behaviour rather than existence, the specific measurement is stated.

---

## 1. Proving semantic absence

### VERDICT: STILL OPEN

No reviewed work verifies that a retired proposition can no longer be expressed or reconstructed. The substrate sub-problem, whether specific bytes still exist in a specific store, has advanced materially. The semantic problem has not been touched.

### Strongest specific public work

**Ghost Vectors: Soft-Deleted Embeddings Remain Reconstructible in HNSW Vector Databases**, [arXiv:2606.18497v1](https://arxiv.org/abs/2606.18497v1), 2026-06-16. Chakraborttii, García Alvarado, Abdulofizova, Dwivedi.

It is the strongest work here because it attacks the assumption on which any `verified` coverage claim for a vector store currently rests, and then supplies the only concrete route past it.

### What it achieves

The setting is a RAG deployment on an HNSW-backed vector store after a user deletion request. The attack reads the on-disk index files directly and never touches the query API or any defence layered above it.

Measured across three independent systems, ChromaDB on hnswlib, FAISS `IndexHNSWFlat`, and Weaviate 1.26.6 in embedded mode, soft-deleted vectors remained physically present in all three. FAISS `IndexHNSWFlat` exposes no delete method at all. Vec2Text inversion of extracted vectors reached ROUGE-L 0.207 on ChromaDB and 0.167 on FAISS, recovering 25.5% of person names. On structured clinical records, recovery of patient age and gender markers reached 100%. On facial embeddings, top-1 identity recovery reached 99%.

The paper's own framing of the governance failure is the part that matters most here: after a soft delete, a controller checking only the API can "truthfully report that the API has no records for that ID" while the embedding sits unchanged on disk.

The countermeasure, Epoch Key Rotation, encrypts vectors with AES-256-CTR and destroys the key on deletion. Measured recovery falls to ROUGE-L 0.000, processing takes 2.5 ms for 500 records, and the operation emits an ECDSA-signed proof object verifiable against a registered public key. The security argument is a reduction: under IND-CPA security of AES-256-CTR and actual erasure of the epoch key, no probabilistic polynomial-time adversary gains non-negligible semantic recovery advantage.

### What it does NOT achieve

The guarantee is about bytes, not meaning. It says a specific ciphertext cannot be inverted. It says nothing about whether the proposition is still derivable from a summary, a graph edge, a retained sibling record, or model weights.

The paper states two further boundaries itself. First, the guarantee collapses entirely if the epoch key remains accessible anywhere on disk. Second, content erasure leaves the ghost node in the HNSW graph; a complete defence also requires graph repair by re-linking the deleted node's predecessors to its successors, which the paper does not implement.

### What this would change for LLM Errata

Three concrete consequences, one of which is a tightening rather than an upgrade.

**A required tightening.** A vector adapter must not report `verified` on the strength of an API response. This work shows an honest adapter can be honest and wrong at the same time. The conformance profile should require either substrate-level attestation or a downgrade to `partial`, and the receipt should record which of the two it is. This closes a hole the current design does not name.

**A route from `partial` to `verified` for one surface.** Epoch Key Rotation's signed proof object is directly reusable as a receipt component for the erasure case. Bound to the erratum identifier, it turns an unverifiable claim into a checkable one for vector content, though not for the graph structure.

**A second route, for retrieval rather than storage.** [V3DB, arXiv:2603.03065v2](https://arxiv.org/abs/2603.03065v2), 2026-03-05, produces a succinct zero-knowledge proof that a top-k result is exactly what the published search semantics yield on a committed corpus snapshot, without revealing the corpus. LLM Errata's receipt already binds pre-repair and post-repair state. Binding snapshot commitments instead of opaque state hashes would let an origin verify the post-repair index without inspecting it. Verification is millisecond-level; proving is not, so this is a design option rather than a default.

Nothing found lets an opaque store move from `unknown` to `verified`. Nothing found supports a claim of semantic absence. The `unknown` state and the "no semantic overclaim" invariant both survive intact.

### Runners-up

- **Auditing Forgetting in Limited Memory Language Models**, [arXiv:2607.00605v1](https://arxiv.org/abs/2607.00605v1), 2026-07-01. Across 12,228 alias-closure deletions, parametric leakage was near zero and the surviving residue, 0.7% to 13.6% depending on adversarial database topology, was reconstituted almost entirely from near-neighbour retrieval; the deletion boundary is drawn by the database administrator, not the model.
- **Auditing of Unlearning Algorithms**, [arXiv:2607.05898v1](https://arxiv.org/abs/2607.05898v1), 2026-07-07. Computes data-dependent lower bounds on the unlearning parameter via membership inference; it can falsify an unlearning claim but by construction cannot certify one.
- **Is Agent Memory a Database? Rethinking Data Foundations for Long-Term AI Agent Memory**, [arXiv:2605.26252v1](https://arxiv.org/abs/2605.26252v1), 2026-05-25. Formalises Governed Evolving Memory with six correctness conditions including dependency consistency and provenance preservation, and argues that no record-level system can satisfy them regardless of storage model. It contains no cross-system delivery and no attestation.

---

## 2. Lineage through summarisation

### VERDICT: MATERIALLY ADVANCED

Exact span-level provenance still does not survive a model's summarisation step. The field has stopped trying to make it survive and has instead established, with measurements, what must be retained at write time for a later correction to take effect at all. That reframing is the advance, and it is directly usable.

### Strongest specific public work

**Reclaim Evaluation: A Lossy Memory Is Worse Than an Empty One**, [arXiv:2606.25449v5](https://arxiv.org/abs/2606.25449v5), v1 2026-06-24, v5 2026-07-21. Alex Kwon.

### What it achieves

The design is a controlled correction experiment, not an attribution method. Induce a known drift, compress the memory at a fixed token budget, deliver a correction naming the error, then score exact recovery. Scoring is judge-free, which removes the evaluator as a confound.

Holding the budget fixed and varying only *what the compression keeps* isolates correctability from both capability and size. The reported result is a clean separation: where the compressed memory retained the source, a re-derivation basis, correction succeeded, reaching 1.00 exact recovery on the strongest model tested; where the memory retained the conclusion and dropped the source, recovery was 0.00 for every model tested, including frontier ones. An 8B model and a frontier model fail at the same place.

The stated remedy is a one-line write policy: keep the recomputable source, drop the re-derivable conclusion. A length-matched control rules out the explanation that the fix is simply more text. The paper reports the failure compounding through memory loops and replicates across three deployed memory systems, MultiWOZ dialogue, and tau-bench.

### What it does NOT achieve

It does not preserve span-level provenance, and does not claim to. It measures a downstream consequence of losing the derivation basis, not the derivation itself.

The remedy is explicitly bounded to cases where the source is compact and identifiable. Long, diffuse, or multi-source derivations are outside the demonstrated regime. Whether a claim's source is compact is itself a judgement made at write time, before the correction exists.

### What this would change for LLM Errata

This is the most consequential finding in this document for the proposal's design, and it changes a coverage rule rather than adding a mechanism.

The proposal currently treats a descendant with severed lineage as a coverage problem, resolved as `partial` or `unknown`. Kwon's measurement says that is too generous for one specific case. A summary descendant that retained a conclusion but not its re-derivation basis is not merely unverifiable; it is demonstrably uncorrectable, at 0.00, regardless of model capability. That is a `failed` condition under the repo's own definition, relevant state found and not safely repairable, not a `partial` one.

Two further changes follow.

**A write-side conformance requirement becomes justifiable.** LLM Errata could require that a store declaring itself repairable writes derivation bases rather than conclusions. This is currently an implicit assumption behind "rebuild from still-valid inputs"; there is now a measurement showing that rebuild is impossible without it.

**One falsifier becomes a measurable quantity.** RESEARCH.md lists "lineage is routinely severed during summarization" as a condition that should kill the product hypothesis. Reclaim evaluation supplies a harness for testing that condition against real importers rather than assuming it.

It does not upgrade any `unknown` to `verified`.

### Runners-up

- **MemLineage: Lineage-Guided Enforcement for LLM Agent Memory**, [arXiv:2605.14421v1](https://arxiv.org/abs/2605.14421v1), 2026-05-14. Combines an RFC 6962 Merkle log over Ed25519-signed entries with a weighted derivation DAG; note that the derivation edges are LLM-mediated and threshold-gated, so the cryptographic part is exact and the lineage part is not.
- **ProvenAI: Provenance-Native Traces of Evidence in Generated Answers**, [arXiv:2606.26449v1](https://arxiv.org/abs/2606.26449v1), 2026-06-24. Separates citation fidelity from measured per-document influence under leave-one-resource-out ablation and names the gap between them; a clean citation audit co-occurred with one cited source showing weak influence while seven uncited sources measurably shifted the output.
- **Chainwash: Multi-Step Rewriting Attacks on Diffusion Language Model Watermarks**, [arXiv:2605.05503v1](https://arxiv.org/abs/2605.05503v1), 2026-05-06. Detection of a watermark fell from 87.9% to between 14% and 41% after a single rewrite and to 4.86% after five chained rewrites, across four rewriter models. Watermarking should not be proposed as a lineage fallback.

---

## 3. Repair versus model variance

### VERDICT: MATERIALLY ADVANCED

The statistical machinery to separate a real behavioural change from sampling noise now exists, is proven, and is cheap enough to run continuously. It is the closest of the three problems to being closed. Nobody has applied it to memory repair, and the unsolved part has moved from statistics to probe design.

### Strongest specific public work

**Who Drifted: the System or the Judge? Anytime-Valid Attribution in LLM Evaluation Pipelines**, [arXiv:2606.15474v1](https://arxiv.org/abs/2606.15474v1), 2026-06-13. Yitao Li.

### What it achieves

The setting is continuous monitoring where a model judge scores a stream of interactions and a drop triggers an alarm. The ambiguity attacked is that a drop could mean the system got worse or the judge changed. That is structurally the same ambiguity as LLM Errata's: a probe result could mean the memory was repaired or the model simply sampled differently.

The construction has three parts: a fixed, human-labelled anchor set the current judge re-scores at a steady interleave; a betting e-process on the judge-versus-human gap; and a guard-window rule returning one of three verdicts, none, system, or judge. The paper proves anytime-validity, one-way identification such that only the judge can move the anchors, an attribution race condition requiring the anchors to out-run the process they guard, and process orthogonality.

Measured on two real judge changes: a silent version bump was attributed to judge drift in 60 of 60 runs with no misattribution, and a contaminating strict-prompt change was correctly attributed in 110 of 120 runs at guard width 300. The comparison that matters most is the baseline: an industry-default rolling z-test raised false alarms on 75% of drift-free streams. Results replicated on a second domain with nothing re-tuned. Monitoring cost was about 0.64 of strong-judging every item.

### What it does NOT achieve

It is a monitoring procedure over a stream, not a one-shot test of a discrete event. LLM Errata's repair triad runs once per erratum, so the sequential machinery has to be re-cast as a paired pre-repair versus post-repair comparison rather than adopted directly.

More fundamentally, it presumes a scored quantity that is known to move when the thing of interest moves. For a memory repair there is no such agreed quantity. The paper solves attribution, not the prior question of what to measure. The anchor set is human-labelled, which is an ongoing cost the proposal does not currently budget for.

### What this would change for LLM Errata

**The preservation check gains a construction.** The anchor-set idea maps onto the preservation postcondition almost directly: a fixed set of unrelated retained facts, scored before and after repair, where by construction only a repair fault can move them. The proposal currently states the preservation check as a goal without saying how to make it identifying.

**The negative check gains a stated error rate.** The proposal currently says a stale belief "did not reappear in a declared sample." With an e-process the receipt could instead carry a false-alarm bound and a stopping rule. That is a genuine tightening of a stated test, and it is the first thing in this document that makes `verified` mean more than it does today.

**Single-run probes should be inadmissible.** [On Randomness in Agentic Evals, arXiv:2602.07150v3](https://arxiv.org/abs/2602.07150v3), 2026-03-25, collected 60,000 agentic trajectories on SWE-Bench-Verified and found single-run pass@1 varying by 2.2 to 6.0 percentage points by run selection, with standard deviations above 1.5 points even at temperature 0, and trajectories diverging within the first few percent of tokens. A probe run once is not evidence about a repair.

None of this upgrades `unknown` to `verified`, because a store that cannot be enumerated cannot be probed either.

### Runners-up

- **CELEUS: Certifiable and Efficient LLM Evaluation via E-Processes**, [arXiv:2606.20820v2](https://arxiv.org/abs/2606.20820v2), 2026-06-26. Anytime-valid confidence intervals reaching target precision with 54% to 62% fewer evaluated samples, which makes per-erratum probing affordable rather than aspirational.
- **Resolution Diagnostics for Paired LLM Evaluation**, [arXiv:2605.30315v1](https://arxiv.org/abs/2605.30315v1), 2026-05-28. Reports a per-pair resolution ratio and shows that a widely used unpaired sample-size shortcut is wrong by roughly a factor of two in the close-comparison regime, a deficit inherited by three of five off-the-shelf calculators tested.
- **Ground Truth First: A Longitudinal Evaluation Instrument for Agent Memory**, [arXiv:2607.21962v1](https://arxiv.org/abs/2607.21962v1), 2026-07-24. Generates facts with validity intervals and source channels *before* any text exists, so gold answers are correct by construction; reports memory-architecture rankings inverting with history length under three replicates and cross-family re-judging.

---

## What is still genuinely unsolved

Four residues survive all three verdicts.

**Absence of a proposition, as opposed to absence of bytes.** Cryptographic erasure now proves a ciphertext is not invertible. Nothing proves a claim is not re-derivable from what was legitimately retained. Every result found points the same way: the residue after a correct deletion lives in the relationships between surviving items, not in the deleted item. Near-neighbour retrieval reconstituted deleted answers at up to 13.6%; a ghost node persists in the graph after its content is destroyed; a formal treatment argues that record-level correctness is the wrong unit. LLM Errata's `unknown` state is the correct answer here and should not be softened.

**Nobody has closed the loop across a trust boundary.** Every repair contract found stops at the edge of one store. MemoRepair defines withdrawal before repair and validated republication; GEM defines dependency consistency and provenance preservation as correctness conditions; AOEP-v0 scores governance obligations including quarantine state and rollback logging. None of them delivers the event to an independently operated prior recipient, and none returns evidence to an origin. That is still the gap, and it is now a better-populated neighbourhood than it was on 2026-08-01.

**Incomplete lineage fails non-linearly, and nothing degrades gracefully.** MemoRepair reports that dropping 1% of influence edges yields 17.7% leaked invalidated state, roughly an eighteen-fold amplification. Its own remedy is binary: withdraw or expose. No reviewed system has a middle state. This is the strongest quantitative argument for the proposal's refusal to allow a green aggregate while a required store is unresolved, and it should be cited in support of that rule rather than treated as an obstacle.

**Probe design, not probe statistics.** The hard remaining question in problem 3 is what quantity moves if and only if a repair happened. Anytime-valid inference will control the error rate of whatever is measured; it cannot tell you that the measurement is identifying. Nothing found addresses this for memory repair.

A fifth observation is not a research gap but an incentive one. No reviewed work penalises a system for reporting success when its substrate contradicts it. Coverage honesty currently has no adversary. Ghost Vectors is the closest thing to one, and it is a demonstration rather than a test suite.

## Consequences for the existing prior-art record

Nothing found requires the four-part conjunction in [PRIOR_ART.md](PRIOR_ART.md) to be withdrawn. Four additions and one correction are warranted.

| Work | Requirement touched | Why it belongs in the matrix |
|---|---|---|
| [MemoRepair, arXiv:2605.07242v1](https://arxiv.org/abs/2605.07242v1), 2026-05-08 | B, partly C | The closest B collision found anywhere. It is an explicit *contract* in which descendants are withdrawn before repair and republication is restricted to validated predecessor-closed successors, reducing invalidated-memory exposure from 69.8–94.3% to 0% *given complete influence provenance*. It independently arrives at quarantine-before-repair. It has no cross-system delivery, no preservation test, and no receipt. |
| [Governed Evolving Memory, arXiv:2605.26252v1](https://arxiv.org/abs/2605.26252v1), 2026-05-25 | B | Formal correctness conditions for dependency consistency and provenance preservation, with an argument that record-level stores cannot satisfy them. |
| [Always-On Agents / AOEP-v0, arXiv:2606.30306v1](https://arxiv.org/abs/2606.30306v1), 2026-06-29 | C | The closest *conformance-protocol* collision: a pilot evaluation contract scoring state mutation and recovery obligations, deterministically, rather than answer quality. |
| [memorywire, arXiv:2606.01138v3](https://arxiv.org/abs/2606.01138v3), v1 2026-05-31, v3 2026-07-17 | A | A vendor-neutral wire format with forget and expire operations and a cross-adapter conformance suite. Relevant to the "vendor-neutral" framing, not to importer repair. |

The correction: RESEARCH.md and SOURCES.md cite arXiv 2604.16548 under the short name "long-term-memory security survey." As of v2, 2026-06-11, the paper's title is *A Survey on Long-Term Memory Security in LLM Agents: Attacks, Defenses, and Governance Across the Memory Lifecycle*. SOURCES.md already records this title; RESEARCH.md's link text does not.

## Limitations

This screen shares every limitation recorded in [RESEARCH.md](RESEARCH.md) and adds several of its own.

Internet research cannot prove a negative. A `STILL OPEN` verdict is a statement about what was found, not about what exists. Private systems, unpublished work, non-English material, and equivalent mechanisms under different terminology were all outside reach.

Most sources here are preprints, several of them days or weeks old and none of them confirmed as peer-reviewed at the time of writing. Five of the seventeen cited works are solo-authored. Preprint measurements have not been independently replicated, and single-paper numbers should be treated as claims about one experimental setup rather than facts about the field.

Titles, authors, dates, and version numbers were confirmed against the arXiv metadata API. Detailed findings were read from the abstract and, where a specific mechanism or limitation is asserted, from the paper body. Claims sourced only from an abstract are stated at abstract granularity. One anomaly is recorded rather than resolved: arXiv reports [2606.27379v1](https://arxiv.org/abs/2606.27379v1) with a submission date of 2026-05-08, which is inconsistent with its 2606 identifier. Nothing above rests on that paper, and the discrepancy was not chased.

Two of the works cited above, Reclaim evaluation and Governed Evolving Memory, were reached by first finding them referenced in the Always-On Agents survey and then verifying them independently at source. That path biases toward what one survey team considered important.

Verdicts are judgements about a moving field, made on one day. `MATERIALLY ADVANCED` means a specific capability improved in a way that changes what the proposal can require or claim. It does not mean the underlying problem is close to solved. Where a finding would tighten the proposal rather than relax it, that is stated, because a screen that only ever finds good news is not a screen.
