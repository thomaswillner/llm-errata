# Phase 2 Conformance Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the Phase 1 demo into something a third party can implement against and audit, and close the one hole the threat model calls sharpest — an adapter that reports `verified` on the strength of its own bookkeeping.

**Architecture:** Four vertical slices. A published wire schema with conformance vectors defines the contract. A SQLite adapter proves the model survives a real transactional store. A substrate residue scan reads the store's actual bytes, so `verified` requires evidence rather than an API acknowledgement. A CLI makes all of it operable without importing Python.

**Tech Stack:** Python 3.11+ standard library only. `sqlite3`, `argparse`, `json`, `hashlib`, `unittest`. No network, no third-party packages, no API keys.

## Global Constraints

- **Standard library only.** No dependency may be added. `tests/test_demo.py::test_it_needs_no_network_and_no_api_key` forbids `requests`, `urllib.request`, `http.client`, `socket`, and `openai` in `prototype/`.
- **`make check` must stay green** — lint, claim guard, self-tests, demo.
- **`make demo` must keep exiting 2.** The aggregate must remain non-green while an opaque required store is in scope. No task may make the demo look better.
- **No trailing whitespace, LF endings, UTF-8.** `scripts/validate_repo.py` fails the build otherwise.
- **No absolute local paths in Markdown.** `scripts/validate_repo.py` rejects absolute Unix home and temp directories, Windows user paths, and sandbox or file URI schemes. The exact patterns are in `LOCAL_PATH_PATTERNS`; they are deliberately not reproduced here, because writing one down trips the check that reads this file.
- **Fixtures are synthetic.** AGENTS.md forbids real personal, customer, employer, or credential material.
- **Every new required file must be added to `REQUIRED_FILES` in `scripts/validate_repo.py`**, so the tooling cannot be deleted and still pass.
- **Coverage vocabulary is fixed:** `verified`, `partial`, `unknown`, `failed`. `pending` is a lifecycle state, never a result.

---

## File Structure

| File | Responsibility |
|---|---|
| `spec/erratum.schema.json` | Normative wire shape of an erratum |
| `spec/receipt.schema.json` | Normative wire shape of a receipt |
| `spec/vectors/manifest.json` | Every conformance vector, its file, and whether it must validate |
| `spec/vectors/*.json` | The vectors themselves |
| `spec/README.md` | What the schema covers, what the bundled validator supports, and how to use the vectors |
| `prototype/schema.py` | Dependency-free validator for the JSON Schema subset the specs use |
| `prototype/sqlite_store.py` | `SqliteAdapter`: a real transactional store, plus its residue scan |
| `prototype/residue.py` | `ResidueReport` and the substrate-evidence rule shared by adapters |
| `prototype/cli.py` | `errata` subcommands over an on-disk workspace |
| `prototype/workspace.py` | On-disk layout: feeds, registry, receipts, identity, store |
| `tests/test_schema.py` | Validator behaviour and every conformance vector |
| `tests/test_sqlite_store.py` | Transactions, interrupted repair, residue |
| `tests/test_residue.py` | The substrate-evidence rule, including the Ghost Vectors case |
| `tests/test_cli.py` | End-to-end through `python3 -m prototype.cli` |

---

### Task 1: Wire schema and conformance vectors

**Files:**
- Create: `prototype/schema.py`, `spec/erratum.schema.json`, `spec/receipt.schema.json`, `spec/vectors/manifest.json`, `spec/vectors/*.json`, `spec/README.md`
- Modify: `scripts/validate_repo.py` (REQUIRED_FILES), `Makefile` (`vectors` target)
- Test: `tests/test_schema.py`

**Interfaces:**
- Consumes: `prototype.errata.Erratum.signable()`, `prototype.receipts.Receipt.to_dict()`
- Produces:
  - `schema.validate(instance: dict, schema: dict) -> list[str]` — returns human-readable error strings, empty list means valid
  - `schema.load(name: str) -> dict` — loads a schema from `spec/` by bare name, e.g. `"erratum"`
  - `schema.SUPPORTED_KEYWORDS: frozenset[str]` — every keyword the validator implements

- [ ] **Step 1: Write the failing test for the validator subset**

```python
def test_unsupported_keyword_in_a_schema_is_an_error_not_a_silent_pass(self):
    # A validator that ignores keywords it does not implement will pass an
    # instance that the published schema rejects. That is the same class of
    # failure as a checker that cannot fail.
    errors = schema.validate({"a": 1}, {"type": "object", "$comment": "x",
                                        "unevaluatedProperties": False})
    self.assertTrue(any("unevaluatedProperties" in e for e in errors))
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python3 -m unittest tests.test_schema -v`
Expected: FAIL, `ModuleNotFoundError: prototype.schema`

