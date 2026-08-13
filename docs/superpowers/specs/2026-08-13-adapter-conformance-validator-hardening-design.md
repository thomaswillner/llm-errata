# Adapter Conformance and Validator Hardening Design

**Date:** 2026-08-13
**Owner:** Thomas Willner
**Status:** Approved for implementation
**Target release:** 0.4.0

## Purpose

LLM Errata currently exercises its wire contract, controller, semantic
aggregator, and receipt binding more deeply than it exercises independently
authored store adapters. Rastislav Drahos reported that an external runner
could reproduce 28 of 28 published cases while only one case reached any store
adapter. He then published candidate adapter cases and validator anti-vacuity
requirements at immutable commit
`DanceNitra/agora@2ba1e299b3483b9038d03387345702427608b90b`.

This change adopts the verified behavioral findings without copying or
vendoring the contributed runner. It adds an independently authored,
provider-neutral adapter-conformance corpus and a fail-closed validator whose
own controls must demonstrably fail against flattering implementations.

Release 0.4.0 remains an experimental conformance proposal and tested
reference implementation. It does not change the project verdict from
`NOT_PROD_READY`, and it does not satisfy G2 or G4.

## Ownership, licence, and provenance

- LLM Errata, its repository, specification, project name, and files authored
  in this repository remain owned and governed by Thomas Willner.
- Repository publication and versioned releases do not transfer copyright.
- Rastislav Drahos and DanceNitra retain copyright in their candidate fixture.
  Its MIT licence permits reuse but does not assign ownership.
- This repository will not copy or vendor that runner or its fixture files.
  Implementation is independently authored from the accepted behavioral
  requirements and the LLM Errata normative contract.
- Documentation must credit Rastislav Drahos and DanceNitra for the reported
  adapter-coverage gap, duplicate-preservation counterexample, candidate cases,
  and anti-vacuity findings. It must identify the immutable source commit,
  MIT licence, interested-party conflict, and disclosed Claude Opus 5
  co-authorship.
- Existing LLM Errata licence terms remain unchanged. Any product or
  commercial implementation remains subject to repository terms, including
  accessible credit to LLM Errata and Thomas Willner and any required written
  grant. Technical adoption, contributor credit, or release publication does
  not imply endorsement, partnership, certification, or commercial permission.

## Normative preservation rule

Preservation is strengthened from boolean recallability to bounded
multiplicity preservation.

Within a declared, inspectable adapter scope, repair must not increase the
active multiplicity of a preserved proposition unless the erratum explicitly
requires an additional assertion. A proposition is identified by the
adapter-provided stable proposition identity used by its conformance
observation interface, not by lossy text normalization or embedding
similarity.

The conformance observation for each active proposition contains:

- a stable, provider-local proposition identifier;
- a content-free or synthetic fixture label suitable for comparison; and
- an active assertion count.

Adapters unable to expose proposition identity or active multiplicity cannot
pass the cardinality case. They report `unknown` for that observation. This
rule is scoped evidence: it does not claim semantic uniqueness outside the
declared adapter surface.

## Corpus format

`spec/adapter-conformance.json` is a versioned, provider-neutral corpus. Each
case contains:

- stable case ID and operation;
- synthetic initial state;
- complete expected checkpoint, aggregate, triad, receipt, and store
  observations;
- required adapter method calls;
- a pinned normative source path and exact quotation;
- one named mutation and the complete result that mutation must produce; and
- provenance and evidence-boundary fields.

Partial expected outcomes are forbidden. A case fails when any extra triad
failure, worse aggregate result, missing store observation, unexpected
exception, or unspecified result appears.

Initial behavioral cases cover:

1. undeclared derivatives cannot become `verified`;
2. complete lineage can reach `verified`;
3. a rebuild cannot increase preserved-proposition multiplicity;
4. erasure evidence is content-free and non-vacuous; and
5. collateral survives supersession while the complete repair still passes.

## Validator architecture

`prototype/conformance.py` owns parsing, source binding, execution, and
result comparison. It exposes one public entry point:

