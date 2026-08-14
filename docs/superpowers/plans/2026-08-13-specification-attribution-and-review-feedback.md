# Specification Attribution and Review Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grant irrevocable commercial and non-commercial implementation rights for the LLM Errata specification with mandatory Thomas Willner attribution, preserve personal-use restrictions on reference code, and incorporate the Inspeximus maintainer's remaining protocol and cryptography recommendations.

**Architecture:** Keep one custom `LICENSE` with two explicit scopes: a specification implementation grant and a personal-use source-code grant. Enforce the boundary with dependency-free repository checks and negative tests. Clarify, without renumbering the four-part conjunction, that requirement D contains independently evaluated authenticity and coverage-truthfulness properties; then freeze and publish a new G2 review commit and digest.

**Tech Stack:** Markdown, Python 3.11/3.13 standard library, `unittest`, existing repository validators, Git, GitHub CLI.

## Global Constraints

- The specification implementation grant is irrevocable, worldwide, royalty-free, and non-exclusive for versions released under it.
- Commercial, governmental, academic, standards, research, personal, hosted-service, and distributed-product implementations are permitted.
- Every commercial or non-commercial product or service implementing a material part of the specification must name `LLM Errata`, `Thomas Willner`, and `https://github.com/thomaswillner/llm-errata` in an ordinarily accessible About, Legal, documentation, acknowledgements, or NOTICE location.
- Attribution must not imply endorsement, sponsorship, certification, audit, or responsibility.
- `prototype/`, `scripts/`, and `tests/` remain personal-use source code; independent product code may implement `spec/` but may not copy reference code without separate permission.
- `spec/vendor/` remains governed only by third-party licences.
- Version 0.2.0 and earlier retain irrevocable Apache-2.0 rights.
- No patent licence or certification status is granted.
- Preserve correction, supersession, erasure, quarantine-before-repair, repair triad, content-free erasure evidence, and fail-closed coverage semantics.
- Repository verdict remains `NOT_PROD_READY`; interested-party feedback cannot satisfy G2 independently.

---

### Task 1: Machine-Enforced Dual Licence Contract

**Files:**
- Modify: `tests/test_validate_repo.py`
- Modify: `scripts/validate_repo.py`
- Modify: `LICENSE`

**Interfaces:**
- Consumes: `read_utf8()`, `Reporter.check()`, and `check_publication_metadata()` in `scripts/validate_repo.py`.
- Produces: deterministic `license and notice` validation covering implementation rights, attribution, source-code boundary, no endorsement, no patent grant, and historical Apache rights.

- [ ] **Step 1: Write failing negative tests**

Add tests that mutate one exact licence property at a time:

