# Independent review request

LLM Errata is seeking independent technical review of an experimental
conformance proposal for repairing derived AI memory after a post-export
correction, supersession, or erasure.

Repository: https://github.com/thomaswillner/llm-errata

Current verdict: **NOT_PROD_READY**.

## Reviews requested

### Novelty and conformance review

Challenge the narrow conjunction in `RESEARCH.md` and `PRIOR_ART.md`. Identify
any earlier public implementation or normative profile that requires all of:

1. post-export update delivery to prior importers;
2. importer-side quarantine and repair of known local descendants;
3. negative, positive, and preservation verification; and
4. an authenticated, coverage-truthful callback bound to the event and importer state: D1 verifies signer and byte binding; D2 checks that signed stores, aggregate, and limitations truthfully represent the declared required scope.

Partial collisions are valuable and should narrow the proposal.

### Security and distributed-systems review

Review authorization, sequencing, rollback, equivocation, quarantine ordering,
lineage gaps, opaque coverage, receipt binding, erasure confidentiality, key
lifecycle, retries, and incomplete stores. Find the smallest counterexample that
breaks an invariant or makes the contract impractical.

## Required review record

Please identify:

- your name or stable public identity;
- reviewed commit SHA and date;
- files and behavior reviewed;
- prior work or standards relied upon;
- blocking, major, and minor findings;
- conflicts of interest or prior involvement; and
- verdict: proceed, narrow, redesign, or retire.

## G2 ledger schema

A review can qualify G2 only when its public external report is represented in
the readiness ledger with all fields below. A `fail` result is recorded as
evidence but cannot make G2 pass.

```json
{
  "kind": "external",
  "ref": "https://reviewer.example/report",
  "producer": "Independent reviewer identity",
  "observed": "YYYY-MM-DD",
  "review_type": "phase2-conformance",
  "reviewed_commit": "40 lowercase hexadecimal characters",
  "scope": [
    "schemas", "vectors", "cli", "adapter-interface",
    "transactional-store", "substrate-evidence", "semantic-probes",
    "security-boundaries"
  ],
  "result": "pass | pass-with-findings | fail",
  "relationship": "independent-third-party",
  "conflicts": [],
  "producer_identity": "https://identity.example/reviewer",
  "independence_attestation": "llm-errata-independent-review-v1",
  "surface_digest": "SHA-256 of canonical Phase 2 surface"
}
```

`ref` must be a public `https` URL with host and path, or a well-formed
`urn:<nid>:<nss>`. `producer_identity` must be an `https` URL with host and
path. `observed` cannot be future-dated. `conflicts` is always an array,
including when empty. Scope must contain each token exactly once. A qualifying
pass requires `pass` or `pass-with-findings` plus every listed scope token.

`surface_digest` is SHA-256 over sorted canonical paths. For every path, append
its UTF-8 repository-relative path, one NUL byte, raw bytes, then one final NUL
byte. Canonical path enumeration is:

```text
all first-party prototype/*.py
prototype/README.md
spec/README.md
all first-party spec/*.schema.json
all first-party spec/vectors/*.json
all first-party spec/semantic/*.json
ROADMAP.md
THREAT_MODEL.md
SECURITY.md
tests/test_adapters.py
tests/test_cli.py
tests/test_controller.py
tests/test_ed25519.py
tests/test_errata_feed.py
tests/test_schema.py
tests/test_semantic.py
tests/test_sqlite_store.py
```

Vendor files under `spec/vendor/` are excluded. All named groups must be
nonempty. Use `python3 -c 'from scripts.check_readiness import
g2_surface_digest; print(g2_surface_digest())'` from repository root to print
current digest.

The checker requires live Git metadata, verifies `reviewed_commit` is a commit,
reads each canonical file at that commit with `git show`, and requires supplied
digest to match both commit and current worktree. It validates schema, claimed
relationship, and report identity. It cannot prove reviewer independence or
complete conflict disclosure; a human must verify those claims before changing
readiness verdict.

Open a GitHub issue for public findings. Security-sensitive findings must follow
`SECURITY.md`. Review invitations and automated reviews are not independent
evidence for the production-readiness ledger.
