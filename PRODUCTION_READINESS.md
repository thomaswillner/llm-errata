# Production readiness

## Current status

| Field | Value |
|---|---|
| Version | 0.3.0 |
| Verdict | **NOT_PROD_READY** |
| Ledger | `readiness/production-readiness.json` |

Build health means the repository's deterministic structure/metadata checks, bounded-claim guard, readiness-evidence honesty check, and self-tests pass. Production readiness is a separate, evidence-based decision: it requires every gate below to pass with the evidence stated for that gate. Green local tests and agent reviews are useful internal evidence, but neither is external evidence and neither can change an external gate to `PASS`.

## Readiness matrix

| Gate | Criterion | Current status | Current evidence | Next evidence required |
|---|---|---|---|---|
| G1 | VERSION, SECURITY support policy, readiness matrix, and check documentation remain aligned; negative tests protect every machine-enforced binding. | `PASS` | `VERSION`, `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, `PRODUCTION_READINESS.md`, readiness ledger, both checkers, and their focused tests. | Maintain document, ledger, matrix, checker, and test consistency with each release. |
| G2 | Complete Phase 2 implementation, including provider-neutral semantic probes, and an independent reviewer evaluates the complete conformance surface. | `BLOCKED` | Phase 2 implementation includes conflict-disclosed remediation for split-view equivocation and unsupported empty enumeration, plus schemas, checkpoints, semantic probes, key rotation, invalid-target, confidentiality, and receipt binding; no qualifying independent review is recorded. | Dated independent external conformance-review result covering the exact complete Phase 2 surface after remediation. |
| G3 | Production signing uses an audited constant-time library through the Signer seam, with independent security review of key lifecycle. | `BLOCKED` | `THREAT_MODEL.md` and `docs/CRYPTOGRAPHY_QUALIFICATION.md` record the internal candidate assessment. PyCA passed wire-compatibility checks but documents no external project audit; libsodium has audited lineage only for older versions. No production signer or qualifying independent lifecycle review exists. | Qualify exact current library, binding, build, and platforms; implement rotation, recovery, revocation, and delegation; obtain dated independent security review. |
| G4 | Two independently authored adapters consume the same erratum and a third-party validator evaluates their receipts consistently. | `BLOCKED` | `ROADMAP.md` records this dependency; no independent implementations or validator result are recorded. | Dated evidence from two independent adapters and separately produced third-party validator result. |
| G5 | One user-controlled synthetic root completes declared experiment across three independently operated memory systems. | `BLOCKED` | `ROADMAP.md` records interoperability experiment requirement; no approved systems or measured result are recorded. | Approved third-party systems, authorized synthetic-data experiment, and measured report. |
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
