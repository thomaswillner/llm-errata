# Publication strategy

## Canonical destination

Every publication points to:

https://github.com/thomaswillner/llm-errata

Substantive prior-art, conformance, implementation, or security findings return
to traceable GitHub issues, pull requests, or private security reports.

## Active and historical surfaces

An **Active surface** is a current public instruction recorded in
`publication/active-surfaces.json`; it binds one immutable commit and digest to
named evidence roles and an explicit evidence boundary. A **Historical surface**
records an earlier project state and remains visible for provenance, but must not
be used as current instructions.

Corrections are append-only. Publish a superseding artifact, name the older URL
as historical, update the manifest, verify every pinned path with
`git cat-file -e <commit>:<path>`, and read the rendered result back before
recording success. Network observations remain publication-time evidence;
`make publication` validates the deterministic tracked contract offline.

## Message

**Problem:** portable AI memory can be corrected at its source while stale local
summaries, embeddings, profiles, graphs, and caches remain active elsewhere.

**Proposal:** importers observe authenticated errata, quarantine known
descendants, rebuild from valid inputs, test absence/replacement/preservation,
and attest honestly—including `unknown` coverage.

**Bounded claim:** reviewed sources contain the individual mechanisms, but no
reviewed public implementation or normative profile required the complete
conjunction at the dated cutoff.

**Status:** experimental conformance proposal and tested reference
implementation; `NOT_PROD_READY`; no independent interoperability evidence yet.

**Call:** find prior art, break the invariants, review the conformance surface,
or independently implement an adapter.

## Channel matrix

| Channel | Audience | Primary request | Publication gate |
|---|---|---|---|
| GitHub | implementers and reviewers | issues, review, adapters | repository and CI current |
| Hacker News | systems and open-source engineers | falsification and prior art | concise factual submission |
| LinkedIn | named researchers and standards experts | independent reviewers | authenticated author account |
| X | AI-memory practitioners | reviewer and implementer referrals | authenticated account |
| Reddit | focused technical communities | critique, not promotion | subreddit rules checked |
| DEV Community | developers | reproducible technical walkthrough | authenticated account |
| Medium | broader technical readers | explanatory article | authenticated account |
| Zenodo/OSF | citable archival record | archive release and evidence | stable reviewed release |
| arXiv | academic readers | paper and experiments | paper-quality manuscript |

## Canonical short announcement

> If an AI imports a memory, should it also accept responsibility for future
> corrections? LLM Errata is an experimental vendor-neutral conformance proposal:
> observe an authenticated correction, quarantine known descendants, rebuild
> from valid inputs, run negative/positive/preservation checks, and return a
> signed receipt that admits unknown coverage. The repository includes prior-art
> collisions, schemas, vectors, a runnable reference implementation, and explicit
> falsifiers. It is NOT_PROD_READY and needs independent review and adapters:
> https://github.com/thomaswillner/llm-errata

## Hacker News title

`LLM Errata – making corrections follow portable AI memory`

## LinkedIn opening

`An imported AI memory is a dependency, not a copy.`

The post should ask AI-memory, distributed-systems, privacy, and standards
specialists to review the exact four-part conjunction and identify collisions.

## Publication evidence

For every successful post, record channel, URL, publication timestamp, account,
source commit, exact copy digest, and moderation state. A submitted or queued
post is not recorded as publicly available until its URL is accessible.
Recruitment evidence records a bounded request only. It never establishes an
independent review, implementation, validator result, operated-system result, or
production-readiness pass.
