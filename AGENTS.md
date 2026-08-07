# Agent Working Agreement

This file governs coding, research, review, and documentation work in the LLM Errata repository. It is model-agnostic: every automated or human-assisted agent must follow the same evidence, safety, and validation rules.

## Agent skills

### Issue tracker

Local markdown under `.scratch/<feature>/`, git-ignored, private to the build. Public intake is GitHub Issues once the repository is published. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical roles, unchanged: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repository root. See `docs/agents/domain.md`.

## Preserve the core proposal

LLM Errata is a vendor-neutral conformance proposal for what happens after an update to imported AI memory crosses a system boundary. Its core contract is:

1. authenticate and sequence the update;
2. quarantine the affected root and its known descendants before repair or recall;
3. retire or rebuild affected descendants from still-valid inputs;
4. run negative, positive, and preservation checks;
5. return a signed, coverage-aware receipt or callback that identifies verified, partial, unknown, or failed coverage. `Pending` is a lifecycle state, not terminal success.

The central thesis is: **An imported memory is a dependency, not a copy.** Do not weaken this into ordinary synchronization, deletion, provenance, or notification. Those are inputs to the proposal, not the complete proposal.

## Inspect before changing

Before making a change:

1. Read `README.md`, `IDEA.md`, and the file being changed.
2. For novelty, standards, or comparison work, also read `RESEARCH.md` and `PRIOR_ART.md`.
3. For implementation or protocol work, also read `ROADMAP.md`, `SECURITY.md`, and relevant contribution requirements.
4. Search the repository for the affected term, invariant, link, status, and example.
5. Identify whether the change affects the core claim, public evidence, conformance behavior, privacy, security, or version metadata.

Do not infer repository state from a single excerpt. Preserve established terminology and cross-file consistency.

## Change discipline

- Prefer the smallest complete change that resolves the issue.
- Make additive changes when new evidence or detail is needed. Do not silently remove qualifications, prior art, limitations, attribution, tests, or security boundaries.
- Preserve existing file names, public links, definitions, and interfaces unless the requested change requires a documented migration.
- Keep normative requirements separate from examples, aspirations, and research hypotheses.
- Update every directly affected document when a definition, status, version, or claim changes.
- Do not add empty scaffolding, speculative integrations, invented results, or unverifiable citations.

## Maintain the semantic distinctions

Never collapse these operations:

- **Correction:** an earlier proposition was wrong for all or part of the interval it claimed to describe.
- **Supersession:** an earlier proposition was true and later stopped being true.
- **Erasure:** a proposition must no longer be retained or used, regardless of whether it was true.

The distinction must survive schemas, examples, tests, state transitions, receipts, and documentation. Erasure evidence must not repeat the value it claims to erase.

Quarantine always precedes repair. Once a valid update is observed, the affected root and its known descendant closure must not remain available to declared recall paths while slower rebuild work runs. If a required retrieval gate cannot quarantine affected state, report failure or incomplete coverage and follow the applicable fail-closed policy.

Maintain the complete repair triad:

- **Negative:** the retired proposition does not reappear within the declared scope.
- **Positive:** the replacement or required post-update state is active where it should be.
- **Preservation:** unrelated retained memory still works.

For erasure, there is no positive replacement value. A positive check may verify the required content-free post-erasure behavior or policy state; it must not preserve or reconstruct erased content.

## Never overclaim

### Novelty

Describe LLM Errata as a **novel synthesis with a narrow, apparently unimplemented conformance gap in the reviewed public sources as of the stated research date**. Public searching cannot prove universal nonexistence. Never claim a world first, patentability, legal priority, freedom to operate, or that no equivalent system can exist. New prior art must narrow, correct, or retire the claim when the evidence warrants it.

### Deletion and erasure

Do not equate a deletion request, notification, tombstone, receipt, or passed probe with complete deletion. Backups, logs, screenshots, model weights, provider-controlled caches, copied prose, and severed lineage may be outside observable or controllable scope. State those boundaries.

### Semantic proof

Signatures authenticate actors and bytes. Lineage provides structural evidence. Probes provide scoped behavioral evidence. None is a mathematical proof that a model can never express, reconstruct, or remain influenced by a retired proposition. Record test scope, uncertainty, verifier configuration, and known blind spots.

### Coverage

Never convert missing lineage, inaccessible stores, skipped tests, timeouts, or unsupported adapters into success. A receipt must use the canonical terminal results `verified`, `partial`, `unknown`, and `failed`. `Pending` remains a lifecycle state, and stores outside the required scope are omitted. Aggregate success requires every required store to be `verified`.

## Research and citations

- Prefer primary sources: normative standards, official specifications and documentation, original papers, source repositories, and patent records.
- Cite the exact page, version, draft, release, commit, or publication date where available.
- Record access dates for mutable sources when the research protocol requires them.
- Explain what a source actually overlaps; a citation alone does not establish a collision.
- Separate source statements from inference, comparison, and project judgment.
- Treat search-result snippets, generated summaries, and uncited assertions as discovery aids, not evidence.
- Respect quotation, copyright, license, confidentiality, and personal-data boundaries.
- Preserve contrary and partial-collision evidence. Do not select sources only because they support the proposal.

## Implementation and test expectations

- Use synthetic fixtures; never add real personal, customer, employer, credential, or confidential data.
- Make authorization, identity binding, sequencing, replay handling, scope, timeouts, and failure states explicit.
- Record lineage at import and derivation time rather than attempting to reconstruct exact lineage only after an erratum arrives.
- Gate stale recall before slow mutation or rebuild work.
- Exercise correction, supersession, erasure, rollback, sequence gaps, mixed-source rebuild, stale reimport, opaque stores, and partial failure.
- Verify receipt binding to the erratum and relevant pre-repair and post-repair state.
- Keep deterministic structural checks separate from model-graded behavioral probes.
- Never mark an opaque required store green merely because accessible stores passed.

## Required completion check

Before presenting work as complete:

1. Review the diff and confirm that requested scope is covered without unrelated rewrites.
2. Recheck the core claim, three operation meanings, quarantine-before-repair order, repair triad, coverage honesty, and bounded novelty wording.
3. Verify every added or changed factual claim against an appropriate primary source, and record the pin and access date in `SOURCES.md`.
4. Run:

   ```bash
   make check
   ```

   This runs three things, and each answers a different question:

   - `scripts/validate_repo.py` — is the repository structurally well formed?
   - `scripts/claim_guard.py` — does the documentation still state the bounded claim? It anchors to exact sentences in named files, because keyword presence over the whole corpus cannot tell a hedge from its inversion.
   - `tests/` — do those two checkers actually reject the faults they claim to catch? A checker that has only ever passed has not been shown to work.

   Run `make links` as well whenever a citation is added or changed.

5. Run any additional tests relevant to changed implementation files.
6. Report validation failures, unresolved evidence gaps, and unsupported coverage honestly. Do not suppress or relabel a failing check.

   `claim_guard.py` exits `2` for *inconclusive* when a guarded file is missing or unreadable. Inconclusive is not a pass. Treat it as a blocker and say so.

   If a guard is wrong, fix the guard in its own change with a test that fails first. Never widen an anchor, delete a test, or add an entry to `ALLOWED_QUOTATIONS` in order to make an unrelated change pass.
