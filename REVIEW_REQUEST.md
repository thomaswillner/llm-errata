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
4. a signed, coverage-aware callback bound to the event and importer state.

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
  "conflicts": []
}
```

`ref` must be a public `https` URL with host and path, or a well-formed
`urn:<nid>:<nss>`. `observed` cannot be future-dated. `conflicts` is always an
array, including when empty. A qualifying pass requires `pass` or
`pass-with-findings` plus every listed scope token.

Open a GitHub issue for public findings. Security-sensitive findings must follow
`SECURITY.md`. Review invitations and automated reviews are not independent
evidence for the production-readiness ledger.
