# G6 Operational Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make G6 pass only from one independent, commit- and deployment-bound report with passing measured evidence for all ten operational scopes.

**Architecture:** `scripts/check_readiness.py` adds strict G6 report validators and a canonical G6 surface digest, then specializes external-pass qualification by gate. Human docs define operator-owned thresholds without fabricating values. Ledger stays `BLOCKED` until genuine evidence arrives.

**Tech Stack:** Python 3.11+ standard library, JSON, SHA-256, Git object inspection, `unittest`, Markdown.

## Global Constraints

- Keep one gate ID: `G6`.
- Require exactly ten unique normative scope tokens.
- Every measurement has finite value and threshold, one unit, a supported comparator, and raw evidence reference.
- Missing thresholds remain `BLOCKED`.
- Internal producers, repository CI, invitations, and example reports never qualify.
- Exact current checkout and reviewed-commit surface digests must match.
- Current verdict remains `NOT_PROD_READY` without genuine external evidence.

---

### Task 1: G6 evidence validator and digest

**Files:**
- Modify: `scripts/check_readiness.py`
- Modify: `tests/test_readiness.py`

**Interfaces:**
- Produces: `G6_SCOPE`, `G6_ATTESTATION`, `g6_surface_files`, `g6_surface_digest`, `g6_surface_digest_at_commit`, `valid_g6_operational_evidence`, and `qualifying_g6_operational_evidence`.
- Extends gate validation so G2 uses G2 qualification, G6 uses G6 qualification, and other external gates retain generic independent evidence behavior.

- [ ] **Step 1: Write a complete synthetic report fixture helper**

  In `tests/test_readiness.py`, build ten literal scope results with hand-derived passing measurements. Commit a temporary repository copy before binding its full commit and surface digest.

- [ ] **Step 2: Write failing positive and mutation tests**

  Prove a complete report validates and qualifies. Mutate one field per test to reject generic URL, producer identity, relationship, conflicts, attestation, commit, digest, deployment identity, platform, artifact digest, provenance, workload, volume, concurrency, duration, failure domain, observation window, missing/duplicate/extra scope, artifacts, measurements, value, unit, comparator, threshold, evidence ref, failed comparator, scope status, and report result.

- [ ] **Step 3: Verify RED**

  Run `python3 -m unittest tests.test_readiness -v`. Expected: imports for G6 symbols fail.

- [ ] **Step 4: Implement strict validation**

  Use exact-key validation for report subobjects where forward ambiguity would be unsafe. Reject `bool` as numeric, reject `math.isfinite(value) is False`, validate ISO timestamps and ordering, require positive workload volume/concurrency/duration, and evaluate comparators through an explicit mapping rather than `eval`.

- [ ] **Step 5: Bind gate PASS semantics**

  When G6 status is `PASS`, require at least one `qualifying_g6_operational_evidence()` entry. While blocked, reject malformed external G6 entries but accept repository evidence. Keep G2 behavior unchanged.

- [ ] **Step 6: Verify GREEN**

  Run focused readiness tests and full test discovery.

- [ ] **Step 7: Commit**

  `git add scripts/check_readiness.py tests/test_readiness.py && git commit -m "feat: enforce measured G6 evidence"`

### Task 2: Operational-readiness operator contract

**Files:**
- Create: `docs/OPERATIONAL_READINESS.md`
- Modify: `PRODUCTION_READINESS.md`
- Modify: `readiness/production-readiness.json`
- Modify: `ROADMAP.md`
- Modify: `SECURITY.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Produces the ten-scope operator workflow and exact G6 matrix/ledger wording.
- Ledger cites `docs/OPERATIONAL_READINESS.md`, checker, and tests but remains `BLOCKED`.

- [ ] **Step 1: Add failing matrix-binding tests**

  Require exact G6 criterion, current-evidence, and next-evidence cells; mutation to “internal tests are enough” must fail.

- [ ] **Step 2: Verify RED**

  Run focused readiness tests. Expected: G6 canonical constants and document are absent.

- [ ] **Step 3: Write operational contract and synchronize status**

  Document each scope, envelope, measurements, comparators, independence, operator threshold ownership, submission workflow, and a deliberately incomplete non-qualifying skeleton with no invented numbers. Update matrix/ledger language and repository evidence references exactly.

- [ ] **Step 4: Verify GREEN**

  Run focused readiness tests and `python3 scripts/check_readiness.py`.

- [ ] **Step 5: Commit**

  `git add docs/OPERATIONAL_READINESS.md PRODUCTION_READINESS.md readiness/production-readiness.json ROADMAP.md SECURITY.md CHANGELOG.md tests/test_readiness.py && git commit -m "docs: publish G6 operational evidence contract"`

### Task 3: Pin primary grounding sources

**Files:**
- Modify: `SOURCES.md`
- Modify: `docs/OPERATIONAL_READINESS.md`

**Interfaces:**
- Records official title, version, canonical URL, access date `2026-08-12`, and exact use for NIST SP 800-61r3, NIST SP 800-218, SLSA v1.2, OpenTelemetry signals/semantic conventions, and OWASP Logging Cheat Sheet.

- [ ] **Step 1: Verify official current source metadata**

  Re-open official primary sources because these facts are version-sensitive. Record no source as project certification and derive no numeric operator threshold from generic guidance.

- [ ] **Step 2: Add source records and inline citations**

  Keep source statement, project inference, and operator decision distinct.

- [ ] **Step 3: Validate**

  Run `make check`, `make links`, and `git diff --check`. Retry link checking once only if failure is a classified remote disconnect; otherwise report the exact failure.

- [ ] **Step 4: Commit**

  `git add SOURCES.md docs/OPERATIONAL_READINESS.md && git commit -m "docs: ground operational readiness scopes"`

### Task 4: Exact-head validation and publication update

**Files:**
- Modify: `docs/PUBLICATION_LOG.md`

**Interfaces:**
- Produces pushed exact-head commit, updated draft PR, exact G2 digest, and an Issue #4 comment requesting review of the final Phase 2 surface.

- [ ] **Step 1: Run local release gates**

  Run `make check`, `make links`, `make cli-demo`, `git diff --check`, and secret-safe staged-content inspection.

- [ ] **Step 2: Compute final G2 digest**

  Run `python3 -c 'from scripts.check_readiness import g2_surface_digest; print(g2_surface_digest())'` after all Phase 2 artifacts are committed.

- [ ] **Step 3: Update publication log**

  Record exact commit/digest only after commit identity exists; use a follow-up documentation commit and state that its non-G2 publication-log bytes do not alter the surface digest.

- [ ] **Step 4: Push and publish review request**

  Push branch, update Issue #4 with exact reviewed commit and digest, link PR #8, and request qualifying independent review. Do not change G2 or G6 status from the request.

- [ ] **Step 5: Verify exact-head CI**

  Inspect checks belonging to pushed head, not cached predecessor status. Retry one classified `TemporaryDirectory` cleanup race or link-check remote disconnect once; diagnose any other failure.
