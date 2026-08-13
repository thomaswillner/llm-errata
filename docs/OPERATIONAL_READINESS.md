# Operational readiness evidence contract

LLM Errata gate G6 is an external operational-evidence gate. Repository tests
can validate this contract but cannot satisfy it. G6 passes only when one
independent report binds an exact repository commit and deployment to measured
passing evidence for all ten scopes below.

## Operator declaration

Before testing, operator declares:

- stable deployment ID, platform, environment, deployed artifact SHA-256,
  build-provenance reference, and deployment timestamp;
- workload name, dataset class, whether data is synthetic, positive event or
  request volume, concurrency, duration in seconds, and failure domain;
- observation-window start and end in UTC; and
- numeric threshold, unit, comparator, metric, and raw evidence reference for
  every measurement.

Repository does not invent universal latency, throughput, RTO, RPO, overload,
or incident-response thresholds. Operator owns those service decisions before
exercise. Missing thresholds remain `BLOCKED`.

## Ten mandatory scopes

Each token appears exactly once. Alias, duplicate, missing, unknown, or extra
scope fails qualification.

1. `deployment-integrity-provenance`: verify deployed artifact identity,
   signature or digest, build and dependency provenance, and environment.
2. `rollback-exercise`: measure rollback and verify restored service and state.
3. `backup-recovery-rto-rpo`: exercise recovery against declared numeric RTO
   and RPO thresholds.
4. `lifecycle-observability-alerting`: observe quarantine, rebuild, test,
   attest, refusal, and incomplete coverage, including alert delivery.
5. `telemetry-privacy-redaction`: verify logs, metrics, traces, and retained
   evidence exclude prohibited memory content, secrets, and erased values.
6. `supported-version-compatibility`: exercise declared runtime, schema,
   adapter, store, and platform version matrix.
7. `representative-latency-throughput`: measure representative latency and
   throughput against declared thresholds.
8. `overload-rate-limit-dos`: measure overload, resource exhaustion, rate
   limiting, and denial-of-service behavior against declared safety thresholds.
9. `incident-response-exercise`: measure detection, containment, recovery,
   communication, and learning exercise.
10. `operational-access-secrets-dependencies-vulnerability-management`:
    exercise least privilege, secret lifecycle, dependency inventory, patch
    policy, and vulnerability response.

## Structured report

Top-level external evidence entry contains:

- non-generic report `ref`, independent `producer`, HTTPS
  `producer_identity`, ISO `observed` date, `relationship` equal to
  `independent-third-party`, conflicts list, and exact attestation
  `llm-errata-independent-operational-review-v1`;
- result `pass`, `pass-with-findings`, or `fail`;
- full lowercase 40-character `reviewed_commit` and canonical
  `surface_digest`;
- `deployment`, `workload`, and `observation_window` declarations; and
- exactly ten `scopes` records.

Every scope contains its normative token, status `pass` or `fail`, one or more
raw artifact references, one or more measurements, and findings list. Every
measurement contains non-empty metric and unit, finite numeric value and
threshold in same unit, comparator (`<=`, `<`, `>=`, `>`, `==`, or `!=`), and
raw evidence reference.

Checker evaluates comparators; declared `pass` cannot override failed number.
Structurally complete failed report remains useful evidence but cannot qualify
G6. Generic URL, absent measurement, nine passing scopes, or internally
produced report cannot qualify.

## Independence and binding

Producer cannot be author, owner, maintainer, reference implementer, assessed
deployment operator, contributor, repository-controlled agent, or self-review
identity. Conflicts must be declared even when list is empty.

Surface digest covers this document, security and roadmap documents, checker,
and checker tests using ordered
`relative-path + NUL + raw-bytes + NUL` SHA-256 framing. Reported digest must
match current checkout and named commit. Any drift requires new review.

Readiness ledger and matrix remain outside digest because they record report
and gate result after review; including them would create self-referential
evidence. Their exact synchronization is checked separately.

## Evidence workflow

1. Freeze commit, deployment, workload, thresholds, and observation window.
2. Execute all ten scopes and retain raw artifacts without prohibited content.
3. Independent producer publishes or privately delivers structured report.
4. Maintainer records evidence entry without editing measurements or identity.
5. Run `make readiness`; change G6 only if checker finds qualifying report.

An invitation, scheduled exercise, CI run, internal agent review, or skeleton
below is not operational evidence.

```json
{
  "kind": "external",
  "result": "fail",
  "scopes": []
}
```

Skeleton is deliberately incomplete and non-qualifying. It contains no
invented operator thresholds or measurements.

## Grounding boundary

Scope selection draws on incident response, secure development, provenance,
telemetry, and logging guidance pinned in `SOURCES.md`. Those sources do not
certify LLM Errata and do not supply operator-specific numeric thresholds.
