# Publication log

This log records publication and outreach evidence. It does not upgrade a
readiness gate. Last verified: 2026-08-12.

## GitHub public calls

| Surface | Public artifact | Status |
|---|---|---|
| Draft implementation and review surface | [PR #8](https://github.com/thomaswillner/llm-errata/pull/8) | Open draft, targeting `agent/prod-readiness`. |
| Independent review request | [Issue #4](https://github.com/thomaswillner/llm-errata/issues/4) and its [exact review target](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5269378077) | Open call for conformance, novelty, security, and distributed-systems review. |
| Targeted independent-review recruitment | [Inspeximus maintainer invitation](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5269444341) | Invitation to challenge the stated collision boundary; it is not external evidence. |
| Targeted adapter recruitment | [Remnic invitation](https://github.com/thomaswillner/llm-errata/issues/5#issuecomment-5269523953) | Invitation to become a future independently authored adapter after Phase 2 completion; it is not technical evidence. |
| Targeted validator or system recruitment | [ai-memory-mcp invitation](https://github.com/thomaswillner/llm-errata/issues/5#issuecomment-5269524142) | Invitation to choose one separate role: independently produced validator or independently operated system; it is not technical evidence. |
| Targeted standards/collision review | [Portable Agent Memory invitation](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5269524323) | Invitation to test the conformance/standards collision boundary; it is not review evidence. |
| Targeted operated-system nomination | [Mem0 invitation](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269537990) | Invitation to nominate a future independently operated system; it is non-evidence and separate from validator authorship. |
| Targeted operated-system nomination | [Cognee invitation](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269538156) | Invitation to nominate a future independently operated system; it is non-evidence and separate from validator authorship. |
| Separate CODEOWNER volunteer recruitment | [PR #3 reviewer call](https://github.com/thomaswillner/llm-errata/pull/3#issuecomment-5269583214) | Invitation only; no volunteer or reviewer is recorded, no access was granted, and this call made no CODEOWNERS or protection change. It is not external evidence. |
| Independent implementation call | [Issue #5](https://github.com/thomaswillner/llm-errata/issues/5) and its [implementation update](https://github.com/thomaswillner/llm-errata/issues/5#issuecomment-5269378246) | Open call for independently authored adapters and a separately produced validator. |
| Phase 3 system nominations | [Issue #6](https://github.com/thomaswillner/llm-errata/issues/6) and its [nomination update](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269378440) | Open nominations only; no experiment is authorized or underway. |

No targeted invitation has an acceptance or reply recorded.

The conformance review target remains source commit
[`35052868cde8b6f16fc6c20b4136ae0277f9a00e`](https://github.com/thomaswillner/llm-errata/commit/35052868cde8b6f16fc6c20b4136ae0277f9a00e)
with canonical Phase 2 surface digest
`a3133f759620ed942d6cd519d303c0be1554f0193b89e0a141c410aaf4c047b9`.
PR #8 currently heads at publication-log commit
[`cbcfd2a0d77f1060651bac781599edc469a42c26`](https://github.com/thomaswillner/llm-errata/commit/cbcfd2a0d77f1060651bac781599edc469a42c26).
GitHub Actions for that current PR head completed successfully for [Python
3.11](https://github.com/thomaswillner/llm-errata/actions/runs/31616716434/job/94181230842)
and [Python
3.13](https://github.com/thomaswillner/llm-errata/actions/runs/31616716434/job/94181230861).

## Direct email outreach

| Recipient | Subject | Status |
|---|---|---|
| `founders@mem0.ai` | `Nomination request: Mem0 for an independent AI-memory interoperability experiment` | Sent 2026-08-12; no reply or acceptance recorded. Linked [Mem0 GitHub invitation](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269537990) remains nomination-only. |
| `info@topoteretes.com` | `Nomination request: Cognee for an independent AI-memory interoperability experiment` | Sent 2026-08-12; no reply or acceptance recorded. Linked [Cognee GitHub invitation](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269538156) remains nomination-only. |

These messages are outreach, not external evidence. They do not authorize a
synthetic experiment, account access, data transfer, cost, integration, or a
role that overlaps validator authorship.

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
external evidence. Phase 2 remains incomplete: the explicit `errata quarantine`
CLI and vectors for key rotation, concurrent events, invalid targets, and
confidentiality remain absent; receipt state-root binding vectors exist but
receipt-binding coverage is partial. G2 remains `BLOCKED` pending internal Phase
2 completion and a dated independent external review of the complete
conformance surface. Repository verdict remains `NOT_PROD_READY`.