- [ ] **Step 3: Implement `prototype/schema.py`**

Implement exactly these keywords and refuse any others: `type`, `properties`, `required`, `additionalProperties`, `enum`, `const`, `pattern`, `minimum`, `maximum`, `minLength`, `maxLength`, `items`, `minItems`, `uniqueItems`, `oneOf`, `allOf`, `not`, `$ref` (local `#/$defs/...` only), `$defs`, `title`, `description`, `$schema`, `$id`, `examples`. Any other keyword encountered in a schema returns an error naming it.

- [ ] **Step 4: Run the test, watch it pass**

- [ ] **Step 5: Write the schemas**

`erratum.schema.json` requires `erratum_id`, `sequence` (integer, minimum 1), `target_root`, `operation` (enum correct/supersede/erase), `valid_from` (RFC 3339 pattern), `postconditions`, and forbids additional properties. `oneOf` splits erasure (no `replacement`, no `positive` postcondition) from correction and supersession (`replacement` required, `positive` required).

`receipt.schema.json` requires `importer`, `erratum_id`, `sequence`, `target_root`, `operation`, `pre_state_root`, `post_state_root`, `stores` (object of coverage enum), `dispositions`, `triad`, `aggregate` (coverage enum), `limitations`, `history_retained`, `signature`.

- [ ] **Step 6: Write the vectors and the manifest**

At minimum: valid correction, valid supersession, valid erasure, valid receipt at each of the four aggregates; invalid — erasure carrying a replacement, supersession missing `replacement`, missing `positive` postcondition, sequence 0, unknown operation, unknown coverage value, additional property. Each invalid vector's manifest entry names the keyword that must reject it.

- [ ] **Step 7: Write the round-trip test**

```python
def test_the_prototype_emits_instances_its_own_schema_accepts(self):
    receipt = build_importer(OWNER).repair(supersede())
    self.assertEqual(schema.validate(receipt.to_dict(), schema.load("receipt")), [])
```

- [ ] **Step 8: Run the full suite, then commit**

```bash
make check && git add -A && git commit -m "feat: publish the erratum and receipt wire schema with conformance vectors"
```

---

### Task 2: SQLite adapter with real transactions

**Files:**
- Create: `prototype/sqlite_store.py`
- Test: `tests/test_sqlite_store.py`
- Modify: `scripts/validate_repo.py`

**Interfaces:**
- Consumes: `prototype.adapters.Coverage`, `prototype.adapters.Hit`, `prototype.lineage.LineageLedger`
- Produces: `SqliteAdapter(path: Path, ledger: LineageLedger, name: str = "sqlite")` with the adapter protocol — `enumerate`, `quarantine`, `is_quarantined`, `retire`, `rebuild`, `recall`, `coverage`, `dispositions`, `snapshot`, plus `residue_scan(value: str) -> ResidueReport` and `vacuum()`

- [ ] **Step 1: Write the failing test for durable quarantine**

```python
def test_quarantine_survives_an_interrupted_rebuild(self):
    # Quarantine commits in its own transaction, before the rebuild starts.
    # A rebuild that raises rolls back, and the gate is still closed.
    adapter = SqliteAdapter(self.path, self.ledger)
    adapter.quarantine(("fact:diet",))
    with self.assertRaises(RuntimeError):
        adapter.rebuild_all_failing()
    reopened = SqliteAdapter(self.path, self.ledger)
    self.assertTrue(reopened.is_quarantined("fact:diet"))
```

- [ ] **Step 2: Run it, watch it fail**

- [ ] **Step 3: Implement the adapter**

One table `artifacts(artifact_id TEXT PRIMARY KEY, root TEXT, content TEXT, inputs TEXT, quarantined INTEGER DEFAULT 0, retired INTEGER DEFAULT 0, rebuilt INTEGER DEFAULT 0)`. `journal_mode=WAL`. Quarantine commits immediately. Rebuild opens an explicit transaction and rolls back on exception.

- [ ] **Step 4: Run, watch it pass**

- [ ] **Step 5: Add the recall and preservation tests, run, commit**

```bash
make check && git add -A && git commit -m "feat: add a SQLite-backed adapter with durable quarantine"
```

---

### Task 3: Substrate residue scanning

**Files:**
- Create: `prototype/residue.py`
- Modify: `prototype/sqlite_store.py`, `prototype/adapters.py`, `prototype/controller.py`, `THREAT_MODEL.md`, `prototype/README.md`
- Test: `tests/test_residue.py`

