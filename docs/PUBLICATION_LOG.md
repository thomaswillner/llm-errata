# Publication log

This log records publication and outreach evidence. It does not upgrade a
readiness gate. Last verified: 2026-08-13.

## GitHub public calls

| Surface | Public artifact | Status |
|---|---|---|
| Draft implementation and review surface | [PR #8](https://github.com/thomaswillner/llm-errata/pull/8) | Open draft, targeting `agent/prod-readiness`. |
| Independent review request | [Issue #4](https://github.com/thomaswillner/llm-errata/issues/4) and its [corrected targeted review request](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5274367774) | Open call against corrected immutable target. Portable Agent Memory and libsodium maintainers were asked for distinct, bounded review or referral roles. Invitation only; G2 and G3 remain `BLOCKED`. |
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
| Historical Phase 2 review target | Commit [`50e895fbfec544b16c94caa07bf2d1f4049a42e2`](https://github.com/thomaswillner/llm-errata/commit/50e895fbfec544b16c94caa07bf2d1f4049a42e2), digest `9547aec8328b601489dda067c6e62f287229b2b24a413dac2c9e7be98e429804` | Stale: this target predated the accepted prior-art corrections and must not be used for a current review. Preserved as historical publication evidence. |
| Corrected complete Phase 2 review target | Commit [`08b95263c9ed700c43aea0b285696956cc23e878`](https://github.com/thomaswillner/llm-errata/commit/08b95263c9ed700c43aea0b285696956cc23e878), digest `03abc492319b875a7d528e0e8de05714bc5a7219b42031fc7c3f42cff1f0bf14` | Complete corrected specification, prior-art, licensing, and cryptographic-qualification surface. Checkout and committed-source digests match; exact-target CI passed Python 3.11 and 3.13. Internal evidence does not satisfy G2. |
| Former feedback-remediation target | Commit [`a477fe4f5c86730031b6285d9505778fb8eec060`](https://github.com/thomaswillner/llm-errata/commit/a477fe4f5c86730031b6285d9505778fb8eec060), digest `a6908d21a3fbfc71c11da85ff72634a3917205a06d0ec6c5e3f949756c04e3a3` | Remediated same-importer conflict persistence, signed split-view limitations, and unsupported empty enumeration. Later adapter testing found checkpoint-coverage and contract defects, so this target is historical. Exact-target [CI run 31698542878](https://github.com/thomaswillner/llm-errata/actions/runs/31698542878) passed Python 3.11 and 3.13. |
| Current adapter-contract remediation target | Commit [`ac4468faf73c2cc7949dd29b2a2a151f5bd23116`](https://github.com/thomaswillner/llm-errata/commit/ac4468faf73c2cc7949dd29b2a2a151f5bd23116), digest `7e0d6c88c1ca3a87743ac70ba2a3dfea0b350d112d2d3c59a3c6cbb537568f12` | Preserves adapter-supplied checkpoint coverage, exposes complete adapter runtime surface, and removes hidden reference-ledger coupling. Checkout and committed-tree digests match; exact-target [CI run 31713580146](https://github.com/thomaswillner/llm-errata/actions/runs/31713580146) passed Python 3.11 and 3.13. Internal evidence does not satisfy G2 or G4. |
| Adapter checkpoint finding | [Inspeximus implementation report](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5280326386) | Reproduced `partial` adapter quarantine coverage being recorded as `verified`; accepted and fixed. Interested-party technical evidence, not a qualifying G2 review. |
| Adapter provenance and contract findings | [Inspeximus v2.7.0 report](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5281287746) | Preserves v2.6.1 contamination disclosure, claims a clean-room v2.7.0 rewrite, and reports omitted repair methods plus hidden ledger coupling. Findings reproduced and fixed; independence and current-target behavior remain unverified. |
| Current human remediation reply | [Point-by-point response](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5282207719) | Read back from GitHub with author and body verified. Publishes commit `ac4468f`, digest `7e0d6c88…`, exact-head CI, accepted fixes, provenance boundary, current vector set, and request to rebind Inspeximus. Recruitment and response only; G2 and G4 remain `BLOCKED`. |
| Interested-party technical review | [Two counterexamples](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5276848751) | Bound to the corrected target with explicit Inspeximus/market conflict. Reproduced same-importer versus split-view equivocation limits and unsupported empty-enumeration success. Useful external technical evidence, but not a qualifying complete independent G2 review. |
| Cross-project remediation and adapter offer | [Inspeximus follow-up](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5279081884) | Inspeximus source commit `3661102` fixes an adjacent known-hole audit defect and offers an independently authored adapter plus benchmark harness with explicit commercial interest. No adapter artifact exists yet; the producer cannot also validate its own adapter for G4. |
| Cryptography maintainer response | [Pure-Python Ed25519 reference](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5275036522) | Useful referral and evidence that the outreach lacked plain-language context. The linked pure-Python project is a comparison oracle, not audited constant-time G3 evidence. |
| Human cryptography/context reply | [Plain-language response](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5280206599) | Read back from GitHub with author and body verified. Explains the project and AI-assistance boundary, records the comparison oracle, and states why G3 remains blocked. Technical response only; no further review request. |
| Human findings and adapter reply | [Point-by-point remediation response](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5280210050) | Read back from GitHub with author and body verified. Accepts both reproduced findings, explains the `unknown` decision, records the split-view limitation, and defines a clean-room Inspeximus adapter plus separate-validator shape. Recruitment-only for G4; conflict disclosure remains controlling. |
| Current PR remediation checkpoint | [PR #8 feedback checkpoint](https://github.com/thomaswillner/llm-errata/pull/8#issuecomment-5280225709) | Read back from GitHub with author and body verified. Publishes current commit/digest, exact-head CI, reply URLs, and unchanged G2–G6 blockers without additional mentions. Publication only; it supersedes prior active target pointers. |
| Final independent-implementation call | [Issue #5 completion update](https://github.com/thomaswillner/llm-errata/issues/5#issuecomment-5272475120) | Publishes the immutable Phase 2 commit and digest for two independent adapters and a separate validator. No implementation has been accepted; G4 remains `BLOCKED`. |
| Final three-system nomination call | [Issue #6 completion update](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5272475614) | Publishes the immutable Phase 2 target and exact nomination fields. No system authorization or experiment evidence exists; G5 remains `BLOCKED`. |
| Interested-party review follow-up | [Inspeximus maintainer reply](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5272476094) | Acknowledges the source-grounded correction and points to the final review target. Conflict disclosure remains controlling; a future review from this maintainer cannot satisfy G2 alone. |
| Stale-target finding | [Inspeximus maintainer correction](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5273206921) | Correctly found that the prior frozen commit predated the accepted prior-art corrections. This is interested-party feedback, not independent G2 evidence; the finding required a new immutable target. |
| Corrected maintainer reply | [Human reply and re-frozen target](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5273960394) | Acknowledges the publication defect, publishes corrected commit and digest, answers the licence question, and preserves the conflict boundary. DanceNitra's offered review remains interested-party evidence and requires a separate disinterested reviewer. |
| Corrected adapter and validator recruitment | [Issue #5 targeted follow-up](https://github.com/thomaswillner/llm-errata/issues/5#issuecomment-5274369945) | Supersedes obsolete target and permission language; asks the Remnic maintainer about one clean-room adapter and the ai-memory-mcp maintainer about the separate validator role. No acceptance or implementation evidence is recorded. |
| Corrected operated-system recruitment | [Issue #6 targeted follow-up](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5274371747) | Supersedes obsolete target; asks Mem0 and Cognee maintainers for exact-version operator nominations or impracticality findings. No experiment or account action is authorized. |
| Corrected PR checkpoint | [PR #8 correction](https://github.com/thomaswillner/llm-errata/pull/8#issuecomment-5274373337) | Marks prior PR comments' target and digest historical, publishes corrected immutable target and routes readers to the three current evidence calls. No user mention was added. |
| Corrected Discussion announcement | [Discussion #9 follow-up](https://github.com/thomaswillner/llm-errata/discussions/9#discussioncomment-17995307) | Publishes corrected target, current implementation grant, and current external-evidence calls without mentioning additional users. Publication only; readiness remains unchanged. |
| Phase 2 completion announcement | [Discussion #9 completion update](https://github.com/thomaswillner/llm-errata/discussions/9#discussioncomment-17993648) | Announces internal completion and routes falsifiers to Issues #4, #5, #6, and #10. Publication only; it records no external acceptance or readiness-gate change. |
| Six-step readiness checkpoint | [PR #8 checkpoint](https://github.com/thomaswillner/llm-errata/pull/8#issuecomment-5272526975) | Audits every approved production-readiness step against exact internal and external evidence. Records `NOT_PROD_READY`, the external blockers, PR #3 status, validation, and publication boundaries without claiming certification. |

One current-target reply asks the conflict-disclosed Inspeximus maintainer to
rebind the externally authored adapter candidate to the corrected immutable
surface. It does not establish clean-room independence or satisfy G2 or G4 by
itself. Prior role-specific calls remain historical and visible. No qualifying
second adapter, separate validator, operated-system approval, or CODEOWNER
volunteer is recorded.

The current complete conformance review target is source commit
[`ac4468faf73c2cc7949dd29b2a2a151f5bd23116`](https://github.com/thomaswillner/llm-errata/commit/ac4468faf73c2cc7949dd29b2a2a151f5bd23116)
with canonical Phase 2 surface digest
`7e0d6c88c1ca3a87743ac70ba2a3dfea0b350d112d2d3c59a3c6cbb537568f12`.
The digest was recomputed from checkout and committed tree with an exact match.
The exact-target [GitHub Actions run
31713580146](https://github.com/thomaswillner/llm-errata/actions/runs/31713580146)
passed Python 3.11 and Python 3.13.

The former feedback-remediation target is source commit
[`a477fe4f5c86730031b6285d9505778fb8eec060`](https://github.com/thomaswillner/llm-errata/commit/a477fe4f5c86730031b6285d9505778fb8eec060)
with digest `a6908d21a3fbfc71c11da85ff72634a3917205a06d0ec6c5e3f949756c04e3a3`.
It is historical because the later adapter implementation found checkpoint-
coverage and adapter-contract defects in that surface.

The former complete conformance review target is source commit
[`08b95263c9ed700c43aea0b285696956cc23e878`](https://github.com/thomaswillner/llm-errata/commit/08b95263c9ed700c43aea0b285696956cc23e878)
with canonical Phase 2 surface digest
`03abc492319b875a7d528e0e8de05714bc5a7219b42031fc7c3f42cff1f0bf14`.
The digest was recomputed both from the checkout and from `git show` at that
commit with an exact match. The exact-target [GitHub Actions run
31646616085](https://github.com/thomaswillner/llm-errata/actions/runs/31646616085)
passed Python 3.11 and Python 3.13. It is now historical because external review
found two accepted defects in that surface; the current remediation target
supersedes it.
The previously frozen source commit
[`50e895fbfec544b16c94caa07bf2d1f4049a42e2`](https://github.com/thomaswillner/llm-errata/commit/50e895fbfec544b16c94caa07bf2d1f4049a42e2)
and digest `9547aec8328b601489dda067c6e62f287229b2b24a413dac2c9e7be98e429804`
are historical and stale because they predate the accepted prior-art
corrections. Earlier source commit
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

The later publication head
[`cc4aae11a048c7058e03f8a065b6ddb660a8ab8f`](https://github.com/thomaswillner/llm-errata/commit/cc4aae11a048c7058e03f8a065b6ddb660a8ab8f)
passed [Python 3.11 and Python 3.13](https://github.com/thomaswillner/llm-errata/actions/runs/31637838807)
CI. Python 3.11 initially failed after all 250 test assertions ran, during
`TemporaryDirectory` removal of a Git object directory; one bounded rerun of
the failed job passed. This classifies the first result as an observed cleanup
race rather than suppressing it or treating it as protocol evidence.

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
| publishto.us | [Public challenge page](https://publishto.us/p/oJ88e94KEN) published and read back on 2026-08-13 at 19:07 UTC, then updated and read back after current-target feedback at 19:13 UTC. No account or login was used. | Public recruitment mirror only. It links commit `ac4468faf73c2cc7949dd29b2a2a151f5bd23116`, digest `7e0d6c88…`, repository terms, and `NOT_PROD_READY`. It does not establish review, conformance, interoperability, endorsement, or any G2–G6 pass. |
| Telegra.ph | [Attributed public challenge page](https://telegra.ph/LLM-Errata-please-try-to-break-this-experimental-AI-memory-correction-protocol-08-13) published and read back on 2026-08-13 at 19:08 UTC, then updated and read back after current-target feedback at 19:13 UTC. The official API created a page without user login; author is Thomas Willner and links to the repository. | Public recruitment mirror only. Same immutable target, attribution, `NOT_PROD_READY`, and non-endorsement boundary; no readiness evidence. |
| InstantPost | [Public-stream challenge page](https://instantpost.us/p/di32CWRcqx) published and read back on 2026-08-13 at 19:10 UTC, then updated and read back after current-target feedback at 19:13 UTC. It was visible in the service's public `All posts` stream; no user account or login was used. | Public recruitment mirror only. Same immutable target and boundary; publication and public-stream visibility do not establish independent evidence or upgrade readiness. |

All three successful no-login mirrors use the same reviewed publication copy;
the final amended copy SHA-256 is
`89cdc0dea3bae126f12250a40f84cb385f36b7f8f8a8bd875bab22cd86f21365`. It identifies Thomas Rainer Willner as the
responsible publishing author, discloses substantial AI assistance, names the
commercial and non-commercial attribution requirement, and records the latest
interested-party result as 28/28 published wire/controller cases with only 1/28
reaching an adapter. The producer explicitly states that result does not
validate adapter behavior or move G2 or G4. Write.as returned HTTP/application
code `201` with `id=contentisblocked` and no public URL; InstantPost's first
unauthenticated REST attempt returned `401` before its documented no-account
API-key generation path was used. Neither failed attempt is a public placement.

Zenodo and OSF remain deferred until a stable reviewed release. arXiv and
standards engagement remain deferred pending a paper-quality manuscript and
interoperability evidence.

## Readiness boundary

GitHub calls, replies, CI results, maintainer work, and conflict-disclosed
interested-party review are not qualifying independent evidence. Phase 2 now
also preserves adapter-supplied quarantine coverage, exposes the complete
runtime adapter contract, and removes hidden reference-ledger coupling. G2
remains `BLOCKED` pending a dated qualifying independent review of commit
`ac4468faf73c2cc7949dd29b2a2a151f5bd23116` and digest
`7e0d6c88c1ca3a87743ac70ba2a3dfea0b350d112d2d3c59a3c6cbb537568f12`.
G4 remains `BLOCKED` pending two independently established current-target
adapters and a separately produced validator. Repository verdict remains
`NOT_PROD_READY`.
