# G6 Operational Evidence Design

**Date:** 2026-08-12

**Status:** Approved for readiness-checker implementation

## Purpose

Turn G6 from a broad prose aspiration into a fail-closed operational evidence
contract. G6 remains one external gate. It passes only when one independently
produced structured report binds an exact repository commit and deployment to
measured evidence for every mandatory operational scope.

Internal tests validate the contract; they do not satisfy it. Missing operator
thresholds, synthetic example reports, repository CI, invitations, and author-
or agent-produced assessments keep G6 `BLOCKED`.

## Mandatory scopes

One report contains exactly one result for each unique scope token:

1. `deployment-integrity-provenance` — deployed artifact identity, build and
   dependency provenance, signature or digest verification, and environment
   binding;
2. `rollback-exercise` — measured rollback from the tested deployment and
   verification of restored service and state;
3. `backup-recovery-rto-rpo` — recovery exercise with declared numeric RTO and
   RPO thresholds and measured recovery time and recovery-point loss;
4. `lifecycle-observability-alerting` — observable quarantine, rebuild, test,
   attest, refusal, and incomplete-coverage lifecycle with alert delivery;
5. `telemetry-privacy-redaction` — verification that logs, traces, metrics, and
   retained evidence exclude prohibited memory content, secrets, and erased
   values;
6. `supported-version-compatibility` — declared supported runtime, schema,
   adapter, store, and platform versions exercised against a compatibility
   matrix;
7. `representative-latency-throughput` — declared workload with measured
   latency and throughput against numeric thresholds;
8. `overload-rate-limit-dos` — overload, rate limiting, resource exhaustion,
   and denial-of-service behavior measured against declared safety thresholds;
9. `incident-response-exercise` — dated detection, containment, recovery,
   communication, and learning exercise with measured response thresholds; and
10. `operational-access-secrets-dependencies-vulnerability-management` —
    least-privilege access, secret lifecycle, dependency inventory, supported
    patch policy, and vulnerability response measured against declared gates.

Scope tokens are normative and unique. Aliases, duplicate tokens, missing
tokens, or extra tokens fail qualification rather than being guessed into a
mapping.

## Report envelope

A qualifying evidence entry is `kind: external` and includes:

- `ref`: non-generic HTTPS report URL with a path, or a scoped URN;
- `producer`, `producer_identity`, `relationship`, `conflicts`, and the exact
  attestation `llm-errata-independent-operational-review-v1`;
- `observed` ISO date and `result` equal to `pass`, `pass-with-findings`, or
  `fail`;
- `reviewed_commit`: full 40-character lowercase commit available in repository
  history;
- `surface_digest`: canonical digest of G6 readiness and operational contract
  files at that commit and in current checkout;
- `deployment`: stable deployment ID, platform, environment, artifact digest,
  build provenance reference, and deployment timestamp;
- `workload`: name, dataset class, synthetic-data declaration, request or event
  volume, concurrency, duration, and failure domain;
- `observation_window`: ISO start and end timestamps with end after start; and
- `scopes`: the ten structured results.

The producer must be independent of author, owner, maintainer, reference
implementer, deployment operator being assessed, and project-controlled agents.
Declared conflicts are retained for review; an empty list is permitted, but a
missing conflicts field is not.

## Per-scope measurement contract

Every scope result contains:

- its unique `scope` token;
- `status`: `pass` or `fail`;
- at least one raw `artifact` reference;
- non-empty `measurements`; and
- optional findings that cannot override a failed comparator.

Every measurement declares:

- `metric`: stable non-empty name;
- `value`: finite JSON number;
- `unit`: non-empty explicit unit;
- `comparator`: one of `<=`, `<`, `>=`, `>`, `==`, or `!=`;
- `threshold`: finite JSON number in the same unit; and
- `evidence_ref`: raw evidence URL or scoped URN.

The checker evaluates every comparator. A scope passes only when its declared
status is `pass`, every measurement comparator passes, and required identity,
artifact, workload, platform, failure-domain, and observation-window fields are
present. Text such as “acceptable,” absent numeric thresholds, mixed units,
NaN, infinity, or a generic evidence URL cannot pass.

Operator-specific policy decides threshold values; the repository does not
invent universal latency, RTO, RPO, volume, or incident thresholds. A report
without them remains structurally valid evidence of work but cannot qualify G6
for `PASS`.

## Gate qualification

`valid_g6_operational_evidence()` validates complete report structure and exact
commit/deployment binding. `qualifying_g6_operational_evidence()` additionally
requires:

- report result `pass` or `pass-with-findings`;
- all ten scopes present exactly once;
- every scope status `pass`;
- every comparator true; and
- current checkout G6 surface digest equal to both reported digest and the
  digest reconstructed from `reviewed_commit`.

Generic external evidence remains insufficient. G6 changes to `PASS` only when
at least one evidence entry qualifies. A structurally complete `fail` report is
valuable evidence but keeps G6 from passing.

## Canonical G6 surface

The digest covers:

- `docs/OPERATIONAL_READINESS.md`;
- `PRODUCTION_READINESS.md`;
- `SECURITY.md`;
- `ROADMAP.md`;
- `readiness/production-readiness.json`;
- `scripts/check_readiness.py`; and
- `tests/test_readiness.py`.

It uses the same ordered `relative path + NUL + raw bytes + NUL` SHA-256 framing
as G2. A missing file, unavailable commit, or byte drift blocks qualification.

## Human documentation

`docs/OPERATIONAL_READINESS.md` explains the ten scopes, report schema,
measurement rules, independence boundary, operator workflow, and example
non-qualifying skeleton. It contains no fabricated measurements or thresholds.

The readiness ledger and human matrix cite the document and state exactly why
G6 is `BLOCKED`: no independent report binding an exact commit, deployment, and
passing measured comparator for all ten scopes exists. `CHANGELOG.md` records
the strengthened contract, and `SOURCES.md` pins the primary grounding sources:

- NIST SP 800-61 Revision 3;
- NIST SP 800-218;
- SLSA version 1.2;
- OpenTelemetry signals and semantic conventions; and
- OWASP Logging Cheat Sheet.

Sources support scope selection and terminology. They do not certify this
project or supply operator thresholds.

## Test contract

Strict TDD must prove rejection of:

- generic URL-only evidence;
- internal or ambiguous producer;
- missing or invalid identity, conflicts, relationship, or attestation;
- nonexistent or non-current commit and surface digest drift;
- missing deployment, platform, artifact, provenance, workload, failure domain,
  or observation window;
- missing, duplicate, unknown, or extra scope tokens;
- missing artifacts or measurements;
- missing, nonnumeric, nonfinite, unitless, or invalid thresholds and values;
- invalid comparator and failed comparator;
- a scope marked pass when one comparator fails;
- report result `fail`; and
- nine passing scopes presented as complete evidence.

Positive tests use a complete synthetic report bound to a temporary committed
repository copy. Test reports do not enter the production-readiness ledger and
do not upgrade G6.