**Interfaces:**
- Produces:
  - `ResidueReport(scanned: bool, found: bool, where: str, detail: str)`
  - `ResidueReport.blocks_verified() -> bool` — true when `not scanned` or `found`
  - Adapters gain `residue_scan(value: str) -> ResidueReport`; the default returns `scanned=False`

> **CRITICAL correction to this task, made before any code was written.**
>
> The first draft said "scan the database file" and set `journal_mode=WAL`. Measured on this machine, that combination is wrong in the worst possible direction:
>
> | journal | secure_delete | vacuum | where the deleted value actually is |
> |---|---|---|---|
> | delete | 0 | no | main `.sqlite3` file |
> | delete | 1 | no | nowhere |
> | **wal** | **0** | **no** | **`-wal` file, main file clean** |
> | wal | 0 | no, after close | main file (checkpointed) |
>
> In WAL mode the main database file does **not** contain the deleted value while the connection is open. A scan that reads only `store.sqlite3` would report clean while the plaintext sits in `store.sqlite3-wal` on the same disk. That is precisely the false `verified` this feature exists to prevent — the plan would have shipped the bug it is meant to catch.
>
> Therefore:
> - `residue_scan` MUST scan every file in the store's on-disk footprint: the main database, `-wal`, `-shm`, and any rollback journal. Scanning one file is not scanning the store.
> - The scan MUST report *which* file matched, so "clean main database, dirty WAL" is visible rather than averaged away.
> - There MUST be a test asserting that a main-file-only scan misses it, so the narrow scan cannot be reintroduced.
> - `secure_delete` MUST be recorded in the report. An adapter can be clean in the main file and dirty in the WAL, and the two facts have different causes.

- [ ] **Step 1: Write the failing test that is the whole point**

```python
def test_a_deleted_row_is_still_in_the_database_file(self):
    # SQLite moves deleted rows to the freelist. The bytes stay on disk until
    # VACUUM. This is the same failure Ghost Vectors demonstrates for HNSW
    # indexes, reproducible with the standard library.
    adapter = SqliteAdapter(self.path, self.ledger)
    adapter.retire("fact:diet")
    report = adapter.residue_scan("is vegetarian")
    self.assertTrue(report.scanned)
    self.assertTrue(report.found, "expected the value to survive a plain DELETE")

def test_vacuum_clears_the_residue(self):
    adapter = SqliteAdapter(self.path, self.ledger)
    adapter.retire("fact:diet")
    adapter.vacuum()
    self.assertFalse(adapter.residue_scan("is vegetarian").found)

def test_an_adapter_with_residue_cannot_report_verified(self):
    adapter = SqliteAdapter(self.path, self.ledger)
    adapter.retire("fact:diet")
    self.assertNotEqual(adapter.coverage(DIET, erased_value="is vegetarian"),
                        Coverage.VERIFIED)

def test_an_adapter_that_cannot_scan_cannot_report_verified_either(self):
    # Not scanning is not the same as scanning clean. An adapter that has no
    # way to inspect its substrate reports partial, never verified.
    self.assertFalse(ResidueReport(scanned=False, found=False,
                                   where="x", detail="").blocks_verified() is False)
```

- [ ] **Step 2: Run, watch all four fail**

- [ ] **Step 3: Implement `residue.py` and wire it into coverage**

`residue_scan` opens the database file in binary and searches the raw bytes. Coverage downgrades to `partial` when a scan finds residue or when no scan was performed and the operation was an erasure.

- [ ] **Step 4: Run, watch them pass**

- [ ] **Step 5: Update THREAT_MODEL.md**

Move "a store whose substrate contradicts its API" from *not defended* to *partly defended*, stating precisely what the scan does and does not cover: it finds a literal value in the store's own file, not in the OS page cache, a backup, a WAL that has been checkpointed elsewhere, or an index structure that encodes the value without storing it verbatim.

- [ ] **Step 6: Commit**

```bash
make check && git add -A && git commit -m "feat: require substrate evidence before an adapter may report verified"
```

---

### Task 4: The errata CLI

**Files:**
- Create: `prototype/workspace.py`, `prototype/cli.py`
- Test: `tests/test_cli.py`
- Modify: `Makefile`, `README.md`, `prototype/README.md`, `ROADMAP.md`, `scripts/validate_repo.py`

**Interfaces:**
- Consumes: everything above
- Produces: `python3 -m prototype.cli <command>` with `init`, `export`, `publish`, `pull`, `plan`, `quarantine`, `repair`, `test`, `attest`, `audit`, `verify`
- Exit codes: `0` success, `1` failure or refusal, `2` inconclusive or non-green aggregate

- [ ] **Step 1: Write the failing end-to-end test**

