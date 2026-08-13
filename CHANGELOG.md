# Changelog

All notable changes to LLM Errata will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for version labels.

Changes to the bounded novelty statement or the source comparison are recorded here even when they narrow or retire part of the claim. That is the intended direction of travel, not an exception.

## [Unreleased](https://github.com/thomaswillner/llm-errata/compare/v0.3.0...HEAD)

### Added — production-readiness evidence

- Corrected two conflict-disclosed external findings. Importers now remember
  same-view sequence conflicts across separate observe calls, while receipts
  explicitly disclaim global non-equivocation across split views. Required
  adapters must establish root-specific lineage completeness before an empty
  enumeration can receive `verified`; unsupported empty walks become `unknown`
  with a signed limitation. The earlier categorical comparison claiming LLM
  Errata was stricter than Inspeximus is withdrawn and replaced with the
  verified limits and remediations in both projects.
- Upgraded both GitHub Actions workflows to immutable `actions/checkout`
  v7.0.1 and `actions/setup-python` v7.0.0 commit pins. Both action releases use
  Node 24, removing GitHub's Node 20 deprecation path without changing the
  Python 3.11/3.13 validation matrix or local Node runtime. Repository lint and
  negative tests now reject missing, mutable, or downgraded action references.
- Granted irrevocable, worldwide, royalty-free rights for independently
  authored commercial and non-commercial implementations of the specification,
  conditioned on accessible product attribution to LLM Errata and Thomas
  Willner. Reference code remains personal-use, no patent or certification
  right is granted, and the historical Apache-2.0 grant remains unchanged.
- Split the callback requirement into independently evaluated authenticity and
  coverage-truthfulness properties. A valid signature authenticates the
  importer and receipt bytes; it cannot turn overstated, missing, or opaque
  coverage into a truthful claim.
- Reordered the production-cryptography qualification to foreground observed
  refusal of malformed lengths, non-canonical scalars, tampered messages and
  signatures, and wrong keys. Successful RFC vectors remain compatibility
  evidence and do not establish constant-time or production assurance.

- Corrected the Inspeximus comparison after conflict-disclosed maintainer
  feedback and source verification. `retract_lineage` plus `rederive` is a
  stronger local quarantine/rebuild collision than the earlier erasure-focused
  row; its coverage audit remains weaker than required-store aggregation.
- Completed internal Phase 2 conformance surface with owner-key rotation,
  rotated-key refusal, concurrent sequence-conflict, invalid-target,
  content-free confidentiality, and every-field receipt-binding vectors. G2
  remains `BLOCKED` until dated independent review of exact committed surface.
- Added a ten-scope G6 operational evidence contract and fail-closed checker.
  One independent report must bind exact commit and deployment, declare
  workload, platform, failure domain, observation window, numeric thresholds,
  units, comparators, and raw artifacts, then pass every measurement. Internal
  tests validate the contract but leave G6 `BLOCKED`.
- Added durable `errata quarantine` checkpoints. CLI repair now requires an
  authenticated, atomic checkpoint bound to erratum, sequence, target,
  inspectable pre-state, adapters, opaque limitations, and gated artifacts;
  consumption occurs only after durable receipt and applied-state writeback.
  G2 remains `BLOCKED` for remaining Phase 2 vectors and independent review.
- Added a fail-closed production-cryptography qualification record. PyCA
  reproduced the repository's RFC 8032 vectors but documents no external
  project audit; libsodium has a published assessment for older releases, not
  the current 1.0.22 build. G3 remains `BLOCKED` pending exact-build
  qualification, lifecycle implementation, and independent security review.
- Added provider-neutral semantic probes, deterministic recorded fixtures, and `errata semantic-test` documentation as Phase 2 item 6 internal implementation. Opened independent review, independent implementation, and Phase 3 system-nomination programs. G2 remains `BLOCKED`: repository artifacts and local tests do not substitute for dated independent external review.
- Added a fail-closed production-readiness ledger and human verification matrix. Local green tests cannot produce `PROD_READY`; every required gate must pass, and external gates require dated evidence naming an independent producer.
- Added drift checks binding README maturity and SECURITY support policy to `VERSION`. The current verdict remains `NOT_PROD_READY`: only G1, document consistency, is complete.
- Normalize complete-cell Markdown presentation decoration before readiness-matrix duplicate and contradiction checks.

## [0.3.0](https://github.com/thomaswillner/llm-errata/releases/tag/v0.3.0) - 2026-08-07

### Changed — licence