```python
def test_specification_implementation_grant_cannot_be_removed(self) -> None:
    def mutate(root: Path) -> None:
        rewrite(
            root / "LICENSE",
            "commercial and non-commercial products and services",
            "personal non-commercial experiments",
        )
    result = check_after(SCRIPT, mutate)
    self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
    self.assertIn("license and notice", result.stdout)

def test_required_product_attribution_cannot_be_removed(self) -> None:
    def mutate(root: Path) -> None:
        rewrite(root / "LICENSE", "Thomas Willner", "the author")
    result = check_after(SCRIPT, mutate)
    self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
    self.assertIn("license and notice", result.stdout)

def test_reference_code_cannot_be_relicensed_by_the_specification_grant(self) -> None:
    def mutate(root: Path) -> None:
        rewrite(
            root / "LICENSE",
            "does not cover `prototype/`, `scripts/`, or `tests/`",
            "also covers `prototype/`, `scripts/`, and `tests/`",
        )
    result = check_after(SCRIPT, mutate)
    self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
    self.assertIn("license and notice", result.stdout)

def test_false_endorsement_protection_cannot_be_removed(self) -> None:
    def mutate(root: Path) -> None:
        rewrite(
            root / "LICENSE",
            "does not imply endorsement, sponsorship, certification, or audit",
            "implies certification by the author",
        )
    result = check_after(SCRIPT, mutate)
    self.assertEqual(result.returncode, EXIT_FAIL, result.stdout)
    self.assertIn("license and notice", result.stdout)
```

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_validate_repo -v
```

Expected: the new tests fail because current licence lacks the specification grant and canonical attribution contract.

- [ ] **Step 3: Replace `LICENSE` with explicit dual-scope terms**

Write these sections in plain language:

1. historical Apache-2.0 rights;
2. definitions for `Specification Materials`, `Reference Code`, `Implementation`, and `Product or Service`;
3. irrevocable specification implementation grant including necessary downstream sublicensing;
4. exact product attribution and accessible-location rule;
5. no false endorsement, trademark, patent, or certification grant;
6. personal-use reference-code grant and restrictions;
7. third-party materials, contributions, termination for condition breach, and warranty disclaimer.

Canonical credit:

```text
Implements the LLM Errata specification by Thomas Willner —
https://github.com/thomaswillner/llm-errata
```

- [ ] **Step 4: Strengthen validator**

Replace the old `Personal Use Licence`-only predicate with exact required clauses:

```python
required_license = (
    "LLM Errata Specification Implementation and Personal Use Licence",
    "commercial and non-commercial products and services",
    "Implements the LLM Errata specification by Thomas Willner",
    "https://github.com/thomaswillner/llm-errata",
    "does not cover `prototype/`, `scripts/`, or `tests/`",
    "does not imply endorsement, sponsorship, certification, or audit",
    "No patent rights are granted",
    "Apache License 2.0",
    "irrevocable",
)
```

Require every string plus matching Thomas Willner copyright in `LICENSE` and `NOTICE`.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_validate_repo -v
```

Expected: all validator tests pass.

- [ ] **Step 6: Commit**

```bash
git add LICENSE scripts/validate_repo.py tests/test_validate_repo.py
git commit -m "license: permit attributed specification implementations"
```

### Task 2: Public Licence and Adoption Documents

**Files:**
- Modify: `README.md`
- Modify: `NOTICE`
- Modify: `INDEPENDENT_IMPLEMENTATION.md`
- Modify: `CONTRIBUTING.md`
- Modify: `SECURITY.md`
- Modify: `CHANGELOG.md`
- Test: `tests/test_validate_repo.py`

**Interfaces:**
- Consumes: dual-scope terms from Task 1.
- Produces: synchronized user-facing adoption instructions and canonical attribution.

- [ ] **Step 1: Add failing synchronization tests**

Add one table-driven test asserting required phrases in each surface:

```python
def test_public_documents_state_the_dual_license_boundary(self) -> None:
    with repo_copy() as root:
        required = {
            "README.md": ("commercial and non-commercial", "Thomas Willner"),
            "NOTICE": ("LLM Errata specification by Thomas Willner",),
            "INDEPENDENT_IMPLEMENTATION.md": ("No per-implementer permission",),
            "CONTRIBUTING.md": ("independently authored implementation",),
        }
        for name, phrases in required.items():
            text = (root / name).read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, name)
```

- [ ] **Step 2: Run focused test and verify RED**

Run the exact new test. Expected: FAIL on current personal-use-only wording.

- [ ] **Step 3: Synchronize documents**

- `README.md`: describe repository as source-available; permit attributed independent specification implementations; retain personal-use reference-code boundary.
- `NOTICE`: add canonical credit and dual-scope notice.
- `INDEPENDENT_IMPLEMENTATION.md`: remove written-permission intake; state that clean-room implementations need no individual grant and must preserve attribution.
- `CONTRIBUTING.md`: distinguish implementation reports from copying reference code.
- `SECURITY.md`: state security support does not certify third-party implementations and licence attribution does not imply endorsement.
- `CHANGELOG.md`: record accepted licensing/adoption feedback and retained limits.

- [ ] **Step 4: Run focused tests and validator**

