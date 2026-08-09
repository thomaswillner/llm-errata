# Production Readiness Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed production-readiness evidence ledger, correct version/security documentation drift, and make readiness validation part of every repository check.

**Architecture:** `readiness/production-readiness.json` is the machine-readable source of current readiness state; `PRODUCTION_READINESS.md` explains the same gates for reviewers. `scripts/check_readiness.py` validates structure, project-version alignment, evidence references, external-evidence independence metadata, and the rule that `PROD_READY` is impossible unless every required gate passes. Existing repository validation separately prevents README and SECURITY version drift.

**Tech Stack:** Python 3.11+ standard library, JSON, Markdown, Make, GitHub Actions, `unittest`.

**Plan revision:** 2. Task 3 creates `PRODUCTION_READINESS.md`; Task 2 must not link that file before it exists.

## Global Constraints

- Current project version is `0.3.0` and current verdict remains `NOT_PROD_READY`.
- Required gates are exactly `G1` through `G6` from the user-approved production-readiness path.
- `G1` may become `PASS` after this plan; `G2` through `G6` remain `BLOCKED`.
- No local test, local agent review, or repository file may be represented as independent external evidence.
- An external gate may become `PASS` only when its evidence includes an external entry with a non-empty independent producer, an ISO `YYYY-MM-DD` observation date, and an `https://` or `urn:` reference.
- Never convert `unknown`, `partial`, or inaccessible coverage into `verified`.
- Preserve correction, supersession, and erasure distinctions; quarantine-before-repair ordering; repair triad; and bounded novelty language.
- Use only synthetic fixtures. Add no credentials, personal data, customer data, employer data, or production memory.
- Keep runtime dependency-free. Do not add a package manager, framework, service, or deployment.

---

### Task 1: Machine-readable readiness contract and fail-closed checker

**Files:**
- Create: `readiness/production-readiness.json`
- Create: `scripts/check_readiness.py`
- Create: `tests/test_readiness.py`

**Interfaces:**
- Consumes: `VERSION`; repository-relative evidence files; readiness JSON.
- Produces: `scripts/check_readiness.py::main() -> int`, exit `0` only when ledger is structurally honest; stable output containing `[PASS]` or `[FAIL]` lines.

- [ ] **Step 1: Write failing checker tests**

Create `tests/test_readiness.py` using `tests.support.check_after`, `repo_copy`, and `run_checker`. Tests must cover:

```python
SCRIPT = "check_readiness.py"

class ReadinessCheckerPasses(unittest.TestCase):
    def test_current_not_ready_ledger_is_honest(self) -> None:
        with repo_copy() as root:
            result = run_checker(root, SCRIPT)
        self.assertEqual(result.returncode, EXIT_OK, result.stdout)
```

Add `ReadinessCheckerFailsClosed` with these exact test names: `test_project_version_drift_is_rejected`, `test_missing_required_gate_is_rejected`, `test_missing_repository_evidence_is_rejected`, `test_prod_ready_with_a_blocked_gate_is_rejected`, `test_external_pass_without_independent_evidence_is_rejected`, `test_external_evidence_without_producer_is_rejected`, and `test_external_evidence_without_iso_date_is_rejected`.

Each test must load `readiness/production-readiness.json`, change one exact field, write formatted JSON using `json.dumps(payload, indent=2) + "\n"`, run the checker, assert exit `1`, and assert an actionable check name in stdout. Use `next(gate for gate in payload["gates"] if gate["id"] == "G2")` for external-evidence mutations so tests do not depend on array position.

- [ ] **Step 2: Run tests and verify they fail for missing artifacts**

Run:

```bash
python3 -m unittest tests.test_readiness -v
```

Expected: failure because `scripts/check_readiness.py` and `readiness/production-readiness.json` do not exist.

- [ ] **Step 3: Create initial readiness ledger**

Create `readiness/production-readiness.json` with:

