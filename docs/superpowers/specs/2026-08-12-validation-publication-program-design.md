# LLM Errata Validation and Publication Program Design

**Date:** 2026-08-12

**Status:** Approved for execution by the repository owner

## Objective

Turn LLM Errata from a self-reviewed reference implementation into a publicly
falsifiable interoperability effort. Publication is part of validation: every
artifact must invite prior-art challenges, independent review, and independent
implementation without representing planned work as completed evidence.

## Fixed claims boundary

The program may describe LLM Errata as an experimental, vendor-neutral
conformance proposal and tested reference implementation. It may state that no
reviewed public source was found to require the complete four-part conjunction
at the dated research cutoff.

The program must not describe LLM Errata as:

- a world first, proven breakthrough, production protocol, or standard;
- proof of deletion, semantic absence, patentability, or freedom to operate;
- interoperable before independently authored implementations and measured
  cross-system evidence exist; or
- externally reviewed when the only reviewers are the author or author-directed
  agents.

## Program sequence

1. **Intellectual-property posture.** Retain the current personal-use licence.
   Permit research and standards implementations through explicit written,
   scoped grants. Do not relicense or make patent conclusions without separate
   owner approval informed by qualified legal advice.
2. **Independent review.** Publish two calls: one for novelty/conformance review
   and one for security/distributed-systems review. Reviews must identify the
   reviewer, reviewed commit, date, scope, findings, and conflicts.
3. **Readiness-foundation integration.** Preserve PR #3 and branch protection.
   It may merge only after the required separate CODEOWNER approval and green
   required checks.
4. **G2 semantic evidence.** Implement the provider-neutral semantic-probe
   design in the companion specification. Internal implementation can complete
   Phase 2 item 6, but G2 remains `BLOCKED` until dated independent review of
   the complete Phase 2 surface exists.
5. **Independent conformance and interoperability.** Recruit two independently
   authored adapters and a separately produced validator. Only then run the
   declared three-system experiment with synthetic data, one intentionally
   nonconforming importer, and one genuinely incomplete-coverage system.
6. **Evidence-bounded publication.** Publish channel-specific calls that link
   the canonical repository and request falsification, review, or implementation.
   Record every public URL and the exact claim version used.

## Licensing and permission strategy

The current licence remains controlling. Research implementers may request a
written permission grant through a public GitHub issue. A grant must name:

- grantee and repository or organization;
- research or standards purpose;
- permitted specification version and files;
- commercial and redistribution boundaries;
- term, attribution, and publication expectations; and
- whether resulting implementation evidence may be cited by LLM Errata.

No permission request, discussion, or contribution changes the licence by
implication. Permission records must not disclose confidential legal advice.

## Independent evidence contract

An independent review qualifies only when its producer is not the author, not
the implementation maker being reviewed, and not an agent controlled by either.
It must be reproducible from a named commit and publish or privately deliver a
dated report with concrete findings. A review invitation is not review evidence.

An independently authored adapter qualifies only when its author works from the
published specification and vectors rather than copying the reference adapter.
Shared test vectors are allowed and expected. Shared implementation code is not.

## Publication channels

Priority is based on evidence value rather than audience size:

1. GitHub repository, issues, pull requests, and Discussions if enabled;
2. Hacker News and relevant technical forums for prior-art and systems critique;
3. LinkedIn and X for named expert recruitment;
4. Reddit communities whose rules permit research or open-source submissions;
5. archival research surfaces such as Zenodo or OSF after a citable release;
6. arXiv only after a paper-quality manuscript and appropriate category fit.

Every post links `https://github.com/thomaswillner/llm-errata`, uses the current
`NOT_PROD_READY` disclosure, and directs substantive findings into traceable
GitHub issues or pull requests.

## Acceptance gates

- Strategy, reviewer rubric, implementation call, and publication copy are
  version-controlled and pass repository checks.
- G2 deterministic fixtures pass without credentials or network access.
- Missing, skipped, malformed, configuration-drifted, or inconclusive semantic
  observations cannot support a verified semantic result.
- Recruitment and publication URLs are recorded after successful submission.
- Readiness gates change only from qualifying evidence, never from invitations,
  implementation completion, CI, or publication volume.

## Stop and reroute conditions

Stop mutation or publication when copy would overstate evidence, platform rules
prohibit the submission, credentials are unavailable, a reviewer is not
independent, or implementation requires an unapproved licence change. Reroute
after a complete prior-art collision, external review rejection, material G2
contract change, or failure to recruit independent implementers.

