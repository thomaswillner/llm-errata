# Provider-Neutral Semantic Probes Design

**Date:** 2026-08-12

**Status:** Approved as Phase 2 item 6 implementation scope

## Purpose

Add model-assisted behavioral evidence without coupling LLM Errata to one
provider or allowing nondeterministic, unavailable, or ambiguous verification
to become success. Structural checks remain deterministic and separate.

## Architecture

`prototype/semantic.py` defines four stable units:

1. `SemanticProbe` describes one negative, positive, or preservation question,
   its declared scope, operation, and whether it is required.
2. `VerifierConfig` records provider, model, prompt-template version, sampling
   parameters, and an optional seed. Its canonical digest binds observations to
   the exact verifier configuration.
3. `SemanticVerifier` is a protocol whose only operation evaluates one probe and
   returns a structured observation. Provider SDKs remain outside the core.
4. `SemanticProbeRunner` validates observations and produces a coverage-aware
   report. A deterministic `RecordedSemanticVerifier` consumes checked-in
   synthetic fixtures for tests and offline conformance.

The runner never interprets free-form prose as success. A verifier observation
must declare `pass`, `fail`, `inconclusive`, or `error`, bind the probe ID and
configuration digest, carry a timestamp, and include a SHA-256 digest of its raw
response. Raw provider output is not included in receipts.

## Aggregation

- all required observations valid and `pass` -> `verified`;
- any valid required `fail` -> `failed`;
- otherwise -> `unknown`.

`inconclusive`, `error`, missing observations, duplicates, unexpected probe IDs,
configuration drift, malformed timestamps, or invalid digests all yield
`unknown` with explicit limitations. Optional probes never compensate for a
missing required probe.

## Erasure boundary

Erasure evidence must not reproduce erased content. An erasure probe record may
contain opaque commitments, synthetic labels, and a content-free prompt
template, but not the retired value. Runtime provider adapters may receive
ephemeral confidential inputs through provider-owned mechanisms; those inputs
are excluded from the persisted probe, observation, report, and receipt.

The deterministic fixtures use synthetic propositions and still assert that the
serialized report contains no retired erasure value.

## CLI and fixtures

`errata semantic-test` accepts a probe manifest, verifier configuration, and
recorded-observation manifest. It prints the canonical report and exits:

- `0` for `verified`;
- `1` for `failed`;
- `2` for `unknown`.

Checked-in fixtures cover:

- correction with all required probes passing;
- supersession with a failing negative probe;
- erasure with content-free records;
- inconclusive observation;
- provider error;
- missing response;
- duplicate response;
- configuration drift; and
- deliberately nonconforming verifier output.

## Integration boundary

This milestone publishes semantic evidence as a separate report and CLI command.
It does not silently change existing Phase 1 receipt semantics. A later reviewed
profile may embed or reference the semantic report from a receipt after external
conformance review settles binding and privacy questions.

## Tests and evidence

Unit tests must prove aggregation, binding, parser failure behavior, erasure
non-disclosure, deterministic serialization, and CLI exit codes. `make check`
must continue to run without network access or API keys.

Implementation completes Phase 2 item 6 internally. G2 remains `BLOCKED` until
an independent reviewer evaluates the schemas, vectors, CLI, adapters,
cryptographic boundaries, and semantic-probe layer as one conformance surface.