```json
{
  "schema_version": 1,
  "project_version": "0.3.0",
  "verdict": "NOT_PROD_READY",
  "last_reviewed": "2026-08-09",
  "gates": [
    {
      "id": "G1",
      "name": "Version and security document consistency",
      "class": "internal",
      "status": "BLOCKED",
      "criterion": "README maturity and SECURITY supported-version policy match VERSION and are protected by negative tests.",
      "evidence": [{"kind": "repository", "ref": "VERSION"}]
    },
    {
      "id": "G2",
      "name": "Phase 2 complete with external conformance review",
      "class": "external",
      "status": "BLOCKED",
      "criterion": "Phase 2 item 6 is implemented and an independent reviewer evaluates the complete conformance surface.",
      "evidence": [{"kind": "repository", "ref": "ROADMAP.md"}]
    },
    {
      "id": "G3",
      "name": "Audited constant-time production cryptography",
      "class": "external",
      "status": "BLOCKED",
      "criterion": "Production signing uses an audited constant-time library through the Signer seam and independent security review covers key lifecycle.",
      "evidence": [{"kind": "repository", "ref": "THREAT_MODEL.md"}]
    },
    {
      "id": "G4",
      "name": "Two independent implementations and third-party validator",
      "class": "external",
      "status": "BLOCKED",
      "criterion": "Two independently authored adapters consume the same erratum and a third-party validator evaluates their receipts consistently.",
      "evidence": [{"kind": "repository", "ref": "ROADMAP.md"}]
    },
    {
      "id": "G5",
      "name": "Three-system Phase 3 interoperability experiment",
      "class": "external",
      "status": "BLOCKED",
      "criterion": "One user-controlled synthetic root completes the declared experiment across three independently operated memory systems.",
      "evidence": [{"kind": "repository", "ref": "ROADMAP.md"}]
    },
    {
      "id": "G6",
      "name": "Operational production gates",
      "class": "external",
      "status": "BLOCKED",
      "criterion": "Security, observability, recovery, compatibility, performance, deployment, and rollback gates pass with current operational evidence.",
      "evidence": [{"kind": "repository", "ref": "SECURITY.md"}]
    }
  ]
}
```

- [ ] **Step 4: Implement checker**

Create `scripts/check_readiness.py` with:

```python
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "readiness" / "production-readiness.json"
REQUIRED_GATES = {"G1", "G2", "G3", "G4", "G5", "G6"}
VERDICTS = {"NOT_PROD_READY", "PROD_READY"}
STATUSES = {"PASS", "FAIL", "BLOCKED"}
CLASSES = {"internal", "external"}

class Reporter:
    def __init__(self) -> None:
        self.passed = 0
        self.failures: list[str] = []

    def check(self, name: str, condition: bool, detail: str) -> None:
        if condition:
            self.passed += 1
            print(f"[PASS] {name}: {detail}")
        else:
            self.failures.append(name)
            print(f"[FAIL] {name}: {detail}")

    def finish(self) -> int:
        if self.failures:
            print(f"\nReadiness validation failed: {', '.join(self.failures)}")
            return 1
        print(f"\nReadiness evidence is structurally valid; current verdict is not upgraded.")
        return 0

def read_ledger() -> dict[str, object]:
    payload = json.loads(LEDGER.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("readiness ledger root must be an object")
    return payload

def valid_iso_date(value: object) -> bool:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True

def valid_external_ref(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return value.startswith("urn:") or (
        urlparse(value).scheme == "https" and bool(urlparse(value).netloc)
    )

def main() -> int:
    reporter = Reporter()
    try:
        payload = read_ledger()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        reporter.check("readiness ledger", False, str(error))
        return reporter.finish()

    repository_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    validate_ledger(payload, repository_version, reporter)
    print(f"Current verdict: {payload.get('verdict', '<missing>')}")
    return reporter.finish()
```

Define `validate_ledger(payload: dict[str, object], repository_version: str, reporter: Reporter) -> None` immediately before `main()`. It performs the ten checks below and never raises for malformed ledger values; type-check each value before indexing or iterating it.

`main()` must report and reject:

1. missing, unreadable, non-object, or malformed ledger;
2. `schema_version != 1`;
3. project version different from stripped `VERSION`;
4. invalid verdict or last-review date;
5. missing, duplicate, or unexpected gate IDs;
6. invalid name, class, status, criterion, or empty evidence;
7. repository evidence whose path is absolute, escapes root, or does not exist;
8. external evidence without valid reference, producer, or observed date;
9. an external `PASS` without at least one valid external evidence entry;
10. `PROD_READY` unless every gate is `PASS`.

