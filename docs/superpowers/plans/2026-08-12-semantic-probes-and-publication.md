# Semantic Probes and Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the internal Phase 2 semantic-probe surface, publish independent-review and implementation calls, and expose the work through an evidence-bounded draft PR.

**Architecture:** A provider-neutral semantic module records exact verifier configuration and validates structured observations. A recorded-fixture adapter makes conformance deterministic and offline. Publication artifacts remain documentation and GitHub calls; they never change readiness gates without external evidence.

**Tech Stack:** Python 3.11+ standard library, `dataclasses`, `enum`, `hashlib`, `json`, `argparse`, `unittest`, GitHub Actions.

## Global Constraints

- Preserve correction, supersession, and erasure as distinct operations.
- Preserve quarantine-before-repair and negative-positive-preservation semantics.
- Never convert missing, inconclusive, malformed, configuration-drifted, or provider-error evidence into success.
- Erasure reports and fixtures must not retain the erased value.
- `make check` remains offline, standard-library-only, and green.
- Internal implementation cannot change G2 from `BLOCKED`; dated independent review is also required.
- Publication must state `NOT_PROD_READY` and link the canonical repository.

---

### Task 1: Provider-neutral semantic evidence model

**Files:**
- Create: `prototype/semantic.py`
- Test: `tests/test_semantic.py`

**Interfaces:**
- Produces: `ProbeKind`, `ObservationVerdict`, `SemanticCoverage`, `SemanticProbe`, `VerifierConfig`, `SemanticObservation`, `SemanticProbeReport`, `SemanticVerifier`, `RecordedSemanticVerifier`, and `SemanticProbeRunner`.

- [ ] Write tests for canonical configuration digests, all-pass verification, required failure, inconclusive/error/missing/duplicate/configuration-drift results, deterministic serialization, and erasure non-disclosure.
- [ ] Run `python3 -m unittest tests.test_semantic -v` and confirm the new module is missing.
- [ ] Implement immutable data models, canonical JSON serialization, strict parsing, the verifier protocol, recorded adapter, and fail-closed aggregation.
- [ ] Run the focused tests and confirm they pass.
- [ ] Commit with `feat: add provider-neutral semantic probe evidence`.

### Task 2: Offline conformance fixtures and CLI

**Files:**
- Create: `spec/semantic/probes.json`
- Create: `spec/semantic/verifier-config.json`
- Create: `spec/semantic/observations.json`
- Modify: `prototype/cli.py`
- Modify: `spec/README.md`
- Modify: `prototype/README.md`
- Test: `tests/test_cli.py`
- Test: `tests/test_semantic.py`

**Interfaces:**
- Consumes: strict `from_dict` methods and `SemanticProbeRunner.run` from Task 1.
- Produces: `errata semantic-test --probes PATH --config PATH --observations PATH` with exit `0`, `1`, or `2`.

- [ ] Add failing CLI tests for verified, failed, and unknown fixture sets plus malformed input.
- [ ] Add synthetic manifests containing no real or erased personal data.
- [ ] Implement the CLI command and canonical JSON report output.
- [ ] Document fixture format, command, exit codes, privacy boundary, and provider-adapter seam.
- [ ] Run focused CLI and semantic tests.
- [ ] Commit with `feat: publish semantic probe conformance fixtures`.

### Task 3: Readiness, roadmap, and publication integration

**Files:**
- Modify: `ROADMAP.md`
- Modify: `README.md`
- Modify: `PRODUCTION_READINESS.md`
- Modify: `readiness/production-readiness.json`
- Modify: `CHANGELOG.md`
- Modify: `PUBLISHING.md`
- Modify: `scripts/validate_repo.py`
- Modify: `tests/test_validate_repo.py`

**Interfaces:**
- Consumes: Task 1 and Task 2 artifacts.
- Produces: accurate Phase 2 item 6 implementation status while G2 remains `BLOCKED` pending independent review.

- [ ] Add regression tests requiring review and implementation-call artifacts and preventing Phase 2 completion from upgrading G2.
- [ ] Update maturity language, roadmap status, evidence references, and publication workflow.
- [ ] Run `make check` and `git diff --check`.
- [ ] Commit with `docs: open independent LLM Errata validation program`.

### Task 4: Review, push, and public GitHub calls

**Files:**
- Review all changes from the branch base.

**Interfaces:**
- Produces: pushed branch, draft PR, reviewer recruitment issue, independent-implementation issue, and public URL ledger.

- [ ] Conduct separate specification and code-quality review; repair every load-bearing finding.
- [ ] Run `make check`, `make links`, `git diff --check`, and secret-safe staged-content inspection.
- [ ] Push `agent/g2-publication` and create a draft PR targeting `agent/prod-readiness` until PR #3 merges.
- [ ] Create GitHub issues for independent review, implementation permission/recruitment, and Phase 3 system nominations.
- [ ] Publish authenticated external announcements where platform access and rules permit, then record exact URLs without upgrading readiness gates.

