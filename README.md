# LLM Errata

[![validate](https://github.com/thomaswillner/llm-errata/actions/workflows/validate.yml/badge.svg)](https://github.com/thomaswillner/llm-errata/actions/workflows/validate.yml)

**A vendor-neutral proposal for making corrections follow AI memory after it has been copied.**

> **An imported memory is a dependency, not a copy.** When its source changes, the importer should quarantine its known descendants, rebuild them from valid inputs, and report anything it could not verify.

> **If an AI accepts a memory, it should also accept responsibility for its future errata.**

## Publication status

| Field | Value |
|---|---|
| Author | Thomas Rainer Willner |
| Version | 0.3.0 |
| Status | Public concept proposal / Request for Comment |
| Published | 2026-08-07 |
| Research reviewed through | 2026-08-01 |
| License | Personal use only, see [LICENSE](LICENSE). Releases up to 0.2.0 were Apache-2.0. |

This is an independent proposal. It does not represent the position of the author's employer or any organization referenced in this repository.

## The problem

AI memory is beginning to move between assistants, agents, applications, and vendors. Portability is useful, but every import creates another copy that may outlive the truth from which it originated.

Suppose a personal assistant records that Alice is vegetarian. Alice exports that memory to a travel planner and a work-event assistant. Each importer produces local summaries, embeddings, profiles, and caches. Months later, Alice says the preference has ended. Updating the original assistant does not necessarily update any of those descendants.

Existing work covers important parts of the lifecycle:

- portable and cross-runtime memory formats;
- signed corrections and incremental synchronization;
- local lineage, deletion, and regeneration;
- cross-recipient notifications and acknowledgments;
- provenance, revocation, and cryptographic receipts.

The missing obligation is what an importer must do **after** it receives the update.

## The proposal

LLM Errata defines a conformance pattern with five verbs:

```text
observe → quarantine → rebuild → test → attest
```

1. **Observe:** authenticate a correction, supersession, or erasure for an imported memory root.
2. **Quarantine:** block that root and its known local descendants before further recall.
3. **Rebuild:** retire invalid artifacts and reconstruct mixed artifacts from still-valid inputs.
4. **Test:** run the repair triad across the declared stores and behavioral scope.
5. **Attest:** return a signed, coverage-aware receipt bound to the erratum and the importer's pre-repair and post-repair state.

An importer that cannot inspect a relevant cache or derived store reports `unknown`. It does not silently turn incomplete coverage into success.

## The repair triad

Every repair is evaluated against three postconditions:

| Check | Required result |
|---|---|
| Negative | The retired proposition does not reappear in the declared tests. |
| Positive | The replacement is active where it should be. |
| Preservation | Unrelated retained memory still works. |

Erasure has no positive replacement but still requires negative and preservation checks. These tests provide scoped evidence, not mathematical proof that a model can never express the retired proposition again.

## Correct, supersede, and erase are different

- **Correction:** the earlier proposition was wrong.
- **Supersession:** the earlier proposition was true and later stopped being true.
- **Erasure:** the proposition must no longer be retained or used, whether or not it was true.

This distinction prevents false history from being preserved, valid history from being rewritten, and secrets from surviving as audit evidence.

## Why this could affect millions

OpenAI reported more than [800 million weekly ChatGPT users](https://openai.com/index/the-state-of-enterprise-ai-2025-report/) by December 2025. A separate [OpenAI/NBER consumer-use study](https://openai.com/index/how-people-are-using-chatgpt/) found that practical guidance, information seeking, and writing dominate ordinary use. In a 2026 survey of 6,000 digital workers, [Glean reported](https://www.glean.com/work-ai-institute/reports/work-ai-index) that, among its respondents who use AI, 77% used multiple AI tools weekly and 33% used four or more.

Those datasets do not measure the same population, and they do not establish how many users already export memory. They do establish the scale of persistent AI use and multi-tool fragmentation. Even a small affected fraction would represent millions of users.

## What is—and is not—claimed as new

This repository does **not** claim to invent portable memory, correction feeds, provenance graphs, dependency-aware deletion, regeneration, revocation, behavioral testing, or signed receipts.

The narrow research conclusion is:

> **No exact public implementation found in the reviewed sources required all four together: post-export update delivery; importer-side quarantine and repair of the known descendant closure; negative, positive, and preservation tests; and a signed, coverage-aware callback bound to the erratum and pre/post state.**

This is a novel synthesis with an apparently unimplemented conformance gap. It is not a claim of patentability, a “world first,” or freedom to operate. [EngramSpec](https://engramspec.org/) is the strongest AI-memory transport collision. The individual [vCon Lifecycle using SCITT draft](https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01) is the strongest formal standards/control-plane collision. [Shomei](https://shomei.ai/docs/governance-and-receipts/) and [Inspeximus](https://github.com/DanceNitra/inspeximus) are the closest local governance and correction collisions.

See [PRIOR_ART.md](PRIOR_ART.md) for the feature-level comparison and [RESEARCH.md](RESEARCH.md) for the reproducible public decision record.

## Repository map

| File | Purpose |
|---|---|
| [prototype/](prototype/README.md) | **Runnable demo and CLI.** Three stores, one supersession, a receipt that refuses to go green. |
| [spec/](spec/README.md) | The wire schema for errata and receipts, with conformance vectors. |
| [IDEA.md](IDEA.md) | Complete, copy-pasteable idea file and architecture. |
| [RESEARCH.md](RESEARCH.md) | Research scope, search protocol, rejected candidates, limits, and falsifiers. |
| [PRIOR_ART.md](PRIOR_ART.md) | Feature-collision matrix and source-by-source comparison. |
| [THREAT_MODEL.md](THREAT_MODEL.md) | What the design defends against, what it does not, and what it can only make visible. |
| [HARD_PROBLEMS.md](HARD_PROBLEMS.md) | Screen of the three problems the proposal declares out of scope, with verdicts. |
| [SOURCES.md](SOURCES.md) | Pinned source record: versions, commits, access dates, and the sources that remain unpinned. |
| [ROADMAP.md](ROADMAP.md) | Smallest credible implementation, acceptance gates, and standards path. |
| [AGENTS.md](AGENTS.md) | Model-agnostic rules for coding and research agents working in this repository. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to challenge the novelty boundary, correct evidence, or propose an implementation. |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | How disagreement about evidence is expected to be handled. |
| [SECURITY.md](SECURITY.md) | Security-reporting scope and private-reporting guidance. |
| [CITATION.cff](CITATION.cff) | Citation metadata. |
| [CHANGELOG.md](CHANGELOG.md) | Public version history, including claims that were narrowed or retired. |
| [PUBLISHING.md](PUBLISHING.md) | Exact repository settings, review gates, release text, and announcement wording. |
| [REVIEW_REQUEST.md](REVIEW_REQUEST.md) | Required record for independent conformance and security/distributed-systems review. |
| [INDEPENDENT_IMPLEMENTATION.md](INDEPENDENT_IMPLEMENTATION.md) | Call and evidence requirements for independently authored adapters. |
| [PHASE3_SYSTEMS.md](PHASE3_SYSTEMS.md) | Nominations for future authorized three-system synthetic-data experiment. |
| [docs/PUBLICATION_STRATEGY.md](docs/PUBLICATION_STRATEGY.md) | Evidence-bounded publication channels and canonical announcement copy. |

## Verifying this repository

Everything is Python standard library only. There is nothing to install.

```bash
make check    # structure/metadata, bounded claim, readiness-evidence honesty, and self-tests
make links    # liveness of every cited external URL (needs network)
```

`make check` runs four validation components because they answer different questions:

| Command | Question | Failure means |
|---|---|---|
| `make lint` | Are repository structure and metadata well formed? | A file, link, encoding, fence, or metadata field is wrong. |
| `make claim` | Does the documentation still state the bounded claim? | An anchor sentence, the quarantine-before-repair ordering, or the novelty boundary has been altered. |
| `make readiness` | Is the recorded readiness evidence structurally honest and synchronized with the human matrix? | The ledger is malformed, evidence is insufficient for a recorded status, or the matrix contradicts the ledger. |
| `make test` | Do those checkers reject what they claim to reject? | A checker has stopped catching a fault it is supposed to catch. |

The self-tests exist because a check that has never failed has not been shown to
work. The self-tests build corpora that misstate the proposal — an inverted
quarantine ordering, an asserted world first — and require the guard to reject
each one.

Readiness-check exit `0` validates structural honesty of the recorded evidence.
It does **not** mean `PROD_READY`; consult the ledger and human matrix for the
current verdict.

`scripts/claim_guard.py` distinguishes *failed* (exit `1`) from *inconclusive*
(exit `2`, meaning a guarded file was missing or unreadable, so the claim was
never evaluated). Inconclusive is not a pass. `make` reports its own exit `2`
for any failed recipe, so `make claim` prints which of the two occurred; a
script that needs to branch on the distinction should call the guard directly.

## Run it

```bash
make demo        # the narrated three-store scenario
make cli-demo    # the same lifecycle through the errata command line
```

Standard library only, no network, no API key. It exits `2` on purpose: both
inspectable stores are repaired, all three probes pass, and the aggregate is
still `partial` because one required store cannot show its own state.

That refusal is the point. Remove the opaque store and the same repair reports
`verified` — there is a test asserting exactly that, so the non-green result
cannot be read as a bug. See [prototype/README.md](prototype/README.md).

## Current maturity

Version 0.3.0 is an experimental conformance proposal and tested reference implementation, not a production protocol or proof of interoperability. Phase 1 is implemented; Phase 2 remains incomplete. Item 6 adds provider-neutral semantic probes with deterministic fixtures and recorded verifier configuration, while explicit `errata quarantine` CLI support and vectors for key rotation, concurrent events, invalid targets, and confidentiality remain open. Receipt-binding vectors exist for state roots but coverage remains partial. G2 remains `BLOCKED` pending internal Phase 2 completion and a dated independent review of the complete conformance surface.

Current production-readiness verdict: **NOT_PROD_READY**. [ROADMAP.md](ROADMAP.md) defines implementation and kill criteria. [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) records the human evidence matrix and continuous enforcement boundaries.

## Review requests

The most useful contributions are:

1. a public system or specification that already implements the complete four-part conjunction;
2. a correction to a documented feature in the prior-art matrix;
3. an attack that breaks quarantine, lineage, receipt integrity, privacy, or coverage honesty;
4. a smaller design that achieves the same user outcome;
5. a concrete adapter or conformance test.

Please use the evidence requirements in [CONTRIBUTING.md](CONTRIBUTING.md), [REVIEW_REQUEST.md](REVIEW_REQUEST.md), and [INDEPENDENT_IMPLEMENTATION.md](INDEPENDENT_IMPLEMENTATION.md). A convincing prior-art collision should narrow or retire the claim rather than be argued away.

## Authorship and research disclosure

The concept was developed under Thomas Rainer Willner's direction using AI-assisted research, candidate generation and rejection, drafting, prior-art comparison, fact-checking, and adversarial review. Thomas Rainer Willner is the publishing author and accepts responsibility for the final claims after completing the human review checklist in [PUBLISHING.md](PUBLISHING.md).

The public research record exposes the decision criteria and evidence trail. It does not claim to reproduce private model reasoning or hidden chain-of-thought.

## License

Copyright © 2026 Thomas Rainer Willner.

Licensed for personal, non-commercial evaluation and study. See [LICENSE](LICENSE).

You may read, run, study, quote, and cite this work. Commercial use,
redistribution, derivative works, and implementing the specifications in
`spec/` require written permission, which is not unreasonably withheld for
research and standards work.

Version 0.2.0 and earlier were published under the Apache License 2.0. That
grant is irrevocable for those releases and is not withdrawn here.

Third-party files under `spec/vendor/` keep their own licences.
