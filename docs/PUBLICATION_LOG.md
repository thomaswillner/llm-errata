# Publication log

This log records publication and outreach evidence. It does not upgrade a
readiness gate. Last verified: 2026-08-12.

## GitHub public calls

| Surface | Public artifact | Status |
|---|---|---|
| Draft implementation and review surface | [PR #8](https://github.com/thomaswillner/llm-errata/pull/8) | Open draft, targeting `agent/prod-readiness`. |
| Independent review request | [Issue #4](https://github.com/thomaswillner/llm-errata/issues/4) and its [exact review target](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5269378077) | Open call for conformance, novelty, security, and distributed-systems review. |
| Targeted independent-review recruitment | [Inspeximus maintainer invitation](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5269444341) | Invitation to challenge the stated collision boundary; it is not external evidence. |
| Interested-party prior-art feedback | [Inspeximus maintainer response](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5271988057) | Conflict-disclosed preliminary feedback. Source verification confirmed `retract_lineage` as a stronger local quarantine/rebuild collision and narrowed the coverage comparison. The disclosed dogfood ratio was not independently reproduced. Maintainer offered a future scoped review, but explicitly does not meet G2 independence alone. |
| Targeted adapter recruitment | [Remnic invitation](https://github.com/thomaswillner/llm-errata/issues/5#issuecomment-5269523953) | Invitation to become a future independently authored adapter after Phase 2 completion; it is not technical evidence. |
| Targeted validator or system recruitment | [ai-memory-mcp invitation](https://github.com/thomaswillner/llm-errata/issues/5#issuecomment-5269524142) | Invitation to choose one separate role: independently produced validator or independently operated system; it is not technical evidence. |
| Targeted standards/collision review | [Portable Agent Memory invitation](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5269524323) | Invitation to test the conformance/standards collision boundary; it is not review evidence. |
| Targeted production-cryptography review | [Exact-build security-review request](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5269850937) | Published 2026-08-12 against qualification commit `27da4d09c79f03501b1302b9931be3561ff05e75`; requests independent side-channel, build, binding, and key-lifecycle review. Invitation only: G3 remains `BLOCKED`. |
| Targeted operated-system nomination | [Mem0 invitation](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269537990) | Invitation to nominate a future independently operated system; it is non-evidence and separate from validator authorship. |
| Targeted operated-system nomination | [Cognee invitation](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269538156) | Invitation to nominate a future independently operated system; it is non-evidence and separate from validator authorship. |
| Separate CODEOWNER volunteer recruitment | [PR #3 reviewer call](https://github.com/thomaswillner/llm-errata/pull/3#issuecomment-5269583214) | Invitation only; no volunteer or reviewer is recorded, no access was granted, and this call made no CODEOWNERS or protection change. It is not external evidence. |
| Dedicated CODEOWNER reviewer intake | [Issue #10](https://github.com/thomaswillner/llm-errata/issues/10) and [PR #3 linkage](https://github.com/thomaswillner/llm-errata/pull/3#issuecomment-5269972483) | Public volunteer intake for exact readiness-foundation commit `2d086611fed84fc542fda9d2ccc541530c0731f3`. Requires identity, background, relationship/conflict disclosure, and availability before the owner separately considers limited access or a reviewed CODEOWNERS amendment. Created 2026-08-12; grants no access and is not approval or external evidence. |
| Independent implementation call | [Issue #5](https://github.com/thomaswillner/llm-errata/issues/5) and its [implementation update](https://github.com/thomaswillner/llm-errata/issues/5#issuecomment-5269378246) | Open call for independently authored adapters and a separately produced validator. |
| Phase 3 system nominations | [Issue #6](https://github.com/thomaswillner/llm-errata/issues/6) and its [nomination update](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269378440) | Open nominations only; no experiment is authorized or underway. |
| GitHub Discussions announcement | [Discussion #9](https://github.com/thomaswillner/llm-errata/discussions/9), `LLM Errata needs falsifiers, independent reviewers, adapters, and real memory systems` | Created 2026-08-12 after Discussions was enabled (`has_discussions=true`). It links the repository, public issues, and PR #8; states Phase 2 incomplete, G2 `BLOCKED`, and `NOT_PROD_READY`. Publication/invitation only: no response yet and not external evidence. |
| Complete Phase 2 review target | Commit [`50e895fbfec544b16c94caa07bf2d1f4049a42e2`](https://github.com/thomaswillner/llm-errata/commit/50e895fbfec544b16c94caa07bf2d1f4049a42e2), digest `9547aec8328b601489dda067c6e62f287229b2b24a413dac2c9e7be98e429804` | Internal Phase 2 surface is complete and locally validated. Published for independent review; publication and internal tests do not satisfy G2. |

One targeted invitation now has the interested-party response recorded above;
it is not an acceptance of an independent reviewer role and does not satisfy
G2. No adapter, validator, operated-system approval, or CODEOWNER volunteer has
accepted.

The complete conformance review target is source commit
[`50e895fbfec544b16c94caa07bf2d1f4049a42e2`](https://github.com/thomaswillner/llm-errata/commit/50e895fbfec544b16c94caa07bf2d1f4049a42e2)
with canonical Phase 2 surface digest
`9547aec8328b601489dda067c6e62f287229b2b24a413dac2c9e7be98e429804`.
The digest was recomputed both from the checkout and from `git show` at that
commit with an exact match. Earlier source commit
[`35052868cde8b6f16fc6c20b4136ae0277f9a00e`](https://github.com/thomaswillner/llm-errata/commit/35052868cde8b6f16fc6c20b4136ae0277f9a00e)
and digest `a3133f759620ed942d6cd519d303c0be1554f0193b89e0a141c410aaf4c047b9`
remain historical pre-completion checkpoints, not current review targets.
The earlier implementation and outreach surface at commit
[`460883e093b52c99cec697443399da3e03ea2b40`](https://github.com/thomaswillner/llm-errata/commit/460883e093b52c99cec697443399da3e03ea2b40).
was the fixed head exercised by GitHub Actions successfully on [Python
3.11](https://github.com/thomaswillner/llm-errata/actions/runs/31619022097/job/94188870893)
and [Python
3.13](https://github.com/thomaswillner/llm-errata/actions/runs/31619022097/job/94188870819).
The live [PR #8](https://github.com/thomaswillner/llm-errata/pull/8) identifies
later publication-log-only commits and their own CI runs without requiring a
self-referential commit identifier in this file.

## Direct email outreach

| Recipient | Subject | Status |
|---|---|---|
| `founders@mem0.ai` | `Nomination request: Mem0 for an independent AI-memory interoperability experiment` | Sent 2026-08-12; no reply or acceptance recorded. Linked [Mem0 GitHub invitation](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269537990) remains nomination-only. |
| `info@topoteretes.com` | `Nomination request: Cognee for an independent AI-memory interoperability experiment` | Sent 2026-08-12; no reply or acceptance recorded. Linked [Cognee GitHub invitation](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269538156) remains nomination-only. |
| `linzh@memtensor.cn` | `Independent security review invitation: post-export repair of derived AI memory` | Sent 2026-08-12 to the corresponding author contact for cited [arXiv:2604.16548](https://arxiv.org/html/2604.16548v1); preliminary security critique requested, with no reply or acceptance recorded. A formal qualifying review must wait for the final Phase 2 surface. |
| `mgreen@cs.jhu.edu` | `Independent review inquiry: libsodium audit lineage for LLM Errata` | Sent 2026-08-12 to Matthew Green using the professional address published in his Johns Hopkins CV. Requested availability or referral for a scoped review of libsodium 1.0.22 audit delta, Ed25519 binding/build, side channels, and key lifecycle against exact qualification commit `27da4d09c79f03501b1302b9931be3561ff05e75`. Availability/scope inquiry only; no engagement, cost, access, or evidence established. |
| `contact@edgesecurity.com` | `Scope inquiry: independent libsodium integration and key-lifecycle review` | Sent 2026-08-12 using the address on Edge Security's official site after official libsodium documentation identified the company for cryptographic and implementation auditing of libsodium usage. Requested availability and scope/cost discussion against exact qualification commit `27da4d09c79f03501b1302b9931be3561ff05e75`. No engagement, cost, access, or evidence established. |

These messages are outreach, not external evidence. They do not authorize a
synthetic experiment, account access, data transfer, cost, integration, or a
role that overlaps validator authorship. They also do not satisfy G2.

## External channels

| Channel | Current record | Evidence boundary |
|---|---|---|
| Hacker News | Attempted; authentication-blocked. No verified authenticated editor was available. | No public submission URL recorded. |
| LinkedIn | Attempted; authentication-blocked. Live signed-out state observed. | No public post URL recorded. |
| Reddit | Attempted; authentication-blocked. No verified authenticated editor was available. | No public submission URL recorded. |
| DEV Community | Attempted; authentication-blocked. No verified authenticated editor was available. | No public post URL recorded. |
| Medium | Attempted; authentication-blocked. No verified authenticated editor was available. | No public post URL recorded. |
| X | Attempted; authentication-blocked. Live signed-out state observed. | No public post URL recorded. |

Zenodo and OSF remain deferred until a stable reviewed release. arXiv and
standards engagement remain deferred pending a paper-quality manuscript and
interoperability evidence.

## Readiness boundary

GitHub calls, invitations, CI results, and internal reviews are not independent
external evidence. Phase 2 is internally complete: explicit quarantine
checkpoints, key rotation, concurrent conflicts, invalid targets,
confidentiality, semantic probes, and every-field receipt binding are covered.
G2 remains `BLOCKED` pending a dated independent external review of exact commit
`50e895fbfec544b16c94caa07bf2d1f4049a42e2` and digest
`9547aec8328b601489dda067c6e62f287229b2b24a413dac2c9e7be98e429804`.
Repository verdict remains `NOT_PROD_READY`.
