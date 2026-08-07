# Changelog

All notable changes to LLM Errata will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for version labels.

Changes to the bounded novelty statement or the source comparison are recorded here even when they narrow or retire part of the claim. That is the intended direction of travel, not an exception.

## Unreleased

### Added

- `prototype/`: the Phase 1 file-backed proof, runnable with `make demo`. One controller, three deliberately different stores, one imported root mixed into a summary, and the eight required scenarios. Standard library only, no network, no API key.
- The demo exits `2`. Both inspectable stores are fully repaired and all three probes pass, and the aggregate is still `partial` because the opaque store cannot show its own state. A test asserts that removing the opaque store is what turns the same repair `verified`, so the non-green result cannot be read as an aggregation bug.
- Non-conforming repairs are modelled as first-class strategies rather than test hacks: a wipe that destroys retained memory, an append-only repair that leaves the retired value retrievable, and an interrupted rebuild. The repair triad catches the first two; the third proves an interrupted repair fails closed.

- `scripts/claim_guard.py`: an anchored guard for the bounded claim. It checks exact sentences in named files, the ordering of the loop steps, and affirmative-overclaim patterns, with a distinct exit code for *inconclusive* so a missing file can never read as a pass.
- `tests/`: self-tests for both checkers. Every guard is exercised against a corpus that misstates the proposal and is required to reject it, including an inverted quarantine/rebuild order and an asserted world first.
- `scripts/check_links.py` and a scheduled workflow: liveness for every cited URL. Hosts that filter automated clients are reported as blocked rather than dead, and a run that reaches nothing at all exits inconclusive.
- `SOURCES.md`: a pinned source record with commit SHAs, draft revisions, arXiv versions, independent re-verification notes, and an explicit list of the load-bearing sources that have no archive snapshot.
- `.github/`: validation workflow on push and pull request, issue forms for prior-art challenges, factual corrections, conformance proposals, and implementation or failure reports, a pull-request template that requires the invariants to be reconfirmed, a Dependabot policy for action versions, and a `CODEOWNERS` example.
- `CODE_OF_CONDUCT.md`, `Makefile`, `.editorconfig`, and `.gitattributes`.

### Changed

- `PRIOR_ART.md` records four collisions found in a supplementary screen on 2026-08-07, all published after the original cutoff. The most important is [MemoRepair](https://arxiv.org/abs/2605.07242v1), which defines a repair contract withdrawing invalidated descendants *before* repair. Quarantine-before-repair is therefore no longer distinctive and must not be presented as a contribution of this proposal. The four-part conjunction survives: MemoRepair has no cross-boundary delivery, no preservation test, and no receipt.
- `RESEARCH.md` link text for arXiv 2604.16548 now uses the paper's current title, changed at v2 on 2026-06-11.
- `scripts/validate_repo.py` is now a linter only. Its eight keyword-presence checks over the concatenated corpus could not distinguish the bounded claim from its inversion — a document asserting a world first still contains the string "world first" — so responsibility for the claim moved to `claim_guard.py`, where it is anchored and tested.
- The release-version check compares `VERSION` with `CITATION.cff` and a semantic-version shape instead of a hard-coded literal.
- The Glean figure now names its denominator. The report states that 77% *of AI users* bounce between multiple tools weekly; the documentation had attributed the percentage to all 6,000 surveyed digital workers.

### Fixed

- **Security: `repair(resume=True)` skipped authentication entirely.** An unsigned erratum from anyone was applied and produced a signed receipt. Resuming an interrupted repair now re-runs `observe`; the interruption is a reason to re-check the input, not to trust it.
- **Security: the stale-reimport guard was off by one.** It refused `sequence < applied`, so an export stamped with the sequence of the erratum that retired a proposition was accepted and carried the retired value back in. The original test asserted this behaviour as correct, which is how it survived.
- **`make demo` treated every non-zero exit as success**, so a crash passed `make check` while the ROADMAP claimed the headline result could not regress silently. It now requires exit 2 exactly.
- The correct/supersede distinction was a boolean on the receipt. `valid_from` was signed and never read, and both operations retired the artifact identically. A supersession now moves the old value to scoped history reachable only through `recall_history`; a correction and an erasure destroy it.
- `Signer` was documented as the seam Ed25519 would drop into, and no caller was typed against it. `Erratum.forward_to`, `LineageLedger.roots`, and the `required` flag were declared and unread; the first two are removed and the third now governs which stores enter a receipt.

All six were found by adversarial review after the suite was green, and each has a test in `tests/test_regressions.py` that failed before the fix.

- `CHANGELOG.md` used `[version]` heading syntax with no link definitions, so the headings rendered as literal brackets, and it listed a placeholder as though it were a change. Version headings are now plain until the repository has a public URL to compare against.

## 0.1.0 - 2026-08-01

### Added

- Initial public concept proposal for LLM Errata.
- Research and prior-art framing for the bounded novelty claim.
- Proposed lifecycle for update delivery, descendant quarantine, repair, verification, and coverage-aware receipts.
- Initial repository contribution, security, citation, licensing, and version metadata.
