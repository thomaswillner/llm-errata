# Phase 3 system nominations

LLM Errata is seeking nominations for three independently operated AI-memory
systems for a synthetic-data interoperability experiment.

Repository: https://github.com/thomaswillner/llm-errata

Current verdict: **NOT_PROD_READY**. The experiment has not started.

## Required experiment shape

One synthetic memory root must receive a correction, supersession, and erasure
across three independently operated systems. The set must include:

- one intentionally nonconforming importer;
- one system whose coverage is genuinely incomplete or opaque; and
- at least one system capable of recording derivation across mixed artifacts.

Measurements include observation-to-quarantine time, known-descendant coverage,
stale-behavior rate, replacement activation, collateral retention, stale-reimport
resistance, opaque coverage, operator effort, and user-visible friction.

## Nomination requirements

Please name:

- system, operator, public documentation, and version;
- memory stores and derivation surfaces exposed;
- API, account, cost, and data-residency requirements;
- deletion, correction, export, and audit capabilities;
- known opaque stores or unsupported coverage; and
- whether the operator can authorize a synthetic experiment and publish results.

Nomination is not approval. Every system, account, integration, cost, and
interaction requires explicit owner authorization before the experiment begins.
