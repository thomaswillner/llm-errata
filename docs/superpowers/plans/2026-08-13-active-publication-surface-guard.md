# Active Publication Surface Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make stale public review targets and obsolete implementation-permission language fail deterministic repository checks while preserving append-only GitHub history.

**Architecture:** A tracked JSON manifest records the five active public surfaces, their immutable source target, evidence roles, mentions, superseded URLs, licence posture, and evidence boundary. A dependency-free Python checker validates exact current values offline; live GitHub identity, rendering, and liveness remain publication-time checks recorded in the publication log.

**Tech Stack:** Python 3.11/3.13 standard library, JSON, unittest, Make, GitHub Actions.

## Global Constraints

- Current frozen source target is `08b95263c9ed700c43aea0b285696956cc23e878`.
- Current canonical G2 digest is `03abc492319b875a7d528e0e8de05714bc5a7219b42031fc7c3f42cff1f0bf14`.
- Historical GitHub comments remain untouched; current comments supersede them append-only.
- Independent specification implementations remain irrevocable, worldwide, royalty-free, commercial and non-commercial, with mandatory LLM Errata, Thomas Willner, and repository attribution.
- Reference code under `prototype/`, `scripts/`, and `tests/` remains personal-use.
- Invitation, publication, maintainer work, and CI remain recruitment/internal evidence, never independent readiness evidence.
- G2 through G6 stay `BLOCKED` unless their existing external-evidence contracts are met.

---

### Task 1: Active-Surface Manifest and Checker

**Files:**
- Create: `publication/active-surfaces.json`
- Create: `scripts/check_publication.py`
- Create: `tests/test_publication.py`

**Interfaces:**
- Consumes: fixed commit/digest and public URLs already verified in `docs/PUBLICATION_LOG.md`.
- Produces: `validate_manifest(payload: object) -> list[str]`, `load_manifest(path: Path) -> object`, and CLI exits `0` pass, `1` invalid, `2` inconclusive.

- [ ] **Step 1: Write failing baseline and mutation tests**

Create tests that require the unmodified manifest/checker to pass and mutations to reject:

```python
class PublicationGuardRejectsDrift(unittest.TestCase):
    def test_stale_commit_is_rejected(self) -> None: ...
    def test_stale_digest_is_rejected(self) -> None: ...
    def test_obsolete_permission_language_is_rejected(self) -> None: ...
    def test_missing_required_surface_is_rejected(self) -> None: ...
    def test_duplicate_mention_is_rejected(self) -> None: ...
    def test_invitation_cannot_be_called_independent_evidence(self) -> None: ...
```

Each mutation runs `check_publication.py` against a disposable repository copy and asserts exit `1` plus a specific diagnostic label.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_publication -v
```

Expected: import/file failures because manifest and checker do not exist.

- [ ] **Step 3: Create exact manifest**

Write schema version `1`, exact target/digest, licence object, and these active IDs:

```text
g2-g3-targeted-review
g4-targeted-implementation
g5-targeted-systems
pr8-correction
discussion9-correction
```

Bind their exact published URLs, gates, distinct evidence roles, exact mentions, superseded URLs, and `recruitment-only` or `publication-only` boundary.

- [ ] **Step 4: Implement minimal dependency-free checker**

Implement strict type/key/regex/date/URL validation, exact canonical target, exact required IDs/URLs, unique roles/mentions, licence contract, and forbidden stale/permission/evidence language. Missing/unreadable JSON returns exit `2`; well-formed invalid contract returns exit `1`.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_publication -v
python3 scripts/check_publication.py
```

Expected: all focused tests pass and CLI reports every publication contract check passed.

- [ ] **Step 6: Commit manifest and checker**

```bash
git add publication/active-surfaces.json scripts/check_publication.py tests/test_publication.py
git commit -m "feat: guard active publication surfaces"
```

### Task 2: Repository and CI Integration

**Files:**
- Modify: `Makefile`
- Modify: `.github/workflows/validate.yml`
- Modify: `scripts/validate_repo.py`
- Modify: `tests/test_validate_repo.py`
- Modify: `AGENTS.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/PUBLICATION_STRATEGY.md`

**Interfaces:**
- Consumes: `scripts/check_publication.py` from Task 1.
- Produces: `make publication`; `make check` and CI enforce the manifest; contributor instructions preserve active/historical distinction.

- [ ] **Step 1: Write failing integration tests**

Add required-file mutations for the manifest, checker, and focused tests. Add focused assertions that `Makefile` routes `check` through `publication` and the workflow runs `make publication`.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_validate_repo tests.test_publication -v
```

Expected: integration assertions fail because Make/CI wiring and required-file declarations are absent.

- [ ] **Step 3: Wire Make, CI, and required files**

Add:

```make
publication:
	$(PYTHON) scripts/check_publication.py
```

Place `publication` in `check` before `test`, add an explicit GitHub Actions step, and add all three Task 1 files to `REQUIRED_FILES`.

- [ ] **Step 4: Document publication discipline**

Update agent/contributor/publication documents to require:

1. active manifest update for every supersession;
2. `git cat-file -e <commit>:<path>` before pinned blob publication;
3. live read-after-write verification;
4. recruitment evidence never upgrades readiness.

- [ ] **Step 5: Run integration tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_validate_repo tests.test_publication -v
make publication
```

Expected: all focused checks pass.

- [ ] **Step 6: Commit integration**

```bash
git add Makefile .github/workflows/validate.yml scripts/validate_repo.py tests/test_validate_repo.py AGENTS.md CONTRIBUTING.md docs/PUBLICATION_STRATEGY.md
git commit -m "ci: enforce current publication contract"
```

### Task 3: Full Evidence Closure and Publication

**Files:**
- Modify if needed: `docs/PUBLICATION_LOG.md`
- Modify ignored: `.scratch/g2-publication/loop-state.yaml`

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: pushed branch, exact-head CI evidence, clean worktree, unchanged readiness verdict.

- [ ] **Step 1: Run complete local validation**

```bash
make check
make links
make cli-demo
git diff --check
```

Expected: 262 or more tests pass, all publication checks pass, all URLs resolve under repository policy, CLI repair exits expected `2`, and no whitespace error exists.

- [ ] **Step 2: Reconcile live GitHub state**

Verify the five active URLs render the admitted owner-authored comments, six mentions remain role-specific, and no external response arrived without analysis.

- [ ] **Step 3: Update durable loop state**

Record manifest/checker evidence, local validation, external response inventory, budget use, and `BLOCKED` verdict for missing external evidence.

- [ ] **Step 4: Push branch**

```bash
git push origin agent/g2-publication
```

- [ ] **Step 5: Verify exact-head CI and SHA equality**

Require Python 3.11 and 3.13 success for exact final head, local/remote SHA equality, clean tracked worktree, and draft PR #8 pointing to exact head.

- [ ] **Step 6: Stop without self-reference loop**

Do not create another tracked publication-log commit solely to record the final commit or CI run. Report those externally and preserve the worktree for responses.
