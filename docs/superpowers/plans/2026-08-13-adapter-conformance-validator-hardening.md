# Adapter Conformance and Validator Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish an independently authored adapter-conformance corpus and fail-closed validator as LLM Errata 0.4.0 without upgrading blocked production-readiness gates.

**Architecture:** A versioned JSON corpus describes complete adapter outcomes, normative predecessor citations, required target-instance calls, and exact mutation counter-results. `prototype/conformance.py` validates and executes the corpus through a provider-neutral binding protocol and reference binding; the CLI emits a canonical report. Release metadata records ownership, contributor provenance, and unchanged readiness status.

**Tech Stack:** Python 3.11/3.13 standard library, JSON, unittest, existing LLM Errata controller/adapters, GitHub Actions and Releases.

**Spec:** `docs/superpowers/specs/2026-08-13-adapter-conformance-validator-hardening-design.md`

## Global Constraints

- LLM Errata files authored here remain owned by Thomas Willner.
- Do not copy or vendor `DanceNitra/agora` candidate runner or fixture.
- Preserve specific attribution to Rastislav Drahos/DanceNitra and immutable source commit.
- Preserve existing attributed commercial specification-implementation grant and restricted Reference Code boundary.
- Keep G2 through G6 blocked unless their existing independent evidence contracts pass.
- Standard-library only; all fixtures use synthetic data.
- Every production-code behavior starts with a failing public-seam test.
- The corpus pins the predecessor normative target `ac4468faf73c2cc7949dd29b2a2a151f5bd23116` and digest `7e0d6c88c1ca3a87743ac70ba2a3dfea0b350d112d2d3c59a3c6cbb537568f12`. Runtime source identity is separately reported because a file cannot non-circularly contain the commit and digest that include its own bytes.

---

### Task 1: Corpus and source/citation validation

**Files:**
- Create: `spec/adapter-conformance.json`
- Create: `prototype/conformance.py`
- Create: `tests/test_conformance.py`

**Interfaces:**
- Produces: `load_corpus(path: Path, source_root: Path) -> AdapterCorpus`
- Produces: `ConformanceInputError`

- [ ] **Step 1: Write failing corpus validation tests**

Tests require exact schema keys, immutable commit availability, predecessor surface digest, exact source path/quotation, complete expectations, exact mutation counter-results, and provenance fields. Negative copies change one field at a time and must raise `ConformanceInputError`.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python3 -m unittest tests.test_conformance.CorpusValidation -v`
Expected: import failure because `prototype.conformance` does not exist.

- [ ] **Step 3: Implement typed corpus parser and source binder**

Use frozen dataclasses, exact-key validation, `git cat-file`/`git show`, and the pinned predecessor manifest/digest algorithm. Reject dirty identity ambiguity only when a run claims current committed identity; normative citation validation always reads immutable target bytes.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `python3 -m unittest tests.test_conformance.CorpusValidation -v`
Expected: all corpus validation tests pass.

- [ ] **Step 5: Commit**

`git commit -m "feat: define adapter conformance corpus"`

### Task 2: Target-instance tracing and complete outcome comparison

**Files:**
- Modify: `prototype/conformance.py`
- Modify: `tests/test_conformance.py`

**Interfaces:**
- Produces: `TracingAdapter`
- Produces: `compare_complete_outcome(expected, observed) -> tuple[str, ...]`
- Produces: `ConformanceBinding` protocol and `ReferenceConformanceBinding`

- [ ] **Step 1: Write failing tracing and comparison tests**

Tests prove an unrelated object with matching method names cannot satisfy the control, every unspecified triad/aggregate failure is rejected, and missing/extra observation fields fail.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python3 -m unittest tests.test_conformance.TargetTracing tests.test_conformance.CompleteComparison -v`
Expected: missing types/functions.

- [ ] **Step 3: Implement proxy, binding protocol, reference binding, and strict comparator**

Proxy only records calls routed through the exact wrapped instance. Reference binding builds synthetic lineage and exposes stable synthetic proposition labels/counts without private production data.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `python3 -m unittest tests.test_conformance.TargetTracing tests.test_conformance.CompleteComparison -v`

- [ ] **Step 5: Commit**

`git commit -m "feat: trace exact adapter conformance outcomes"`

### Task 3: Exact mutations and validator anti-vacuity controls

**Files:**
- Modify: `prototype/conformance.py`
- Modify: `tests/test_conformance.py`

**Interfaces:**
- Produces: `validate_adapter_conformance(corpus_path, source_root, binding_factory) -> ConformanceReport`
- Produces: `run_validator_anti_vacuity_controls() -> tuple[ControlResult, ...]`

- [ ] **Step 1: Write failing behavioral and mutation tests**

