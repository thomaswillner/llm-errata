## What this changes

<!-- The problem being addressed, and the files and claims affected. -->

## Evidence

<!--
Required for any changed factual claim: primary source, stable URL, and the
version, draft, release, or commit. Add an access date for mutable pages.
Explain what the source actually overlaps — a citation alone establishes
nothing.
-->

## Type of change

- [ ] Editorial only, no technical meaning changed
- [ ] Factual correction to a source, figure, status, or date
- [ ] Prior-art record: narrows, corrects, or retires part of the claim
- [ ] Conformance or normative behaviour
- [ ] Tooling, tests, or CI
- [ ] Implementation or fixtures

## Checks

- [ ] `make check` passes locally
- [ ] `make links` run, if a citation was added or changed

## Invariants

Confirm the change preserves each of these, or explain in the description why it
should not:

- [ ] Quarantine still precedes repair
- [ ] Correction, supersession, and erasure remain distinct operations
- [ ] The repair triad is intact: negative, positive, preservation
- [ ] No path turns `unknown`, `partial`, or `failed` coverage into aggregate success
- [ ] No erasure evidence retains the value it claims to erase
- [ ] Novelty wording stays bounded and dated: no world first, no patentability, no freedom to operate

## Removals

<!--
AGENTS.md forbids silently removing qualifications, prior art, limitations,
attribution, tests, or security boundaries. If this PR removes any of those,
list them here and say why. Write "none" if it does not.
-->

none
