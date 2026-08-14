# Quarantine Checkpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Require an authenticated, durable, state-bound quarantine checkpoint before Phase 2 CLI repair.

**Architecture:** `prototype/checkpoints.py` owns canonical checkpoint data and atomic persistence. `Importer` exposes separate authenticated quarantine and checkpointed-repair operations while retaining `repair()` as Phase 1 composition. `Workspace` resolves deterministic checkpoint paths; CLI orchestrates exactly one pending erratum and consumes evidence only after durable receipt and applied-state writeback.

**Tech Stack:** Python 3.11+ standard library, frozen dataclasses, SHA-256, canonical JSON, `os.replace`, SQLite, `unittest`, `argparse`.

## Global Constraints

- Preserve correction, supersession, and erasure as distinct operations.
- Quarantine must complete before rebuild begins.
- Preserve negative, positive, and preservation checks.
- Missing, opaque, malformed, drifted, or replayed evidence never becomes verified.
- Erasure checkpoints contain identifiers and commitments, not erased content.
- Keep `Importer.repair()` as Phase 1 in-process composition.
- `make check` remains offline and standard-library-only.

---

### Task 1: Canonical checkpoint model and atomic store

**Files:**
- Create: `prototype/checkpoints.py`
- Create: `tests/test_checkpoints.py`

**Interfaces:**
- Produces: `CheckpointError`, `AdapterCheckpoint`, `QuarantineCheckpoint`, `CheckpointStore`.
- `QuarantineCheckpoint.from_dict(value: object) -> QuarantineCheckpoint` performs strict type/key validation.
- `QuarantineCheckpoint.canonical_digest() -> str`, `to_dict() -> dict[str, object]`, and `with_consumed(timestamp: str) -> QuarantineCheckpoint` preserve identity semantics.
- `CheckpointStore.write(checkpoint)`, `load(path)`, and `consume(path, timestamp)` use atomic same-directory replacement.

- [ ] **Step 1: Write failing model tests**

  Add literal-fixture tests for deterministic digest, strict keys/types, digest mutation rejection, consumed-state identity, safe filename validation, atomic round trip, and invalid JSON refusal. Each test names the production mutation it catches.

- [ ] **Step 2: Verify RED**

  Run `python3 -m unittest tests.test_checkpoints -v`.

  Expected: `ModuleNotFoundError: No module named 'prototype.checkpoints'`.

- [ ] **Step 3: Implement minimal checkpoint model**

  Use frozen dataclasses and canonical `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`. Reject booleans where integers are required, non-ISO UTC timestamps, path separators, duplicate adapter names, unsorted/duplicate artifact IDs, and any digest mismatch. Exclude only `checkpoint_digest`, `consumed`, and `consumed_at` from identity bytes.

- [ ] **Step 4: Implement atomic persistence**

  Create a temporary regular file in checkpoint directory, write UTF-8 JSON plus newline, flush and `os.fsync`, `os.replace`, then `fsync` directory. Refuse symlink targets and non-regular existing files. `consume` loads and validates before atomically writing `with_consumed()`.

- [ ] **Step 5: Verify GREEN**

  Run `python3 -m unittest tests.test_checkpoints -v` and `python3 -m unittest discover -s tests -t .`.

- [ ] **Step 6: Commit**

  `git add prototype/checkpoints.py tests/test_checkpoints.py && git commit -m "feat: add durable quarantine checkpoints"`

### Task 2: Controller split between quarantine and checkpointed repair

**Files:**
- Modify: `prototype/controller.py`
- Modify: `prototype/sqlite_store.py`
- Test: `tests/test_controller.py`
- Test: `tests/test_sqlite_store.py`

**Interfaces:**
- Produces: `Importer.quarantine(erratum: Erratum) -> QuarantineCheckpoint`.
- Produces: `Importer.repair_quarantined(erratum: Erratum, checkpoint: QuarantineCheckpoint) -> Receipt`.
- Produces: adapter inspection `is_quarantined(artifact_ids: tuple[str, ...]) -> bool` for checkpoint verification.
- `Importer.repair()` composes `quarantine()` then `repair_quarantined()` without durable persistence.

- [ ] **Step 1: Write failing controller tests**

  Prove authenticated quarantine returns complete adapter records; opaque required store is unknown; no rebuild event occurs; checkpointed repair does not quarantine twice; wrong erratum, state root, adapter set, artifact set, limitation, or ungated state is refused before rebuild; correction, supersession, erasure, and triad behavior remain unchanged.