```python
def test_a_full_lifecycle_through_the_cli(self):
    self.run_cli("init")
    self.run_cli("export", "--root", "mem_01HX", "--content", "is vegetarian")
    self.run_cli("publish", "--root", "mem_01HX", "--operation", "supersede",
                 "--replacement", "eats meat again")
    result = self.run_cli("repair")
    self.assertEqual(result.returncode, 2)          # partial, honestly
    audit = json.loads(self.run_cli("audit", "--json").stdout)
    self.assertEqual(audit["aggregate"], "partial")
    self.assertEqual(self.run_cli("verify").returncode, 0)
```

- [ ] **Step 2: Run, watch it fail**

- [ ] **Step 3: Implement `workspace.py` then `cli.py`**

Workspace layout on disk: `identity/owner.pub`, `identity/owner.key`, `feeds/errata.jsonl`, `registry/lineage.jsonl`, `receipts/<erratum_id>.json`, `store.sqlite3`, `log.md`.

- [ ] **Step 4: Run, watch it pass**

- [ ] **Step 5: Add the refusal tests**

Forged erratum → exit 1. Rollback → exit 1. Stale reimport → exit 1. `verify` on a tampered receipt → exit 1.

- [ ] **Step 6: Wire `make cli-demo`, update docs, commit**

```bash
make check && git add -A && git commit -m "feat: add the errata CLI over an on-disk workspace"
```

---

## Self-Review

**Spec coverage.** Item 1 → Task 1. Item 2 → Task 2. Item 3 → Task 4. Item 4 → Task 3. ROADMAP Phase 2's adapter-interface requirement is satisfied by Task 2 conforming to the same protocol as the in-memory adapters without changes to `controller.py`.

**Placeholders.** None. Every step names files, shows test code, and states the expected failure.

**Type consistency.** `ResidueReport` is defined in Task 3 and used only there and in Task 2's interface block. `schema.validate` returns `list[str]` in every reference. `Coverage` is imported from `prototype.adapters` throughout, never redefined.

**Known risk to flag during execution:** Task 3 changes `coverage()`'s signature by adding `erased_value`. Every existing adapter and its callers must keep working with the argument absent. If that turns out to require touching `controller.py` in more than one place, stop and reconsider the seam rather than threading the parameter through.

---

## Adversarial review, 2026-08-07

Kimi3 was unavailable (Moonshot returned a membership-verification error for every model) and Codex was rate-limited until 2026-08-08. CLIProxy itself was healthy — its own liveness probe reported `claude=ALIVE gemini=ALIVE gpt=DEAD:rate_limited` — so the review ran against **gemini-3.1-pro-low**, an independent vendor.

Nine findings, all verified against the real code before acceptance. The plan above is superseded where they conflict.

| # | Severity | Finding | Correction |
|---|---|---|---|
| 1 | CRITICAL | `coverage(root, erased_value=...)` is undeliverable: the controller calls `coverage(root)` and does not know the erased value. The erratum deliberately does not carry it. | Do not change the signature. The adapter caches the content at `retire()` time and scans for that. |
| 2 | CRITICAL | Downgrading any result to `partial` on residue *upgrades* `unknown` and `failed`. An opaque store would become partially successful. | The residue rule may only ever make a result worse. |
| 3 | CRITICAL | `retired INTEGER DEFAULT 0` is a soft delete. `VACUUM` reclaims space from real deletes and does nothing to a flagged row, so `test_vacuum_clears_the_residue` could never pass. | `retire()` must actually orphan the text. |
| 4 | MAJOR | Residue found was to report `partial`. IDEA.md defines `failed` as "relevant state was found and could not be safely repaired". That is exactly this. Correction destroys data too, not only erasure. | Residue found is `failed`. The scan applies to correction as well as erasure. |
| 5 | MAJOR | The same author writes both the schema and the validator, so a matching pair of mistakes cancels out and the tests still pass. | Vendor cases from the official JSON-Schema-Test-Suite for every implemented keyword. |
| 6 | MAJOR | `receipt.schema.json` omitted `adapter_versions`, which `Receipt.signable()` emits. The round-trip test would have failed. | Include it. |
| 7 | MINOR | `assertFalse(x.blocks_verified() is False)` passes when the method returns `None`. | `assertTrue(x.blocks_verified())`. |
| 8 | MINOR | `adapter.rebuild_all_failing()` does not exist; the test would raise `AttributeError` and fail for the wrong reason. | Force a real database error. |
| 9 | MINOR | The CLI `publish` example omits `--positive`, which supersession requires. | Add it. |

Plus one finding from measurement rather than review, recorded in Task 3 above: in WAL mode the deleted value is in `store.sqlite3-wal`, not `store.sqlite3`. A scan of the main file alone reports clean while the plaintext is on disk.