Malformed input must return `1`, never traceback. Output must identify gate and failed rule.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_readiness -v
python3 scripts/check_readiness.py
```

Expected: all readiness tests pass; checker exits `0` while reporting verdict `NOT_PROD_READY` and blocked G1–G6 honestly.

- [ ] **Step 6: Commit Task 1**

```bash
git add readiness/production-readiness.json scripts/check_readiness.py tests/test_readiness.py
git commit -m "feat: add fail-closed readiness ledger"
```

---

### Task 2: Correct documentation drift and prevent recurrence

**Files:**
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `scripts/validate_repo.py`
- Modify: `tests/test_validate_repo.py`
- Modify: `readiness/production-readiness.json`

**Interfaces:**
- Consumes: repository version returned by `check_version()`.
- Produces: `check_document_version_alignment(reporter: Reporter, repository_version: str | None) -> None`.

- [ ] **Step 1: Write failing negative tests**

Add to `ValidatorRejectsStructuralFaults`:

```python
def test_readme_maturity_version_drift_is_rejected(self) -> None:
    def mutate(root: Path) -> None:
        current = (root / "VERSION").read_text(encoding="utf-8").strip()
        rewrite(root / "README.md", f"Version {current}", "Version 0.0.0")
    result = check_after(SCRIPT, mutate)
    self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
    self.assertIn("README maturity version", result.stdout)

def test_security_supported_version_drift_is_rejected(self) -> None:
    def mutate(root: Path) -> None:
        current = (root / "VERSION").read_text(encoding="utf-8").strip()
        major, minor, _ = current.split(".")
        rewrite(root / "SECURITY.md", f"| {major}.{minor}.x | Yes |", "| 0.0.x | Yes |")
    result = check_after(SCRIPT, mutate)
    self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
    self.assertIn("SECURITY supported version", result.stdout)
```

- [ ] **Step 2: Run tests and verify current documentation fails**

Run:

```bash
python3 -m unittest tests.test_validate_repo -v
```

Expected: new negative-test mutations cannot find current version markers because README and SECURITY are stale.

- [ ] **Step 3: Correct README and SECURITY**

Replace README maturity section with current facts:

```markdown
## Current maturity

Version 0.3.0 is an experimental conformance proposal and tested reference implementation, not a production protocol or proof of interoperability. Phase 1 and Phase 2 items 1 through 5 are implemented; neither has completed external conformance review, and Phase 2 item 6 remains unstarted.

Current production-readiness verdict: **NOT_PROD_READY**. `ROADMAP.md` defines implementation and kill criteria. The human evidence matrix is added with continuous enforcement in the next task.
```

Retain the existing review-request list after this paragraph. Remove the obsolete “next milestone” bullet list because those items are already implemented. In the actual root README, render `ROADMAP.md` as a Markdown link targeting the root-level `ROADMAP.md`. Do not link `PRODUCTION_READINESS.md` in Task 2 because Task 3 owns and creates that file.

Change SECURITY supported versions to:

```markdown
Until a later policy states otherwise, only the latest versioned release is eligible for security fixes. Development revisions after that release receive fixes at maintainer discretion and are not represented as supported releases.

