# Specification Implementation and Attribution Design

**Date:** 2026-08-12

**Status:** Approved design; licence implementation requires owner review of
this written specification before execution.

## Decision

Adopt a dual-boundary licence for version 0.3.0 and later:

1. grant an irrevocable, worldwide, royalty-free, non-exclusive right to
   implement the LLM Errata specification in commercial and non-commercial
   products and services; and
2. retain the current personal-use restrictions for the repository's reference
   implementation and other source code unless a separate licence applies.

Every product or service that implements the specification must attribute
**LLM Errata** and **Thomas Willner**, regardless of whether the use is
commercial or non-commercial.

This design does not change the irrevocable Apache-2.0 rights already granted
for version 0.2.0 and earlier.

## Licensed boundary

The implementation grant covers the normative specification and conformance
materials needed to build an interoperable implementation:

- `spec/`, excluding third-party material under `spec/vendor/`;
- the normative protocol requirements incorporated by reference from
  `README.md`, `IDEA.md`, `ROADMAP.md`, `SECURITY.md`, and `THREAT_MODEL.md`;
- published schemas, canonical examples, and conformance vectors; and
- the right to create, use, modify, distribute, host, and commercialize an
  independent implementation of those requirements.

The grant does not permit copying or distributing repository implementation
code unless another licence or written permission allows it. In particular,
`prototype/`, `scripts/`, and `tests/` remain under the personal-use source-code
licence. Implementers may run published conformance tests for evaluation where
the licence expressly permits it, but must independently author product code.

Third-party files remain governed only by their own licences. Nothing in this
design relicenses them.

## Attribution requirement

Every commercial or non-commercial product or service implementing any
material part of the specification must provide this credit, or a
substantially equivalent credit preserving all three elements:

> Implements the LLM Errata specification by Thomas Willner —
> https://github.com/thomaswillner/llm-errata

The attribution must be reasonably accessible to users or recipients in at
least one ordinary product location, such as:

- an About or Legal screen;
- product or API documentation;
- acknowledgements or third-party notices; or
- a distributed `NOTICE` file.

A source-code comment that is not ordinarily accessible to product users or
recipients does not satisfy the requirement. The licence does not require a
logo, home-screen badge, advertising statement, or fixed visual placement.

The attribution must not imply that Thomas Willner endorses, sponsors,
certifies, audits, or accepts responsibility for an implementation. Conformance
claims remain subject to the repository's evidence requirements.

## Grant properties and retained rights

The specification implementation grant is:

- irrevocable for specification versions released under it;
- worldwide, royalty-free, and non-exclusive;
- sublicensable only as needed to distribute, license, sell, or operate an
  implementation, provided downstream recipients remain subject to the
  attribution, notice-preservation, and no-false-endorsement conditions;
- available for commercial, governmental, academic, standards, research, and
  personal use; and
- conditioned on attribution, preservation of notices, no false endorsement,
  and compliance with third-party rights.

The grant provides no trademark rights beyond nominative use needed for the
required attribution. It provides no patent licence unless the final licence
text explicitly says otherwise. No party receives certification status merely
by implementing the specification.

The copyright holder retains all rights in reference source code not expressly
granted here and may offer separate commercial, source-code, certification, or
support terms.

## Repository changes

Implementation will update these surfaces together:

- `LICENSE`: add the irrevocable specification implementation grant, exact
  attribution condition, path boundary, no-endorsement rule, retained
  source-code restrictions, warranty disclaimer, and historical Apache grant;
- `README.md`: state the dual boundary without calling the source code open
  source;
- `NOTICE`: provide canonical attribution wording and historical licence note;
- `IMPLEMENTATION_CALL.md` and `INDEPENDENT_IMPLEMENTATION.md`: remove the
  per-implementer permission gate for clean-room specification implementations
  and require the canonical attribution;
- `CONTRIBUTING.md` and `SECURITY.md` where licence or support wording is
  affected;
- `SOURCES.md` only if new external legal or licensing references are added;
- repository validators and focused negative tests so licence drift fails; and
- the publication log and GitHub maintainer reply after the final commit and
  validation target exist.

## Protocol feedback incorporated in the same change set

The maintainer feedback also identified two documentation defects independent
of licensing:

1. normative requirement 4 combines two separate properties; documentation
   will distinguish signature authenticity from coverage truthfulness while
   preserving the four-part conjunction; and
2. cryptography qualification understates refusal-path evidence; it will lead
   with malformed-length, non-canonical-scalar, tampered-message,
   tampered-signature, and wrong-key refusal before compatibility vectors.

These clarifications change the canonical Phase 2 surface. Implementation must
compute and publish a new frozen G2 commit and digest. The previous target
remains a historical checkpoint, not the current review target.

## Validation and publication

Before publication:

1. add focused tests that fail on missing implementation rights, missing
   commercial/non-commercial attribution, a source-code relicensing overreach,
   or language implying endorsement;
2. run `make check` and `make cli-demo`;
3. run `make links` only if citations change, reporting network failures
   separately from deterministic checks;
4. recompute the canonical G2 surface digest from the checkout and committed
   target;
5. commit and push only the reviewed repository delta;
6. require exact-head Python 3.11 and 3.13 CI; and
7. reply to the maintainer in natural language with accepted recommendations,
   retained boundaries, exact commit and digest, and the continuing conflict
   disclosure.

The repository remains `NOT_PROD_READY`. A licence grant, attribution, public
reply, or interested-party review does not satisfy G2 or any other external
readiness gate.

## Risks and mitigations

- **Legal ambiguity:** this is an engineering licence design, not legal advice.
  Use plain definitions, explicit path boundaries, and professional legal
  review before relying on it for material commercial enforcement.
- **Accidental source-code relicensing:** tests and documentation must keep
  independent specification implementation separate from copying `prototype/`.
- **Downstream attribution loss:** product distribution and service-operation
  rights must carry the attribution and no-endorsement conditions to recipients
  and operators without extending to unrelated reference code.
- **Attribution burden:** allow several ordinary product locations; do not
  require prominent UI branding.
- **False endorsement:** require attribution but explicitly prohibit language
  suggesting certification or approval.
- **Review-target drift:** publish one new exact commit and G2 digest after all
  normative changes are committed.
