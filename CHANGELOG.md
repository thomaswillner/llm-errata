# Changelog

All notable changes to LLM Errata will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for version labels.

Changes to the bounded novelty statement or the source comparison are recorded here even when they narrow or retire part of the claim. That is the intended direction of travel, not an exception.

## Unreleased

### Added

- `scripts/claim_guard.py`: an anchored guard for the bounded claim. It checks exact sentences in named files, the ordering of the loop steps, and affirmative-overclaim patterns, with a distinct exit code for *inconclusive* so a missing file can never read as a pass.
- `tests/`: self-tests for both checkers. Every guard is exercised against a corpus that misstates the proposal and is required to reject it, including an inverted quarantine/rebuild order and an asserted world first.
- `scripts/check_links.py` and a scheduled workflow: liveness for every cited URL. Hosts that filter automated clients are reported as blocked rather than dead, and a run that reaches nothing at all exits inconclusive.
- `SOURCES.md`: a pinned source record with commit SHAs, draft revisions, arXiv versions, independent re-verification notes, and an explicit list of the load-bearing sources that have no archive snapshot.
- `.github/`: validation workflow on push and pull request, issue forms for prior-art challenges, factual corrections, conformance proposals, and implementation or failure reports, a pull-request template that requires the invariants to be reconfirmed, a Dependabot policy for action versions, and a `CODEOWNERS` example.
- `CODE_OF_CONDUCT.md`, `Makefile`, `.editorconfig`, and `.gitattributes`.

### Changed

- `scripts/validate_repo.py` is now a linter only. Its eight keyword-presence checks over the concatenated corpus could not distinguish the bounded claim from its inversion — a document asserting a world first still contains the string "world first" — so responsibility for the claim moved to `claim_guard.py`, where it is anchored and tested.
- The release-version check compares `VERSION` with `CITATION.cff` and a semantic-version shape instead of a hard-coded literal.
- The Glean figure now names its denominator. The report states that 77% *of AI users* bounce between multiple tools weekly; the documentation had attributed the percentage to all 6,000 surveyed digital workers.

### Fixed

- `CHANGELOG.md` used `[version]` heading syntax with no link definitions, so the headings rendered as literal brackets, and it listed a placeholder as though it were a change. Version headings are now plain until the repository has a public URL to compare against.

## 0.1.0 - 2026-08-01

### Added

- Initial public concept proposal for LLM Errata.
- Research and prior-art framing for the bounded novelty claim.
- Proposed lifecycle for update delivery, descendant quarantine, repair, verification, and coverage-aware receipts.
- Initial repository contribution, security, citation, licensing, and version metadata.
