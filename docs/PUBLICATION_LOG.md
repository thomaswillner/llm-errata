# Publication log

This log records publication and outreach evidence. It does not upgrade a
readiness gate. Last verified: 2026-08-12.

## GitHub public calls

| Surface | Public artifact | Status |
|---|---|---|
| Draft implementation and review surface | [PR #8](https://github.com/thomaswillner/llm-errata/pull/8) | Open draft, targeting `agent/prod-readiness`. |
| Independent review request | [Issue #4](https://github.com/thomaswillner/llm-errata/issues/4) and its [exact review target](https://github.com/thomaswillner/llm-errata/issues/4#issuecomment-5269378077) | Open call for conformance, novelty, security, and distributed-systems review. |
| Independent implementation call | [Issue #5](https://github.com/thomaswillner/llm-errata/issues/5) and its [implementation update](https://github.com/thomaswillner/llm-errata/issues/5#issuecomment-5269378246) | Open call for independently authored adapters and a separately produced validator. |
| Phase 3 system nominations | [Issue #6](https://github.com/thomaswillner/llm-errata/issues/6) and its [nomination update](https://github.com/thomaswillner/llm-errata/issues/6#issuecomment-5269378440) | Open nominations only; no experiment is authorized or underway. |

The published review target is source commit
[`35052868cde8b6f16fc6c20b4136ae0277f9a00e`](https://github.com/thomaswillner/llm-errata/commit/35052868cde8b6f16fc6c20b4136ae0277f9a00e)
with canonical Phase 2 surface digest
`a3133f759620ed942d6cd519d303c0be1554f0193b89e0a141c410aaf4c047b9`.
GitHub Actions completed successfully for [Python
3.11](https://github.com/thomaswillner/llm-errata/actions/runs/31616307869/job/94179861514)
and [Python
3.13](https://github.com/thomaswillner/llm-errata/actions/runs/31616307869/job/94179861561).

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