```bash
python3 -m unittest tests.test_validate_repo -v
python3 scripts/validate_repo.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md NOTICE INDEPENDENT_IMPLEMENTATION.md CONTRIBUTING.md SECURITY.md CHANGELOG.md tests/test_validate_repo.py
git commit -m "docs: publish attributed implementation grant"
```

### Task 3: Separate Receipt Authenticity from Coverage Truthfulness

**Files:**
- Modify: `scripts/claim_guard.py`
- Modify: `tests/test_claim_guard.py`
- Modify: `README.md`
- Modify: `IDEA.md`
- Modify: `RESEARCH.md`
- Modify: `PRIOR_ART.md`
- Modify: `REVIEW_REQUEST.md`
- Modify: `ROADMAP.md`
- Modify: `spec/README.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: existing receipt schema and `Receipt.verify()`/`aggregate_coverage()` behavior.
- Produces: one four-part conjunction whose callback requirement has two independently testable subproperties.

- [ ] **Step 1: Add failing claim-guard tests**

Add exact anchors and negative tests for:

```text
Signature validity authenticates the importer and receipt bytes; it does not establish that the reported coverage is truthful.
Coverage truthfulness requires the signed stores, aggregate, and limitations to match the declared required scope without upgrading missing or opaque evidence.
```

Each test replaces one sentence with its unsafe inversion and expects `claim_guard.py` exit `1`.

- [ ] **Step 2: Run focused claim tests and verify RED**

```bash
python3 -m unittest tests.test_claim_guard -v
```

Expected: new anchor tests fail because the canonical sentences are absent.

- [ ] **Step 3: Update normative prose consistently**

Keep four top-level requirements. Rename D to `Authenticated and coverage-truthful callback`, then define:

- `D1 Authenticity`: valid signature over event, importer, pre/post state, stores, aggregate, and limitations;
- `D2 Coverage truthfulness`: signed coverage matches declared required scope; missing, opaque, skipped, or failed evidence cannot become success.

State the two canonical sentences above in `IDEA.md`, add matching concise language elsewhere, and preserve existing bounded novelty wording.

- [ ] **Step 4: Add exact anchors to `claim_guard.py`**

Guard both canonical sentences in `IDEA.md`. Do not weaken existing anchors or add quotation exceptions.

- [ ] **Step 5: Run claim and schema/controller suites**

```bash
python3 -m unittest tests.test_claim_guard tests.test_schema tests.test_controller -v
```

Expected: PASS; runtime/schema behavior remains unchanged.

- [ ] **Step 6: Commit**

```bash
git add scripts/claim_guard.py tests/test_claim_guard.py README.md IDEA.md RESEARCH.md PRIOR_ART.md REVIEW_REQUEST.md ROADMAP.md spec/README.md CHANGELOG.md
git commit -m "docs: separate receipt authenticity from coverage truth"
```

### Task 4: Promote Cryptographic Refusal Evidence

**Files:**
- Modify: `docs/CRYPTOGRAPHY_QUALIFICATION.md`
- Modify: `tests/test_readiness.py`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `VerificationRefusesBadInput` in `tests/test_ed25519.py`.
- Produces: qualification record that distinguishes refusal-path evidence from signing compatibility and production assurance.

- [ ] **Step 1: Add failing readiness-document test**

Require the qualification to enumerate:

```python
for phrase in (
    "non-canonical scalar",
    "malformed public-key and signature lengths",
    "tampered message",
    "tampered signature",
    "wrong public key",
):
    self.assertIn(phrase, qualification)
```

- [ ] **Step 2: Run focused test and verify RED**

Run the exact test. Expected: FAIL for absent refusal-evidence summary.

- [ ] **Step 3: Rewrite qualification evidence ordering**

Add `### Verification refusal evidence` before PyCA compatibility. Explain that refusal tests are stronger security-relevant reference evidence than successful vector reproduction, while neither proves constant-time behavior or production readiness. Link each phrase to the existing test method name without adding external citations.

