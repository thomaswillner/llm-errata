# External readiness evidence schemas

This document defines the exact machine-admitted G3, G4, and G5 evidence
records. Every record is public, dated, independently produced, bound to one
immutable commit and canonical surface digest, and conflict-disclosed. A valid
`fail` report remains evidence but cannot make a gate pass.

Shared fields are `kind=external`, a public report `ref`, non-empty `producer`,
public `producer_identity`, ISO `observed` date, exact `reviewed_commit`, exact
`surface_digest`, `conflicts` array, gate-specific `review_type`, relationship,
and independence attestation. Extra or malformed fields fail closed.
`result` is exactly `pass`, `pass-with-findings`, or `fail`. Structural
admission preserves a complete negative report; gate qualification separately
requires the passing values described below.

## G3 cryptography record

G3 uses attestation `llm-errata-independent-cryptography-review-v1`. Scope must
contain exactly: `library-build`, `constant-time`, `malformed-input-refusal`,
`key-rotation`, `key-recovery`, `revocation`, and `delegation`.

`implementation` contains exactly `library`, `version`, `binding`,
`build_digest` (`sha256:` plus 64 lowercase hexadecimal characters), non-empty
`platforms`, `constant_time`, and `audited_build`. Qualification requires both
booleans to be true and result `pass` or `pass-with-findings`.

## G4 adapter and validator records

G4 uses attestation `llm-errata-independent-implementation-v1`, review type
`g4-conformance`, and one shared `erratum_id`.

Each adapter record has `evidence_role=adapter`, relationship
`independent-implementation`, a unique `implementation_id`, and one `receipt`
containing exact `receipt_id`, `receipt_digest` (`sha256:` plus 64 lowercase
hexadecimal characters), and public `evidence_ref`.

The separately produced validator record has `evidence_role=validator`,
relationship `independent-third-party-validator`, its own implementation and
producer identity, and `validated_receipts`. Every result names the adapter
`implementation_id`, exact receipt ID and digest, result, and public evidence
reference. G4 qualifies only when one validator reports passing results for
the exact receipts from two different adapter producers against the same
erratum, commit, and surface digest. An unrelated validator report cannot be
combined with the adapters. Structurally complete adapter, validator, and
per-receipt `fail` results remain admissible evidence but do not qualify G4.

## G5 interoperability record

G5 uses attestation `llm-errata-independent-interoperability-review-v1`, review
type `phase3-interoperability`, relationship `independent-experiment-report`,
`synthetic_data=true`, `user_controlled_root=true`, and one non-empty `root_id`.

Exactly three independently operated systems are required, with different
operator identities. Every system names version and evidence, completes
`correction`, `supersession`, and `erasure`, and records all nine metrics:

- observation-to-quarantine time;
- known-descendant coverage;
- stale-behavior rate;
- replacement activation;
- collateral retention;
- stale-reimport resistance;
- opaque coverage;
- operator effort; and
- user-visible friction.

Every operation and measurement has its own public evidence reference. The
three-system set must include at least one intentionally nonconforming importer,
one `incomplete` or `opaque` coverage system, and one mixed-artifact-lineage
system. A structurally complete failed report may record a failed system,
`independently_operated=false`, or `completed=false`. Qualification requires a
passing report, synthetic data, a user-controlled root, three independently
operated passing systems, every operation completed, and all three required
experiment arms. Three generic passing system summaries are insufficient.

These schemas establish structural admission only. Maintainer review still
must verify real identities, authorship, conflicts, authorization, raw evidence,
and whether the claimed measurements support the report.