- **Relicensed to a personal-use licence.** Reading, running, studying, quoting, and citing are permitted. Commercial use, redistribution, derivative works, and implementing the specifications in `spec/` require written permission.
- **Version 0.2.0 and earlier remain under the Apache License 2.0.** That grant is irrevocable: anyone who obtained those releases keeps their Apache-2.0 rights to them permanently, and nothing here withdraws it. The licence file, the notice, and `scripts/validate_repo.py` all assert that this sentence stays present, so it cannot be quietly dropped later.
- No patent licence is granted. That is a deliberate difference from the earlier releases.
- Third-party files under `spec/vendor/` are unaffected and keep their own terms. The JSON-Schema-Test-Suite is Copyright (c) 2012 Julian Berman, MIT, and its licence file now ships alongside it.

This narrows the project's own stated direction, which is recorded rather than glossed: `CONTRIBUTING.md` invites reference implementations, `ROADMAP.md` Phase 2 defines success as two independent implementations, and Phase 5 contemplates a standards path. All three now require the author's permission. Prior-art challenges, corrections, and design critique need no permission and remain the most valuable contribution.


### Added — the Phase 2 conformance surface

- **A published wire schema.** `spec/` carries JSON Schemas for the erratum and the receipt, 19 conformance vectors, and a manifest naming the rule each invalid vector must trip. An invalid vector is not satisfied by being rejected; it must be rejected for the stated reason, and the set must trip at least four distinct rules.
- **`prototype/schema.py`**, a dependency-free validator. Unknown keywords raise rather than being ignored: skipping a keyword accepts instances the published schema rejects, which is worse than having no validator. The official JSON-Schema-Test-Suite is vendored unmodified and found four real bugs on first run — `enum` and `const` treating `False` as equal to `0`, `$ref` dropping its sibling keywords under draft 2020-12, `1.0` rejected as an integer, and an uncompilable ECMA-262 pattern crashing instead of refusing.
- **`prototype/sqlite_store.py`**, a real transactional store. Quarantine commits in its own transaction *before* any rebuild, so a failed repair rolls back with the gate still shut, and the gate survives the process. That is the storage-layer reason for the ordering the proposal insists on, rather than an assertion about code.
- **`prototype/residue.py`**, substrate evidence. `verified` now requires a clean scan of the store's own bytes, not an API acknowledgement. Residue found is `failed`, per IDEA.md's own definition. A scan that did not run is not a scan that came back clean, and the rule may only ever make a result worse — applying it to an `unknown` store would be an upgrade.
- **`prototype/cli.py`** and `prototype/workspace.py`: `init`, `export`, `derive`, `publish`, `pull`, `plan`, `repair`, `test`, `attest`, `audit`, `verify`, over ordinary files. `make cli-demo` drives the whole lifecycle. Exit `2` means the repair ran and the result is not verified — a distinct code, because that case is the entire proposal.

### Fixed

- `RebuildStrategy` keyed on the literal store names `markdown` and `vector`, so a third store was quarantined and then never repaired: it stayed gated, the positive probe failed, and the aggregate reported `failed` for a repair that had simply not been attempted. It is now store-agnostic, and adding a store no longer means editing it.

### Note

Running the CLI against SQLite produces the result the whole design is for: all three probes pass, and the store still reports `failed`, because the retired value is readable in `store.sqlite3-wal` after the row is gone and the API says it is deleted. That is [Ghost Vectors](https://arxiv.org/abs/2606.18497v1) reproduced with the standard library. The design very nearly shipped the same bug — the plan specified scanning the database file, in WAL mode, where the value is not.

### Added

- **Real signatures.** `prototype/ed25519.py` implements Ed25519 per RFC 8032 using only the standard library, checked against the RFC's published test vectors including the 1023-byte message. The previous keyed MAC was symmetric and therefore could not give the property this proposal actually requires: an owner publishing a verification key that no holder of it can forge against. A forged erratum is durable memory poisoning, so that was the wrong primitive for the trust boundary.
- Non-canonical scalars (`S >= L`) are rejected, so a receipt cannot be altered into a second valid signature.
- `THREAT_MODEL.md`: actors, what is defended and where, and what is not — a lying importer, a store whose substrate contradicts its API, unregistered copies, semantic re-derivation, probe identifiability, key compromise. The sharpest open problem is stated as one: coverage honesty has no adversary, and an adapter is trusted to characterise itself.

### Note on the test vectors

The first version of `tests/test_ed25519.py` recited RFC 8032 TEST 1 from memory and got the secret key wrong, then spent an hour attributing the mismatch to the curve arithmetic. The implementation had been correct throughout. The vectors are now extracted from the published RFC text, and the Ed25519ph vectors are excluded because they pre-hash the message and are a different algorithm.

## [0.2.0](https://github.com/thomaswillner/llm-errata/releases/tag/v0.2.0) - 2026-08-07

First public release. Version 0.1.0 was written on 2026-08-01 and never published; it is kept as a dated entry below because the prior-art claim is stated as of that date and the research record must not be back-dated to match a later release.

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