| Version | Supported |
|---|---|
| 0.3.x | Yes |
| 0.2.x and earlier | No |
| Unreleased development revisions | No |
```

- [ ] **Step 4: Add version-alignment validation**

Add `check_document_version_alignment()` to `scripts/validate_repo.py`. It must derive `major.minor.x` from `VERSION`, require exact `Version {VERSION}` in README’s maturity section, and require exact `| {major}.{minor}.x | Yes |` in SECURITY. Call it after `check_publication_metadata()` and before `check_citation()`.

- [ ] **Step 5: Mark G1 pass with evidence**

In `readiness/production-readiness.json`, change only G1 to `PASS` and set evidence to repository references for `VERSION`, `README.md`, `SECURITY.md`, `scripts/validate_repo.py`, and `tests/test_validate_repo.py`. Keep overall verdict `NOT_PROD_READY`; keep G2–G6 `BLOCKED`.

- [ ] **Step 6: Run focused tests**

```bash
python3 -m unittest tests.test_validate_repo tests.test_readiness -v
python3 scripts/validate_repo.py
python3 scripts/check_readiness.py
```

Expected: all focused tests pass; both checkers exit `0`; readiness verdict remains `NOT_PROD_READY` with G1 pass and G2–G6 blocked.

- [ ] **Step 7: Commit Task 2**

```bash
git add README.md SECURITY.md scripts/validate_repo.py tests/test_validate_repo.py readiness/production-readiness.json
git commit -m "fix: align release and security metadata"
```

---

### Task 3: Human readiness matrix and continuous enforcement

**Files:**
- Create: `PRODUCTION_READINESS.md`
- Modify: `README.md`
- Modify: `Makefile`
- Modify: `.github/workflows/validate.yml`
- Modify: `CHANGELOG.md`
- Modify: `scripts/validate_repo.py`
- Modify: `tests/test_validate_repo.py`

**Interfaces:**
- Consumes: `readiness/production-readiness.json` and `scripts/check_readiness.py`.
- Produces: `make readiness`; `make check` includes readiness; CI executes readiness check on Python 3.11 and 3.13.

- [ ] **Step 1: Write failing required-file test**

Extend `REQUIRED_FILES` in `scripts/validate_repo.py` with:

```python
"PRODUCTION_READINESS.md",
"readiness/production-readiness.json",
"scripts/check_readiness.py",
"tests/test_readiness.py",
```

Add a negative test that deletes `PRODUCTION_READINESS.md`, runs validator, and requires `required files` failure.

- [ ] **Step 2: Create human-readable matrix**

Create `PRODUCTION_READINESS.md` with:

- current version `0.3.0` and verdict `NOT_PROD_READY`;
- distinction between build health and production readiness;
- table for G1–G6 with criterion, current status, current evidence, and next evidence required;
- G1 `PASS`; G2–G6 `BLOCKED`;
- statement that local tests and agent reviews are not external evidence;
- approval boundaries for external review, third-party systems, real data, and final verdict change;
- exact command `make readiness` and explanation that exit `0` validates honesty of state, not readiness itself.

After creating the file, update README’s current-maturity paragraph: replace the sentence saying the human evidence matrix arrives in the next task with a Markdown link whose text and root-level target are both `PRODUCTION_READINESS.md`. Preserve the existing root-level `ROADMAP.md` link.

- [ ] **Step 3: Integrate Make targets**

Change Makefile declarations to:

```make
.PHONY: check lint claim readiness test demo cli-demo links all help

check: lint claim readiness test demo ## Everything that must pass before a change is complete

readiness: ## Validate production-readiness evidence without upgrading the verdict

\t$(PYTHON) scripts/check_readiness.py
```

- [ ] **Step 4: Integrate CI**

In `.github/workflows/validate.yml`, add after claim guard:

```yaml
      - name: Validate production-readiness evidence
        run: make readiness
```

- [ ] **Step 5: Record unreleased change**

Under `CHANGELOG.md`’s Unreleased heading add:

```markdown
### Added — production-readiness evidence

- Added a fail-closed production-readiness ledger and human verification matrix. Local green tests cannot produce `PROD_READY`; every required gate must pass, and external gates require dated evidence naming an independent producer.
- Added drift checks binding README maturity and SECURITY support policy to `VERSION`. The current verdict remains `NOT_PROD_READY`: only G1, document consistency, is complete.
```

- [ ] **Step 6: Run full verification**

```bash
make check
git diff --check
git status --short
```

Expected: validator count increases for the new required files and version-alignment checks; readiness checker exits `0` while printing `NOT_PROD_READY`; all 150 existing tests plus new readiness and drift tests pass; demo exits `2` as required; diff check is clean.

- [ ] **Step 7: Commit Task 3**

```bash
git add PRODUCTION_READINESS.md README.md Makefile .github/workflows/validate.yml CHANGELOG.md scripts/validate_repo.py tests/test_validate_repo.py
git commit -m "docs: enforce production readiness evidence"
```

---

## Program handoff after this foundation

This plan completes only G1. Subsequent independently reviewed plans are required in this dependency order:

1. `phase-2-semantic-probes`: provider-neutral model-assisted probe interface, deterministic fixtures, verifier configuration, and external conformance-review package.
2. `production-cryptography`: production signer adapter using an audited constant-time library, key rotation/recovery/delegation, and independent security review.
3. `independent-conformance`: two independently authored adapters and a separately produced validator result.
4. `phase-3-interoperability`: three approved target systems, synthetic root, nonconforming importer, incomplete-coverage system, and measured experiment report.
5. `production-operations`: deployment, rollback, recovery, observability, privacy, compatibility, load, denial-of-service, and incident-response evidence.

No later plan may mark its gate `PASS` from implementation alone. External gates require their declared independent or operational evidence.
