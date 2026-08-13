# Active Publication Surface Reconciliation Design

## Purpose

Prevent reviewers, independent implementers, validator authors, and operated-
system owners from following obsolete LLM Errata targets or licence instructions.
The repository will distinguish current public instructions from append-only
GitHub history and fail deterministic checks when the current contract drifts.

This hardens recruitment and publication integrity. It does not satisfy an
external readiness gate and cannot change `NOT_PROD_READY` by itself.

## Selected approach

Use a tracked active-surface manifest plus a dependency-free offline validator.
The manifest is the sole repository authority for which public artifacts are
current. Historical comments remain untouched and visible; current comments
explicitly supersede them.

The rejected alternatives are:

1. edit or delete obsolete GitHub comments, which weakens provenance;
2. infer current instructions from the newest comment, which confuses chronology
   with semantic authority; and
3. query GitHub from `make check`, which makes deterministic validation depend on
   authentication, rate limits, and mutable network state.

## Active-surface manifest

Create `publication/active-surfaces.json` with:

- `schema_version`: exactly `1`;
- `review_target.commit`: exact 40-character lowercase Git object ID;
- `review_target.surface_digest`: exact 64-character lowercase SHA-256;
- `license`: specification implementation posture, mandatory attribution, and
  personal-use reference-code boundary;
- `surfaces`: one object for each active Issue #4, Issue #5, Issue #6, PR #8, and
  Discussion #9 follow-up;
- each surface: stable ID, kind, URL, publication date, gates, evidence roles,
  mentioned GitHub identities, superseded URLs, and evidence boundary.

The manifest will point to source target
`08b95263c9ed700c43aea0b285696956cc23e878` and digest
`03abc492319b875a7d528e0e8de05714bc5a7219b42031fc7c3f42cff1f0bf14`.

## Deterministic validator

Create `scripts/check_publication.py`, using only Python standard library. It
must reject:

- malformed schema, commit, digest, URL, gate, date, role, or mention fields;
- duplicate active IDs, URLs, evidence roles, or GitHub mentions;
- a current surface that does not bind the canonical commit and digest;
- obsolete target `50e895fbfec544b16c94caa07bf2d1f4049a42e2` or digest
  `9547aec8328b601489dda067c6e62f287229b2b24a413dac2c9e7be98e429804`;
- obsolete case-by-case implementation permission language;
- a commercial/non-commercial implementation grant without LLM Errata, Thomas
  Willner, repository, and personal-use reference-code boundaries;
- a surface that represents invitation, maintainer work, CI, or publication as
  independent readiness evidence;
- missing current surfaces for G2/G3 review, G4 adapter/validator work, G5
  operated systems, PR correction, or Discussion correction.

Successful validation means the tracked publication contract is internally
consistent. It does not prove URLs are live, mentions notified users, conflicts
are complete, or independent work occurred.

## Live publication gate

Network-dependent publication checkpoints continue to verify:

- every target identity maps to the cited project and role;
- every pinned blob path exists at its exact commit before posting;
- public HTTP URLs resolve;
- no duplicate follow-up exists before mutation;
- rendered comment body, author, URL, and mention count match the admitted draft;
- external responses are read before any retry or further mention.

These observations belong in `docs/PUBLICATION_LOG.md` and durable loop state,
not in the offline validator's pass condition.

## Integration

- Add `publication/active-surfaces.json` and `scripts/check_publication.py` to
  required repository files.
- Add `make publication`; run it from `make check` before unit tests.
- Add `.github/workflows/validate.yml` execution through existing `make check`.
- Add negative tests in `tests/test_publication.py`; every advertised rejection
  must be demonstrated by a mutation that fails for the intended reason.
- Update `AGENTS.md`, `CONTRIBUTING.md`, and `docs/PUBLICATION_STRATEGY.md` with
  the active/historical boundary and pre-post pinned-link check.

## Failure handling

- Structural or semantic manifest defects exit `1` and block commit/publication.
- Missing or unreadable manifest exits `2` as inconclusive, never pass.
- Live GitHub ambiguity triggers read-after-write reconciliation before retry.
- A new external response pauses publication mutation until its recommendations,
  conflicts, and gate eligibility are classified.

## Verification

Required gates:

1. focused publication tests demonstrate red, then green;
2. `python3 scripts/check_publication.py` passes current manifest;
3. `make check` passes all repository, claim, readiness, publication, unit, and
   demo checks;
4. `make links` resolves all citations under repository policy;
5. `git diff --check` passes;
6. branch push produces Python 3.11 and 3.13 exact-head CI success;
7. readiness verdict remains `NOT_PROD_READY` unless independent evidence meets
   every gate contract.

## Scope boundary

This slice does not create an independent reviewer, implementation, validator,
system operator, production signer, or measured operational report. It improves
the probability and integrity of obtaining that evidence; G2 through G6 remain
blocked until qualifying external work is recorded.