- [ ] **Step 2: Verify RED**

  Run focused controller/SQLite tests. Expected: missing public methods or attribute failures.

- [ ] **Step 3: Implement minimal controller split**

  Extract current repair body so `quarantine()` authenticates and gates, then returns the model; `repair_quarantined()` re-authenticates, validates every binding and current gate state, then rebuilds/tests/attests. Preserve journal ordering and `repair(resume=...)` compatibility.

- [ ] **Step 4: Verify GREEN**

  Run `python3 -m unittest tests.test_controller tests.test_sqlite_store -v` then full discovery.

- [ ] **Step 5: Commit**

  `git add prototype/controller.py prototype/sqlite_store.py tests/test_controller.py tests/test_sqlite_store.py && git commit -m "feat: separate quarantine from repair"`

### Task 3: Workspace persistence and CLI admission

**Files:**
- Modify: `prototype/workspace.py`
- Modify: `prototype/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `Makefile`

**Interfaces:**
- Produces: `Workspace.checkpoints_dir`, `checkpoint_path(sequence, erratum_id)`, `write_checkpoint`, `load_checkpoint`, and `consume_checkpoint`.
- Produces: `errata quarantine` and checkpoint-requiring `errata repair`.
- Both commands select exactly one next pending erratum.

- [ ] **Step 1: Write failing CLI tests**

  Add real-workspace tests proving quarantine persists before repair; repair without checkpoint refuses; only next erratum is processed; mutated, consumed, replayed, wrong-target, state-drifted, adapter-drifted, and ungated checkpoints refuse without receipt/applied advancement; interrupted repair retains checkpoint; successful partial repair consumes it only after receipt/applied durability.

- [ ] **Step 2: Verify RED**

  Run `python3 -m unittest tests.test_cli -v`. Expected: parser rejects `quarantine` and current repair succeeds without a checkpoint.

- [ ] **Step 3: Implement workspace and CLI**

  Add deterministic paths and `CheckpointStore` delegation. Catch `FeedError`, `CheckpointError`, and state validation errors as `EXIT_REFUSED`. Process one erratum, persist receipt idempotently, record applied sequence idempotently, then consume checkpoint. Add `quarantine` to `COMMANDS` and parser.

- [ ] **Step 4: Update CLI demo**

  Insert `run quarantine` before `run repair`; preserve expected repair exit `2`, receipt verification, and cleanup.

- [ ] **Step 5: Verify GREEN**

  Run `python3 -m unittest tests.test_cli -v`, `make cli-demo`, and full discovery.

- [ ] **Step 6: Commit**

  `git add prototype/workspace.py prototype/cli.py tests/test_cli.py Makefile && git commit -m "feat: require quarantine checkpoint for CLI repair"`

### Task 4: Documentation and Phase 2 status integration

**Files:**
- Modify: `prototype/README.md`
- Modify: `spec/README.md`
- Modify: `README.md`
- Modify: `ROADMAP.md`
- Modify: `PRODUCTION_READINESS.md`
- Modify: `readiness/production-readiness.json`
- Modify: `CHANGELOG.md`
- Modify: `scripts/check_readiness.py`
- Modify: `tests/test_readiness.py`

**Interfaces:**
- Produces accurate internal completion language for explicit quarantine while G2 remains `BLOCKED` for remaining vectors and external review.
- Adds `prototype/checkpoints.py` and `tests/test_checkpoints.py` to canonical G2 surface.

- [ ] **Step 1: Add failing readiness regression tests**

  Require canonical G2 evidence/matrix language to acknowledge checkpoint completion without upgrading G2; require checkpoint files in surface manifest and digest.

- [ ] **Step 2: Verify RED**

  Run `python3 -m unittest tests.test_readiness -v`. Expected: new canonical-language and surface assertions fail.

- [ ] **Step 3: Update documentation and checker constants**

  Document command ordering, checkpoint fields, replay/drift refusal, recovery semantics, and remaining key-rotation/concurrency/invalid-target/confidentiality/receipt-binding gaps.

- [ ] **Step 4: Verify GREEN**

  Run focused readiness tests, `make check`, and `git diff --check`.

- [ ] **Step 5: Commit**

  `git add prototype/README.md spec/README.md README.md ROADMAP.md PRODUCTION_READINESS.md readiness/production-readiness.json CHANGELOG.md scripts/check_readiness.py tests/test_readiness.py && git commit -m "docs: record durable quarantine completion"`