Tests cover five honest cases, exact counter-results, exception-as-failure, mutation no-op rejection, empty receipt, no-op feed acceptance, and constant-`unknown` semantic aggregation.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python3 -m unittest tests.test_conformance.AdapterCases tests.test_conformance.AntiVacuity -v`

- [ ] **Step 3: Implement execution, exact mutations, report, and controls**

Each case runs honest and mutated bindings independently. Mutation success requires the declared complete semantic counter-result. Unexpected exceptions produce failed control evidence.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `python3 -m unittest tests.test_conformance -v`

- [ ] **Step 5: Commit**

`git commit -m "feat: reject vacuous conformance passes"`

### Task 4: CLI and documentation

**Files:**
- Modify: `prototype/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `spec/README.md`
- Modify: `prototype/README.md`
- Modify: `IDEA.md`
- Modify: `ROADMAP.md`
- Modify: `THREAT_MODEL.md`
- Modify: `INDEPENDENT_IMPLEMENTATION.md`
- Modify: `SOURCES.md`

**Interfaces:**
- Produces: `errata adapter-conformance --corpus ... --source-root ... --binding ...`
- Exit `0` pass, `1` behavioral/control failure, `2` invalid/inconclusive evidence.

- [ ] **Step 1: Write failing subprocess CLI tests**

Tests assert canonical JSON, source/runtime identity, five cases, three controls, provenance, evidence boundary, and all three exit classes.

- [ ] **Step 2: Run CLI tests and verify RED**

Run: `python3 -m unittest tests.test_cli.AdapterConformanceCommand -v`

- [ ] **Step 3: Implement CLI and document normative multiplicity/provenance boundary**

CLI imports `module:factory` only when explicitly supplied; default uses reference binding. Documentation states stable proposition identity/count scope and `unknown` behavior.

- [ ] **Step 4: Run focused and full conformance tests**

Run: `python3 -m unittest tests.test_conformance tests.test_cli -v`

- [ ] **Step 5: Commit**

`git commit -m "feat: publish adapter conformance command"`

### Task 5: Version 0.4.0 and release/readiness metadata

**Files:**
- Modify: `VERSION`
- Modify: `CITATION.cff`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `SECURITY.md`
- Modify: `readiness/production-readiness.json`
- Modify: `PRODUCTION_READINESS.md`
- Modify: `scripts/validate_repo.py`
- Modify: `tests/test_validate_repo.py`
- Modify: `scripts/check_readiness.py`
- Modify: `tests/test_readiness.py`
- Modify: `docs/PUBLICATION_LOG.md`

**Interfaces:**
- Produces: internally aligned release version `0.4.0`
- Preserves: verdict `NOT_PROD_READY`, G1 `PASS`, G2-G6 `BLOCKED`

- [ ] **Step 1: Write failing release-alignment tests**

Tests require 0.4.0 across version, citation, maturity, security, ledger, matrix, changelog, and contributor provenance. They require unchanged gate statuses and current G2 evidence to name adapter conformance without treating it as external evidence.

- [ ] **Step 2: Run release tests and verify RED**

Run: `python3 -m unittest tests.test_validate_repo tests.test_readiness -v`

- [ ] **Step 3: Update metadata and validators**

Use release date 2026-08-13. Record independent implementation boundary and exact contributor provenance. Do not change licence grants or gate statuses.

- [ ] **Step 4: Run release tests and verify GREEN**

Run: `python3 -m unittest tests.test_validate_repo tests.test_readiness -v`

- [ ] **Step 5: Commit**

`git commit -m "release: prepare 0.4.0 adapter conformance hardening"`

### Task 6: Full verification, review, integration, and publication

**Files:**
- Review all changes since `c205fa07e818c682f2715e58c02b7e35bfe2ceb0`

- [ ] **Step 1: Run full local gates**

Run: `make check`
Run: `make publication`
Run: `make links` because `SOURCES.md` changes.

- [ ] **Step 2: Run two-axis standards/spec review**

Compare `c205fa0...HEAD` against AGENTS.md, CONTRIBUTING.md, and approved design. Fix all Critical/Important findings with focused regression tests.

- [ ] **Step 3: Push scoped branch and update PR chain**

Push `agent/adapter-conformance-release`, create PR against `agent/g2-publication`, and post exact test/provenance/readiness evidence.

- [ ] **Step 4: Obtain exact-head CI and integrate in dependency order**

Require Python 3.11 and 3.13 checks on exact head. Merge adapter branch, PR #8, then PR #3 only when each resulting head is verified and no new actionable feedback exists.

- [ ] **Step 5: Publish release**

Backfill GitHub release object for immutable `v0.3.0` if absent. Tag current verified `main` as `v0.4.0`, publish release notes with `NOT_PROD_READY`, ownership/licence boundary, contributor thanks, and G2-G6 blockers.

- [ ] **Step 6: Reply to contributors**

Freshly inventory all external authors. Reply individually with what their contribution changed, exact release evidence, unchanged gate limits, and one optional focused follow-up where useful.

- [ ] **Step 7: Final freshness sweep**

Repeat all GitHub surfaces, classify every delta, validate schema-v2 freshness receipt, and reopen loop for any new actionable feedback.