`validate_adapter_conformance(corpus_path, source_root, binding_factory) -> ConformanceReport`.

The validator is standard-library only.

### Source identity

The corpus binds:

- exact LLM Errata Git commit;
- canonical conformance-surface digest;
- fixture schema version; and
- every normative source path and exact quotation.

Validation refuses a dirty or different source tree, a commit mismatch, a
digest mismatch, a missing source, or quotation drift. Source mismatch is an
invalid run, never a case failure or pass.

### Target-instance tracing

Required calls are observed through a proxy around the exact adapter instance
given to the controller. The proxy records protocol member access and calls.
Global frame names, unrelated modules, helper functions, and another object
with the same method name cannot satisfy a positive control.

### Mutation controls

Every case runs twice:

1. honest binding;
2. the declared flattering mutation installed through the public adapter or
   validator seam.

The mutation must complete and produce the exact declared counter-result.
Any unexpected exception, missing result, different failure, or unchanged pass
fails the control. Exceptions count only when the corpus explicitly declares
that exact exception type and message as the required outcome.

### Validator anti-vacuity controls

Three executable meta-tests attack the validator:

- an empty receipt cannot satisfy confidentiality;
- no-op feed verification cannot satisfy accept-side feed cases; and
- a constant-`unknown` aggregator cannot satisfy the semantic corpus.

These are validator requirements, not adapter scores. A release cannot claim
validator readiness unless all three mutations are rejected for their
specified semantic reason.

## Reference binding

The LLM Errata reference binding uses only public adapter/controller
interfaces plus a conformance observation seam. Production adapters are not
required to expose raw private store contents. A binding may expose only
synthetic fixture identities and counts for an isolated conformance run.

The corpus and validator must run against the repository reference adapter.
Passing the reference binding demonstrates harness behavior, not independent
interoperability.

## CLI and evidence

The existing CLI gains an `adapter-conformance` command accepting:

- corpus path;
- source root; and
- an importable binding factory.

Output is one canonical JSON report with source identity, per-case results,
positive controls, mutation controls, anti-vacuity results, provenance, and an
explicit statement that the report is not G2 or G4 evidence.

Exit codes:

- `0`: corpus valid and every case/control passes;
- `1`: one or more behavioral or mutation controls fail;
- `2`: source, corpus, binding, or execution evidence is invalid or
  inconclusive.

## Release integration

Version 0.4.0 includes the current `agent/g2-publication` surface plus this
validator hardening. The release:

- updates `VERSION`, `CITATION.cff`, README maturity text, supported
  security version, readiness ledger/matrix, and changelog;
- records contributor provenance and the independently authored implementation
  boundary;
- keeps every G2 through G6 status unchanged unless its existing evidence
  contract independently passes;
- backfills the missing GitHub release object for immutable tag `v0.3.0`
  without moving that tag; and
- creates immutable tag and GitHub release `v0.4.0` only after exact-head
  local checks and GitHub CI pass.

## Verification seams

TDD is performed at these public seams:

1. corpus validation through `validate_adapter_conformance`;
2. target adapter calls through the tracing proxy;
3. exact mutation-result comparison;
4. executable validator anti-vacuity suite;
5. CLI canonical report and exit codes;
6. repository version/readiness/publication validation; and
7. release metadata consistency.

Required final checks:

- focused conformance and CLI tests;
- `make check`;
- `make publication`;
- `make links` when source citations change;
- two-axis standards/spec review against this design;
- exact-head CI on Python 3.11 and 3.13;
- immutable tag and GitHub release verification; and
- repository-wide GitHub freshness receipt after the last mutation.

## Safe stop

Stop without releasing when any of these occurs:

- the normative cardinality rule cannot be expressed without provider-specific
  private data;
- the validator cannot distinguish its own flattering mutations;
- source identity cannot be bound mechanically;
- current branch integration drops or rewrites existing evidence;
- local or exact-head CI fails;
- a new actionable contributor comment or review changes the required design;
  or
- version, tag, release, licence, attribution, or readiness metadata disagree.
