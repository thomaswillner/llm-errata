# Controlled Pilot Production-Readiness Program v1 Design

**Date:** 2026-08-14

**Owner:** Thomas Willner

**Status:** Draft committed for owner review

**Starting target:** `4ed5d01a1b5838751756f6092bc36cb1ba2802e9` (`v0.4.1`)

**Current verdict:** `NOT_PROD_READY`

## Purpose

Turn LLM Errata from a tested reference implementation into a production-ready
system by producing the exact evidence required by gates G2 through G6. The
program begins immediately with synthetic data and progresses through
authorized shadow and limited-production use. It never upgrades a gate from
planned work, model confidence, repository activity, outreach, or self-issued
attestation.

The end condition is not “pilot launched.” The end condition is one exact
assessed commit and deployment for which G1 through G6 all have current,
qualifying evidence, required GitHub checks pass, no actionable collaboration
feedback remains unresolved, and an authorized maintainer records
`PROD_READY`.

## Selected approach

Run one controlled-pilot program with two coordinated tracks:

1. **Assurance track:** close G2, G3, and G4 through exact-target review,
   production cryptography qualification, independently authored adapters, and
   a separately produced validator result.
2. **Operation track:** close G5 and G6 through a synthetic three-system
   interoperability experiment followed by bounded production operation and an
   independent ten-scope operational report.

The tracks may prepare concurrently, but limited production cannot start until
the assurance entry gates pass. Claude and Codex drive research, drafting,
implementation, coordination, and structural validation. They do not sign
evidence reserved for independent reviewers, auditors, implementers,
validators, operators, or customers.

Rejected approaches:

- **Relabel model output as independent evidence:** fast but invalid under the
  repository's identity, conflict, and relationship contracts.
- **Begin with unrestricted customer data:** creates avoidable confidentiality,
  erasure, authorization, and recovery exposure before safety controls exist.
- **Wait for unsolicited reviewers:** preserves the gate but does not create an
  evidence-producing program.
- **Lower or waive G2-G6:** changes the meaning of `PROD_READY` instead of
  proving it.
- **Create multiple same-owner implementations and call them independent:**
  useful internal differential testing but not G4 evidence.

## Contract and invariants

The program freezes these invariants:

- correction, supersession, and erasure remain distinct;
- quarantine precedes repair, rebuild, or recall;
- negative, positive, and preservation checks remain mandatory;
- missing lineage, opaque stores, skipped tests, unsupported adapters, and
  timeouts never become success;
- erasure evidence never repeats erased content;
- every report binds the exact reviewed commit, canonical surface digest,
  implementation or deployment identity, producer, date, relationship, and
  conflicts;
- synthetic data is mandatory until an explicit approval names the real-data
  scope, systems, handling, retention, and deletion procedure;
- a maker never certifies its own implementation, and a deployment operator
  never produces the qualifying independent G6 report for that deployment;
- commercial or product use credits `LLM Errata`, `Thomas Willner`, and the
  canonical repository in an ordinarily accessible location;
- commercial use of Reference Code requires a separate licence from Thomas
  Willner; the Specification Materials implementation grant does not transfer
  repository ownership or imply endorsement.

## Program architecture

Implementation will add a complete pilot-control surface rather than empty
scaffolding:

| Component | Responsibility |
|---|---|
| `pilot/program.schema.json` | Exact schema for stage, target, roles, authorization, systems, thresholds, data class, evidence, and stop state. |
| `pilot/program.json` | Current admitted program state, never a readiness attestation. |
| `pilot/fixtures/controlled-root.json` | Content-safe synthetic root covering correction, supersession, erasure, opaque coverage, mixed lineage, and stale reimport. |
| `pilot/runs/{run-id}/manifest.json` | Immutable run input: target, deployment, systems, operators, workload, thresholds, observation window, and fixture digest. |
| `pilot/runs/{run-id}/result.json` | Measured result with raw-evidence references and explicit `pass`, `partial`, `unknown`, or `failed` outcomes. |
| `scripts/check_pilot.py` | Dependency-free admission and result validator. It validates structure and comparators but cannot prove identity or independence. |
| `docs/PILOT_OPERATIONS.md` | Operator runbook for authorization, execution, kill, rollback, recovery, retention, and evidence handoff. |

`make pilot` will run the validator. `make check` will include `make pilot` once
the first complete state and negative tests exist. A structurally valid pilot
record does not change the production-readiness ledger.

## Stage model

### Stage 0 — Admission control

No external system or real data is used.

Entry: clean exact target and approved design.

Work: implement schema, validator, state machine, synthetic root, authorization
model, conflict/independence declarations, and negative tests.

Exit: every advertised rejection has a red-then-green test; `make check` passes
on supported Python versions; Claude reviews the exact surface read-only; no
blocking finding remains.

### Stage 1 — Synthetic lab

Use local reference stores and isolated candidate adapters only. No network
account, customer data, or production effect is permitted.

Required evidence:

- correction, supersession, and erasure complete against the synthetic root;
- known descendants have zero stale recall after the declared quarantine
  checkpoint;
