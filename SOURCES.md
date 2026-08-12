# Pinned Source Record

**Research cutoff:** 2026-08-01 — the date the claim in [PRIOR_ART.md](PRIOR_ART.md) is about.

**Independent re-verification:** 2026-08-07 — the date every row below was re-fetched and re-read.

[RESEARCH.md](RESEARCH.md) and [PRIOR_ART.md](PRIOR_ART.md) both state that mutable
documentation should be pinned. This file is that pin. It exists because the
novelty claim is a **dated** statement about public sources: if a source changes
or disappears, a reader in six months cannot reproduce the comparison that
narrowed the claim, and the honest response is to withdraw it rather than to
argue from memory.

Nothing here changes the claim. It records what was checked, when, how, and what
remains unpinned.

## How to read this file

- **Pin** — the immutable identifier where one exists: an RFC number, an arXiv
  version, an Internet-Draft revision, a Git commit. A row with no pin rests on
  a mutable page.
- **Snapshot** — a public archive copy. `none` means no snapshot existed when
  this file was written, so the row is **unpinned** and at risk.
- **Verified** — what was actually read and confirmed on the re-verification
  date, as distinct from what the source is merely cited for.

## Immutable sources

These carry their own version identifiers. Re-fetching them returns the same
document.

| Source | Pin | Verified 2026-08-07 |
|---|---|---|
| [Portable Agent Memory](https://arxiv.org/html/2605.11032v1) | arXiv 2605.11032v1 | Title confirmed: *Portable Agent Memory: A Protocol for Cryptographically-Verified Memory Transfer Across Heterogeneous AI Agents* |
| [Agentic Unlearning](https://arxiv.org/html/2602.17692v1) | arXiv 2602.17692v1 | Title confirmed: *Agentic Unlearning: When LLM Agent Meets Machine Unlearning* |
| [MaRS / Forgetful but Faithful](https://arxiv.org/html/2512.12856v1) | arXiv 2512.12856v1 | Title confirmed: *Forgetful but Faithful: A Cognitive Memory Architecture and Benchmark for Privacy-Aware Generative Agents*. `MaRS` is the framework name introduced in the abstract |
| [Survey on Long-Term Memory Security in LLM Agents](https://arxiv.org/html/2604.16548v1) | arXiv 2604.16548v1 | Title confirmed: *A Survey on Long-Term Memory Security in LLM Agents: Attacks, Defenses, and Governance Across the Memory Lifecycle* |
| [SCITT architecture](https://datatracker.ietf.org/doc/rfc9943/) | RFC 9943 | Confirmed: *An Architecture for Trustworthy and Transparent Digital Supply Chains*. Published RFC, not a draft |
| [vCon Lifecycle using SCITT](https://datatracker.ietf.org/doc/html/draft-howe-vcon-lifecycle-01) | draft-howe-vcon-lifecycle-01 | Confirmed **individual** Internet-Draft, dated 4 May 2026, expires 5 November 2026. Supports the "May 2026 individual draft, not an IETF standard" characterisation in PRIOR_ART.md |
| [ApertoMemory](https://datatracker.ietf.org/doc/draft-ferro-apertomemory/02/) | draft-ferro-apertomemory-02 | Confirmed: *The ApertoMemory Format: Portable, Client-Side-Encrypted AI Memory* |
| [US10956406B2](https://patents.google.com/patent/US10956406B2/en) | US10956406B2 | Confirmed: *Propagated deletion of database records and derived data* |
| [C2PA 2.4](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html) | Specification 2.4 | Versioned specification URL |

## Version-controlled sources

Pinned to the commit that was current at re-verification. The linked pages track
the default branch and will move.

| Source | Pin | Verified 2026-08-07 |
|---|---|---|
| [Inspeximus](https://github.com/DanceNitra/inspeximus) | `3ba90c47560a53d650b4be47b0146b3a9538dd69` (2026-08-06) | README confirms the keying limitation PRIOR_ART.md relies on: its own benchmark reports 4–8 of 60 non-declarative prose sentences keyed. **This commit post-dates the 2026-08-01 research cutoff** — the repository moved between cutoff and re-verification, which is precisely why this file exists |
| [IAB Data Deletion Request Framework](https://github.com/InteractiveAdvertisingBureau/Data-Subject-Rights/blob/main/Data%20Deletion%20Request%20Framework.md) | `b9418f5394ca91193181a61c567ffbbdff79cdef` (2025-02-06) | Repository unchanged since well before the cutoff |
| [Karpathy LLM Wiki idea file](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) | Gist, revision not pinned | Cited only as a presentation precedent, so drift carries no claim risk |

## Unpinned sources — open risk

These are live product and project sites with **no public archive snapshot** at
the time of writing. They are also the sources that carry the most weight in the
collision matrix. If any of them changes, the corresponding row in
[PRIOR_ART.md](PRIOR_ART.md) becomes unverifiable.

| Source | Snapshot | Verified 2026-08-07 | Claim at risk |
|---|---|---|---|
| [EngramSpec](https://engramspec.org/) | none | Live. Confirms signed envelopes over Ed25519, a `corrections` array, `GET /v1/context`, and the "format specification, not a product" framing | The strongest AI-memory transport collision, PRIOR_ART.md row 1 |
| [Portable AI Memory v1.0](https://portable-ai-memory.org/spec/v1.0/) | none | Live, titled *Specification v1.0* | Lifecycle-status collision |
| [Shomei overview](https://shomei.ai/how-it-works/) | none | Live. Page subtitle confirms "Receipts for Every Memory Event" and offline-verifiable signed receipts for deletion, restriction, and export | Strongest governed-memory product collision |
| [Shomei HTTP API](https://shomei.ai/docs/http-api/) | none | Live | Correction/update and lineage detail |
| [Shomei governance and receipts](https://shomei.ai/docs/governance-and-receipts/) | none | Live | Erasure cascade and pending-external-deletion states |
| [TMLS Agent Memory and State](https://www.tmls.nyc/research/agent-memory-state) | none | Live, titled *Agent Memory and State: Durable, Episodic, Semantic* | Provenance-led invalidation and recomputation |
| [OpenAI Memory FAQ](https://help.openai.com/en/articles/8590148-memory-faq) | none | Reachable; answers 403 to automated clients | The single-product correction-burden example |

**Open action before publication:** request a public archive snapshot of each row
above, then replace `none` with the snapshot URL. This has deliberately not been
done automatically — requesting a snapshot publishes a copy of a third party's
page, which is the author's call, not a tool's.

## Quantitative claims

Every figure quoted in the documentation, and where it comes from.

| Claim in the documentation | Source | Verified 2026-08-07 |
|---|---|---|
| "more than 800 million weekly ChatGPT users by December 2025" | [OpenAI, The state of enterprise AI](https://openai.com/index/the-state-of-enterprise-ai-2025-report/) | Confirmed. Report published 2025-12-08; states more than 800 million weekly active users |
| "practical guidance, information seeking, and writing dominate ordinary use" | [OpenAI / NBER consumer-use study](https://openai.com/index/how-people-are-using-chatgpt/) | Page reachable; answers 403 to automated clients |
| "survey of 6,000 digital workers" | [Glean Work AI Index](https://www.glean.com/work-ai-institute/reports/work-ai-index) | Confirmed verbatim: 6,000 full-time digital workers, US n=3,000, UK n=1,500, AU n=1,500 |
| "77% … multiple AI tools weekly; 33% … four or more" | [Glean Work AI Index](https://www.glean.com/work-ai-institute/reports/work-ai-index) | Confirmed verbatim: "77% of AI users bounce between multiple tools every week"; "33% bounce between four or more". **The denominator is AI users, not all surveyed digital workers** — the documentation was corrected to match |

An archived copy of the Glean report exists at
[web.archive.org, 2026-07-18](http://web.archive.org/web/20260718044841/https://www.glean.com/work-ai-institute/reports/work-ai-index).

## Maintenance

- `make links` re-checks that every cited URL still resolves. It reports a
  network failure as *inconclusive*, never as a pass, and never as evidence that
  a source is gone.
- When a source changes materially, update [PRIOR_ART.md](PRIOR_ART.md) and this
  file together, and record the change in [CHANGELOG.md](CHANGELOG.md). Do not
  quietly re-point a citation at new content that says something different.
- When a source disappears, cite the archive snapshot and say so. If no snapshot
  exists, the correct action is to narrow the affected row, not to keep the
  citation.

## Production-cryptography candidate sources

These sources were read on 2026-08-12 for the internal candidate assessment in
[`docs/CRYPTOGRAPHY_QUALIFICATION.md`](docs/CRYPTOGRAPHY_QUALIFICATION.md).
They are security-maintenance and compatibility evidence, not independent
review of LLM Errata and not evidence that G3 passes.

| Source | Pin or version | Verified 2026-08-12 |
|---|---|---|
| [PyCA Ed25519 API](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/) | live documentation; repository `main` observed at `95c04524ef533d6173e4c61d5781ea34bff0e768` | Raw 32-byte private/public key loading, 64-byte signatures, and one-shot verification are supported |
| [PyCA security policy](https://cryptography.io/en/latest/security/) | live documentation | Most recent release and `main` receive security support; binary releases are refreshed for OpenSSL security updates |
| [PyCA project documentation](https://cryptography.io/en/latest/) | live documentation | Explicitly says project code and documentation have not undergone an external audit |
| [PyCA on PyPI](https://pypi.org/project/cryptography/50.0.0/) | 50.0.0 | Python requirement and Apache-2.0 OR BSD-3-Clause licence expression confirmed |
| [OpenSSL Ed25519](https://docs.openssl.org/3.5/man7/EVP_SIGNATURE-ED25519/) | OpenSSL 3.5 documentation | One-shot RFC 8032 Ed25519 signing and verification plus raw key loading confirmed |
| [libsodium signatures](https://doc.libsodium.org/public-key_cryptography/public-key_signatures) | live documentation; stable branch observed at `701aa826b97dc84a353d70a551d49dc26da539c5` | Seed keypair, detached signature, detached verification, exact single-part Ed25519 algorithm, and key sizes confirmed |
| [libsodium 1.0.22](https://github.com/jedisct1/libsodium/releases/tag/1.0.22-RELEASE) | 1.0.22, 2026-04-09 | Current public point release at assessment time |
| [Libsodium 1.0.12 and 1.0.13 Security Assessment](https://www.privateinternetaccess.com/blog/wp-content/uploads/2017/08/libsodium.pdf) | assessment of 1.0.12 and 1.0.13 | Third-party review included Ed25519 signatures and reported no major vulnerabilities in reviewed versions; it is not a current 1.0.22 audit |
| [CVE-2025-69277](https://nvd.nist.gov/vuln/detail/CVE-2025-69277) | CVE-2025-69277 | Older libsodium revisions had an Ed25519 point-validation flaw; 1.0.22 post-dates the cited fix, without making vulnerability review unnecessary |
