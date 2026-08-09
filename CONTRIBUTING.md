# Contributing to LLM Errata

LLM Errata is an independent, evidence-driven proposal. Contributions are welcome from researchers, implementers, standards participants, vendors, auditors, and users. Participation does not imply endorsement by the author's employer or by any organization cited in this repository.

## Useful contributions

The project especially welcomes:

- prior art that predates or overlaps a claim in the proposal;
- factual corrections supported by primary or authoritative sources;
- precise challenges to the stated novelty boundary;
- conformance requirements, test cases, schemas, and threat models;
- reference implementations and interoperability experiments;
- failure reports showing that a proposed invariant is incomplete or impractical;
- editorial improvements that preserve technical meaning.

## Evidence requirements

A claim about an existing system, standard, paper, patent, product, or implementation must include enough evidence for another contributor to verify it. Prefer:

1. normative specifications, standards, official documentation, source code, papers, or patent records;
2. a stable URL or exact repository path;
3. the relevant version, draft, release, commit, or publication date where available;
4. a concise explanation of the exact feature overlap or contradiction;
5. an access date for mutable web content.

Search-result snippets, unsupported summaries, and generated assertions are not sufficient evidence. Secondary sources may provide context, but they should not replace an available primary source.

## Prior-art challenges

Prior-art challenges are treated as improvements, not adversarial noise. A useful challenge should identify:

- the specific LLM Errata requirement at issue;
- the earlier work and its date;
- where that work defines or implements the requirement;
- whether the overlap is complete or partial;
- any remaining difference in update delivery, descendant repair, verification, or receipt semantics.

Do not describe the proposal or a contribution as "world first," "unprecedented," "patentable," or otherwise proven novel. Public-source research cannot establish universal nonexistence, patentability, freedom to operate, or legal priority. Use bounded wording such as "not found in the reviewed sources as of YYYY-MM-DD."

## Conformance proposals

A conformance change should state:

- the actor and system boundary;
- the normative behavior using clear MUST, SHOULD, or MAY language;
- observable inputs, outputs, and state transitions;
- failure, timeout, replay, partial-coverage, and unobservable-store behavior;
- security and privacy consequences;
- positive, negative, and preservation tests;
- backward-compatibility implications.

Whenever possible, include machine-readable examples and deterministic tests. A receipt format must use the canonical terminal coverage results `verified`, `partial`, `unknown`, and `failed`. `Pending` is a lifecycle state, not a successful coverage result; stores outside the required scope are omitted.

## Implementations

Implementation contributions should include:

- a reproducible build and test procedure;
- supported platforms, stores, and adapter boundaries;
- explicit assumptions and unsupported cases;
- test fixtures that contain no real personal or confidential data;
- dependency and license information;
- evidence that unrelated memory is preserved during repair.

Never submit secrets, personal data, proprietary customer material, or confidential employer information.

## Issues and pull requests

Run `make check` before opening a pull request; CI covers the same four validation components: repository structure and metadata, the bounded claim, readiness-evidence honesty, and checker self-tests. Readiness-check exit `0` validates structural honesty of the recorded evidence; it does **not** mean `PROD_READY`. If a citation was added or changed, run `make links` too, and record the pin and access date in [SOURCES.md](SOURCES.md).

If a checker is wrong, fix it in its own pull request with a test that fails before the fix. Widening an anchor, deleting a test, or adding a quotation exception so that an unrelated change passes is not an acceptable fix.

Before opening a large pull request, open an issue describing the proposed change and its evidence. Keep each pull request focused. In its description, include:

- the problem being addressed;
- the files and claims affected;
- the supporting evidence;
- the tests or review performed;
- known limitations and unresolved questions.

By submitting a contribution, you grant the copyright holder a perpetual, worldwide, irrevocable, royalty-free licence to use, modify, and relicense it, and you confirm you have the right to submit the material. You retain your own copyright. See [LICENSE](LICENSE). Cite rather than copy third-party text unless its licence clearly permits inclusion.

Note that this repository is licensed for personal use. Prior-art challenges, corrections, and design critique are welcome and need no permission. Implementing the specifications in `spec/` does require written permission, which is not unreasonably withheld for research and standards work.

## Security findings

Do not disclose exploitable vulnerabilities in a public issue. Follow [SECURITY.md](SECURITY.md) instead.