- unrelated retained content remains available;
- stale reimport fails;
- opaque or incomplete coverage remains explicit;
- telemetry contains zero prohibited memory values, secrets, or erased data;
- rollback restores the declared pre-run state without reviving retired recall.

Exit: complete internal run manifest and result; no claim toward G5 or G6.

### Stage 2 — Authorized shadow interoperability

Use one synthetic, user-controlled root across three real, independently
operated memory systems. Operations are non-authoritative and isolated from
customer-facing recall.

Before any interaction, Thomas Willner must approve each system, account,
integration, data-residency posture, cost class, and publication scope. Each
operator must provide a stable public identity and authority statement.

The three-system set must contain:

1. one intentionally nonconforming importer;
2. one genuinely incomplete or opaque coverage system; and
3. one mixed-artifact-lineage system.

Every system completes correction, supersession, and erasure and records all
nine G5 measurements. A separate producer publishes the complete G5 report.
Generic system summaries, owner-operated local clones, or three accounts under
one operator do not qualify.

Exit: G5 has a qualifying report and is `PASS`; G2, G3, and G4 also pass before
Stage 3 admission.

### Stage 3 — Limited authorized production

Use explicitly approved low-risk data only. The approval must name data fields,
purpose, systems, retention, deletion, incident contacts, and rollback owner.
No approval is inferred from a general pilot agreement.

Entry requires:

- G2, G3, G4, and G5 `PASS` on the current target;
- exact deployment and build provenance;
- operator-declared numeric thresholds for every G6 measurement;
- successful staging rollback and backup-recovery exercises;
- active telemetry redaction, alert delivery, rate limits, least privilege,
  secret rotation, dependency inventory, and vulnerability response;
- signed kill authority available throughout the observation window.

The qualifying G6 producer is independent of the repository and assessed
deployment operator. The report covers exactly ten required scopes and checks
numeric comparators against raw artifacts.

Exit: one complete independent G6 report qualifies, all remaining findings are
within predeclared acceptance policy, and G6 becomes `PASS`.

### Stage 4 — Production expansion

Entry requires G1-G6 `PASS`, green exact-head CI, a clean final GitHub freshness
receipt, and an authorized maintainer verdict change. Expansion preserves the
same evidence and attribution requirements; a platform, cryptographic build,
adapter, deployment, or material surface change invalidates affected evidence
and reopens its gate.

## Gate workstreams

### G2 — External Phase 2 conformance review

Freeze the complete canonical surface using `REVIEW_REQUEST.md` and the shared
surface-digest implementation. Claude prepares the reviewer dossier and checks
coverage against every required token. A qualifying external reviewer must
read the current target, disclose prior involvement and conflicts, publish a
dated report, and return `pass` or `pass-with-findings` for the complete scope.
Thomas verifies identity and independence before ledger admission.

### G3 — Production cryptography

Continue the documented leading path: exact-version libsodium 1.0.22 with a
narrow signer seam, subject to binding, build, platform, vulnerability, and
current-version audit qualification. The design does not treat the 2017 audit
of older libsodium versions as an audit of 1.0.22.

Implementation must cover library/build identity, constant-time boundary,
malformed-input refusal, rotation, recovery, revocation, and delegation. It
must keep private keys out of receipts, logs, repository files, and test
artifacts and define process-memory and zeroization limits. A separate
cryptography reviewer produces the G3 report for the exact build and supported
platforms. Paid review is permitted only after explicit expenditure approval
and with the financial relationship disclosed.

The binding choice is `BLOCKED` until a reproducible qualification compares a
maintained binding with a minimal pinned binding. Thomas owns the decision;
wire compatibility, build identity, secret exposure, maintenance, and audit
scope are the comparators.

### G4 — Independent adapters and validator

Prepare one clean-room input pack containing only normative schemas, vectors,
public conformance requirements, and attribution terms. It must exclude
Reference Code. Claude may draft the pack and answer specification questions in
public, but each implementer owns its design and source history.

Requirements:

- two different producer identities and implementation repositories;
- provenance review for any implementation with historical Reference Code
  exposure;
- untrusted candidates run only in separate least-privilege processes or
  containers with explicit filesystem, network, secret, CPU, memory, and
  deadline limits;
- both adapters consume the same erratum and produce exact receipt IDs and
  digests against the same commit and surface digest;
- a third producer validates both exact receipts and publishes the combined
  result.

Structural identity checks do not authenticate people or conflicts; Thomas
performs and records that human verification.

### G5 — Three-system interoperability

Initial discovery candidates are Mem0 Platform, Zep, and Amazon Bedrock
AgentCore Memory because their official documentation exposes distinct managed
memory systems. They are candidates, not approved systems and not evidence.
Each must complete the nomination fields in `PHASE3_SYSTEMS.md`. Substitution is
allowed when a candidate cannot authorize the experiment, expose the required
surface, publish evidence, or provide an operator identity.

No account is created and no charge is incurred until approval resolves those
contract facts. One system must be deliberately configured as nonconforming;
one must retain genuinely opaque or incomplete coverage; one must exercise
mixed-artifact lineage.

