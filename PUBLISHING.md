# Publishing Checklist

This file records the repository settings and release steps for the first public publication. It is operational guidance, not part of the novelty claim.

## Repository identity

- **Repository name:** `llm-errata`
- **Visibility:** public
- **Default branch:** `main`
- **Description:** `A vendor-neutral conformance proposal for repairing derived AI memory after post-export correction, supersession, or erasure.`
- **Website:** leave empty until a project page or specification URL exists
- **Topics:** `llm`, `ai-memory`, `agent-memory`, `memory-portability`, `provenance`, `interoperability`, `conformance`, `ai-governance`, `ai-safety`

Do not call the repository a standard, certified protocol, proven deletion system, or world-first invention.

## Before making the repository public

1. Run `make check` from the repository root. It must exit zero. Exit `2` from the claim guard is *inconclusive*, not a pass.
2. Run `make links`. Every cited URL must resolve or be reported as `blocked`, never `dead`.
3. Review the author name, date, independent-publication disclaimer, and AI-assisted research disclosure.
4. Check every claim in `PRIOR_ART.md` against the cited primary or authoritative source.
5. Request a public archive snapshot for each source listed as unpinned in `SOURCES.md`, then replace `none` with the snapshot URL. These are the sources the collision matrix depends on most and the ones most likely to change.
6. Confirm that no employer, customer, personal, confidential, or credential material is present.
7. Confirm that `VERSION`, `CITATION.cff`, `CHANGELOG.md`, and the release tag agree with each other. Never re-tag existing content with an older version: the prior-art claim is dated, and a release tag that back-dates it corrupts the only thing this repository is for.
8. Enable GitHub Issues.
9. Enable GitHub private vulnerability reporting before pointing readers to `SECURITY.md`.
10. Decide whether GitHub Discussions should be enabled for design debate; keep factual corrections and prior-art challenges in Issues so they remain traceable.
11. Protect `main` from force pushes once external contributions begin.
12. Require green exact-head CI before merging. Request independent review for changes to the bounded novelty statement or source comparison when a qualified reviewer is available, but do not represent reviewer silence as evidence or make an experimental release depend indefinitely on an unavailable volunteer.
13. Use `.github/CODEOWNERS` to route relevant review requests. In a sole-owner repository, do not configure a mandatory CODEOWNER approval that only the author can provide and GitHub will not count; preserve required checks, force-push protection, deletion protection, and the public review trail instead.
14. Confirm the `validate` workflow has run green on `main` at least once, and make it a required status check for pull requests.
15. Create the `prior-art`, `correction`, `conformance`, `implementation`, and `maintenance` labels used by the issue forms and Dependabot.
16. Publish [REVIEW_REQUEST.md](REVIEW_REQUEST.md), [INDEPENDENT_IMPLEMENTATION.md](INDEPENDENT_IMPLEMENTATION.md), and [PHASE3_SYSTEMS.md](PHASE3_SYSTEMS.md) only as calls for evidence. Record an external review, independent implementation, or system experiment in the readiness ledger only after its dated, independently produced result exists.

## Experimental release policy

Publishing an experimental version and declaring production readiness are
different decisions. A release may be cut when the exact release tree passes
required CI, metadata and links are internally consistent, ownership and
licence boundaries are explicit, and release notes enumerate the unresolved
production gates. G2–G6 stay `BLOCKED` until their evidence contracts are met,
but their blocked status does not require the maintainer to wait indefinitely
for unsolicited external review before publishing a better experimental build.

External challenge remains welcome and must be evaluated when it arrives.
Silence is neither approval nor a blocker; it provides no readiness evidence.
Branch protection must require the Python 3.11 and 3.13 validation contexts,
disallow force pushes and deletion, and avoid an impossible sole-owner approval
requirement. A future independent maintainer may restore mandatory approval
after their identity, role, and conflict boundaries are documented.

## Suggested first commit

```text
docs: publish LLM Errata concept and research record
```

## Suggested first release

- **Tag:** `v0.1.0`
- **Title:** `LLM Errata 0.1.0 — Public Concept Proposal`
- **Release summary:**

  ```text
  Initial public release of LLM Errata, a vendor-neutral proposal for
  post-export AI-memory updates, importer-side descendant quarantine and
  repair, three-way behavioral verification, and signed coverage-aware
  receipts. This release contains the researched idea, prior-art matrix,
  public decision record, roadmap, contribution policy, and validation tool.
  It is a concept and request for comment, not a production protocol.
  ```

## Public announcement wording

> I am publishing LLM Errata as an open concept and request for technical challenge. The premise is simple: an imported AI memory should be treated as a dependency, not a dead copy. When its source is corrected, superseded, or erased, importers should quarantine known descendants, repair affected state, run negative–positive–preservation checks, and report what they could not verify. The repository includes the complete idea, the prior-art collisions that narrowed it, the research method, and explicit conditions under which the proposal should be changed or abandoned.

Link to the repository only after its final public URL exists. Do not invent or reserve a URL in the documentation before publication.

The repository was published on 2026-08-07 at https://github.com/thomaswillner/llm-errata. The CI badge, the changelog compare links, and `CODEOWNERS` were added in the first post-publication commit, which is what this paragraph previously deferred.

## After publication

- archive exact source versions or commit references when a mutable dependency materially affects the novelty comparison;
- classify incoming prior art as complete collision, partial collision, adjacent mechanism, or irrelevant;
- update `RESEARCH.md`, `PRIOR_ART.md`, and `CHANGELOG.md` together when the bounded claim changes;
- record unsuccessful implementation experiments, not only successes;
- cut a new version whenever published semantics change.
- keep [docs/PUBLICATION_STRATEGY.md](docs/PUBLICATION_STRATEGY.md) aligned with canonical repository URL, `NOT_PROD_READY` status, and external-evidence boundaries; a post, nomination, or invitation never upgrades readiness.
