# Production readiness

## Current status

| Field | Value |
|---|---|
| Version | 0.4.1 |
| Verdict | **NOT_PROD_READY** |
| Ledger | `readiness/production-readiness.json` |

Build health means the repository's deterministic structure/metadata checks, bounded-claim guard, readiness-evidence honesty check, and self-tests pass. Production readiness is a separate, evidence-based decision: it requires every gate below to pass with the evidence stated for that gate. Green local tests and agent reviews are useful internal evidence, but neither is external evidence and neither can change an external gate to `PASS`.

This matrix governs claims of production readiness, not whether an experimental
release may be published. A release may ship with blocked gates when its
version, source, tests, limitations, ownership, licence, and evidence boundaries
are internally consistent and the release remains labeled `NOT_PROD_READY`.
G2–G6 therefore remain active development and validation work rather than a
requirement to wait indefinitely for unsolicited external reviewers.

## Readiness matrix

| Gate | Criterion | Current status | Current evidence | Next evidence required |
|---|---|---|---|---|
| G1 | VERSION, SECURITY support policy, readiness matrix, and check documentation remain aligned; negative tests protect every machine-enforced binding. | `PASS` | `VERSION`, `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, `PRODUCTION_READINESS.md`, readiness ledger, both checkers, and their focused tests. | Maintain document, ledger, matrix, checker, and test consistency with each release. |
| G2 | Complete Phase 2 implementation, including provider-neutral semantic probes, and an independent reviewer evaluates the complete conformance surface. | `BLOCKED` | Phase 2 implementation includes conflict-disclosed remediation for split-view equivocation, unsupported empty enumeration, checkpoint coverage, and adapter-contract completeness, plus schemas, semantic probes, adapter-level conformance, validator anti-vacuity controls, key rotation, invalid-target, confidentiality, and receipt binding; no qualifying independent review is recorded. | Dated independent external conformance-review result covering the exact complete Phase 2 surface after remediation. |
| G3 | Production signing uses an audited constant-time library through the Signer seam and independent security review covers key lifecycle. | `BLOCKED` | `THREAT_MODEL.md` and `docs/CRYPTOGRAPHY_QUALIFICATION.md` record the internal candidate assessment. PyCA passed wire-compatibility checks but documents no external project audit; libsodium has audited lineage only for older versions. No production signer or qualifying independent lifecycle review exists. | Qualify exact current library, binding, build, and platforms; implement rotation, recovery, revocation, and delegation; obtain dated independent security review. |
| G4 | Two independently authored adapters consume the same erratum and a third-party validator evaluates their receipts consistently. | `BLOCKED` | Inspeximus `v2.7.0` is one tagged externally authored adapter candidate with disclosed v2.6.1 reference-code contamination and a claimed clean-room rewrite. It targets historical commit `a477fe4f5c86730031b6285d9505778fb8eec060`; provenance, current-target behavior, a second candidate, and a third-party validator result remain unverified. | Rebind candidates to the current immutable target; obtain dated evidence from two independently authored adapters, including separate provenance review where needed, and a separately produced third-party validator result. |
| G5 | One user-controlled synthetic root completes the declared experiment across three independently operated memory systems. | `BLOCKED` | `ROADMAP.md` records interoperability experiment requirement; no approved systems or measured result are recorded. | Approved third-party systems, authorized synthetic-data experiment, and measured report. |
| G6 | All ten operational scopes pass from one independent report bound to exact commit and deployment, with declared thresholds and measured comparators. | `BLOCKED` | No independent report binds an exact commit and deployment to passing measured comparators for all ten operational scopes. | One qualifying independent report with declared workload, platform, failure domain, observation window, numeric thresholds, raw artifacts, and passing measurements for every scope. |

## Approval boundaries

- External review: obtain authorization before requesting, transmitting artifacts for, or recording an external review. [REVIEW_REQUEST.md](REVIEW_REQUEST.md) is a public request template, not external review evidence.
- Third-party systems: obtain approval for each system, account, integration, and interaction before interoperability work.
- Real data: synthetic data is required unless explicit approval names permitted real-data scope, handling, and retention.
- Final verdict change: only an authorized maintainer may change the ledger verdict after every gate has qualifying evidence; implementation, local testing, and agent review alone cannot do so.

## Validate the current state

```bash
make readiness
```

Exit `0` validates honesty and structural validity of the recorded state. It does **not** mean the project is production ready; the current honest verdict remains `NOT_PROD_READY` until every required gate passes.