### G6 — Operational qualification

The deployment operator declares workload, failure domain, observation window,
and numeric thresholds before execution. Universal latency, throughput, RTO,
RPO, overload, or incident-response numbers are not invented by the repository.
Missing operator thresholds remain `BLOCKED` with the named operator as owner.

The independent producer evaluates all ten scopes from
`docs/OPERATIONAL_READINESS.md`. Nine passes do not qualify. A failed comparator
cannot be overridden by a prose `pass`. Raw artifacts must exclude prohibited
content while remaining sufficient for independent reproduction.

## Claude orchestration boundary

Claude is used aggressively for:

- source and prior-art research;
- dossier, clean-room pack, test, runbook, outreach, and report-template drafts;
- implementation and differential-test proposals;
- evidence-schema and comparator validation;
- review of incoming findings against exact repository requirements;
- risk ranking and next-action recommendations.

Every Claude review is read-only, model-identified, exact-file-covered, and
workload-budgeted. Claude output is internal maker/checker evidence unless an
external gate explicitly permits it. Claude cannot invent a third-party
identity, authorize data or spending, conceal a conflict, or sign for another
producer. Claude can solve those workflow problems by finding and coordinating
the real authorized role.

## Data, telemetry, and retention

Stage 0-2 data contains synthetic labels and stable synthetic identifiers only.
Run artifacts store hashes, measurements, dispositions, and content-free
erasure evidence. They never store raw secrets, credentials, private keys,
customer content, or erased values.

Each run declares retention and deletion before execution. Kill or cancellation
stops new imports, quarantines the declared root, preserves non-sensitive raw
evidence needed for diagnosis, revokes temporary credentials, and executes the
system-specific cleanup procedure. Evidence retention never overrides an
erasure obligation.

## Error handling and safe stop

Stop the affected stage without upgrading a gate when any of these occurs:

- authorization, identity, target, digest, deployment, threshold, or evidence
  binding is missing or changes;
- a required system or report producer is not independent under the declared
  role policy;
- any required store cannot quarantine affected state;
- prohibited content appears in telemetry or evidence;
- a required measurement, operation, system, scope, or raw artifact is absent;
- cryptographic build or key lifecycle cannot be independently qualified;
- untrusted adapter code cannot be isolated;
- rollback or recovery exceeds its predeclared threshold;
- CI, publication checks, or GitHub freshness fail;
- a new actionable external finding invalidates the current design or target.

Retries require a changed hypothesis, intervention, evidence source, or gate
coverage. Authentication, schema, authorization, and identity failures are not
transient retries.

## Commercial and ownership model

The initial commercial offer is a controlled specification-evaluation service,
not an unconditional production certification. Deliverables are the synthetic
fixture pack, system-specific gap report, measurements, remediation plan, and
evidence package. Customer obligations include explicit authorization, a named
operator, synthetic-data entry, disclosed conflicts, and acceptance of stop and
retention rules.

Required accessible product wording:

> Implements LLM Errata by Thomas Willner —
> https://github.com/thomaswillner/llm-errata

Third-party implementations add a no-endorsement statement. Commercial use of
Reference Code needs a separate written licence from Thomas Willner. Pilot fees
or paid audits require an approved commercial agreement and budget; neither is
implied by this design.

## Implementation decomposition

The program is too large for one implementation plan. It decomposes in this
order, with one approved specification and plan per slice:

1. **Pilot admission control:** schema, validator, state machine, synthetic root,
   negative tests, `make pilot`, and operator runbook.
2. **G3 signer qualification:** binding decision, production signer, lifecycle,
   platform matrix, and audit dossier.
3. **G4 clean-room execution:** input pack, isolation harness, evidence intake,
   and validator workflow.
4. **G2 exact-target review:** final dossier, reviewer coordination, findings,
   remediation, and qualifying report admission.
5. **G5 shadow interoperability:** approved systems, three experiment arms,
   measurements, and independent report.
6. **G6 limited-production qualification:** deployment, declared SLOs, ten
   exercises, independent report, and ledger reconciliation.
7. **Production verdict and expansion:** exact-head review, CI, freshness,
   release, verdict change, and evidence-expiry monitoring.

The first implementation plan after owner review covers slice 1 only.

## Verification

Every slice requires:

1. a red-capable focused test for each advertised refusal or comparator;
2. focused tests passing on supported Python versions;
3. `git diff --check`;
4. `make check` and `make links` when citations change;
5. Claude read-only review of the exact changed surface, with findings resolved
   or explicitly blocking;
6. exact-head GitHub CI on Python 3.11 and 3.13;
7. repository-wide GitHub freshness receipt after the last mutation; and
8. unchanged readiness status unless the gate's own qualifying evidence exists.

## Design acceptance

This design is acceptable when it contains no placeholder, contradiction,
unstated authority expansion, invented operational threshold, or path that lets
internal work qualify as external evidence. Owner approval authorizes a detailed
implementation plan for Pilot Admission Control; it does not pre-approve paid
services, legal agreements, real data, or the final `PROD_READY` verdict.