- [ ] **Step 4: Run focused readiness and Ed25519 tests**

```bash
python3 -m unittest tests.test_readiness tests.test_ed25519 -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/CRYPTOGRAPHY_QUALIFICATION.md tests/test_readiness.py CHANGELOG.md
git commit -m "docs: foreground cryptographic refusal evidence"
```

### Task 5: Freeze, Publish, and Verify the New Review Target

**Files:**
- Modify: `docs/PUBLICATION_LOG.md`
- Modify: ignored `.scratch/g2-publication/loop-state.yaml`
- Create: ignored `.scratch/g2-publication/maintainer-reply.md`

**Interfaces:**
- Consumes: committed normative surface from Tasks 1-4 and `g2_surface_digest_at_commit()`.
- Produces: new immutable G2 commit/digest, natural maintainer reply, publication log entries, pushed branch, and exact-head CI evidence.

- [ ] **Step 1: Run complete deterministic validation**

```bash
make check
make cli-demo
git diff --check
```

Expected: 250 or more tests pass; demo exits through its expected wrapper result; no whitespace errors.

- [ ] **Step 2: Freeze and verify source target**

Record current `git rev-parse HEAD` as the new review commit. Compute:

```bash
python3 -c 'from scripts.check_readiness import g2_surface_digest; print(g2_surface_digest())'
review_commit=$(git rev-parse HEAD)
python3 -c 'import sys; from scripts.check_readiness import g2_surface_digest_at_commit; print(g2_surface_digest_at_commit(sys.argv[1]))' "$review_commit"
```

Expected: identical 64-character digests.

- [ ] **Step 3: Draft a human maintainer reply**

Reply substance:

- thank them for checking code and correcting their own earlier assumption;
- say `retract_lineage`/`rederive` and Doyle were incorporated;
- say requirement D now separates authenticity from coverage truthfulness;
- say the cryptography record now foregrounds refusal paths;
- answer licence question directly: revocability was deliberate for reference code, but their adoption concern was persuasive, so independent specification implementations now receive an irrevocable royalty-free grant with mandatory Thomas Willner/LLM Errata attribution;
- preserve no-endorsement and conflict boundaries;
- provide exact commit, digest, and review contract;
- invite their proposed quarantine/equivocation/undeclared-lineage review.

Avoid corporate boilerplate, exaggerated praise, or readiness claims.

- [ ] **Step 4: Push source target and verify CI**

```bash
git push origin agent/g2-publication
review_commit=$(git rev-parse HEAD)
run_id=$(gh run list --repo thomaswillner/llm-errata --branch agent/g2-publication --limit 10 --json databaseId,headSha --jq '.[] | select(.headSha == "'"$review_commit"'") | .databaseId' | head -1)
test -n "$run_id"
gh run watch "$run_id" --repo thomaswillner/llm-errata --exit-status
```

Expected: Python 3.11 and 3.13 pass for exact source commit.

- [ ] **Step 5: Publish reply and record URL**

```bash
gh issue comment 4 --repo thomaswillner/llm-errata --body-file .scratch/g2-publication/maintainer-reply.md
```

Add reply URL, new G2 target, digest, accepted recommendations, and evidence boundary to `docs/PUBLICATION_LOG.md`.

- [ ] **Step 6: Commit and push publication record**

```bash
git add docs/PUBLICATION_LOG.md
git commit -m "docs: publish attributed review target"
git push origin agent/g2-publication
```

- [ ] **Step 7: Final verification**

Require:

- clean worktree;
- local HEAD equals `origin/agent/g2-publication`;
- exact-head Python 3.11 and 3.13 CI green;
- PR #8 remains open and points to exact head;
- G2 remains `BLOCKED` with no qualifying independent review.

- [ ] **Step 8: Commit no further self-referential publication changes**

Stop after reporting final commit, frozen source commit/digest, public reply URL, validations, and remaining external blockers.
