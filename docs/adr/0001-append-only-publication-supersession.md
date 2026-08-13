---
status: accepted
---

# Keep GitHub history append-only and track current instructions separately

GitHub comments remain immutable publication history because editing or deleting
them would weaken provenance. A tracked active-surface manifest identifies the
current frozen target, licence posture, evidence roles, and superseding URLs;
deterministic repository checks validate that manifest, while live GitHub checks
remain a publication-time gate rather than part of offline `make check`.

## Considered options

- Editing old comments was rejected because it obscures what reviewers actually
  saw and GitHub exposes edit history anyway.
- Treating the newest comment as current was rejected because chronology does
  not prove semantic supersession or role completeness.
- Scraping GitHub during every repository check was rejected because network,
  authentication, rate limits, and mutable external state make builds
  nondeterministic.

## Consequences

Every current public call must appear once in the manifest and every replacement
must name its superseded surface. Historical URLs remain permitted only outside
the active manifest and must be clearly labelled as historical where presented.
