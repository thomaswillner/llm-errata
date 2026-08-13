# The LLM Errata wire schema

Two JSON Schemas and a set of conformance vectors, so an implementation other
than this one can be built and checked against the same contract.

| File | What it is |
|---|---|
| `erratum.schema.json` | The signed preimage of an erratum. The signature travels alongside and is not part of what it covers. |
| `receipt.schema.json` | What an importer returns after acting on one. |
| `vectors/manifest.json` | Every vector, which schema it belongs to, whether it must validate, and — for an invalid vector — the text that must appear in the rejection. |
| `vendor/json-schema-test-suite/` | Cases from the official JSON-Schema-Test-Suite, vendored unmodified. |
| `semantic/probes.json` | Named, strict semantic-probe sets for offline conformance. |
| `semantic/verifier-config.json` | Exact synthetic verifier configuration, whose canonical digest binds every observation. |
| `semantic/observations.json` | Named recorded-observation sets for the matching probe cases. |
| `vectors/protocol-manifest.json` | Executable key-rotation, concurrency, invalid-target, and confidentiality cases that JSON Schema cannot express. |
| `vectors/receipt-binding-mutations.json` | Valid-domain mutations proving every signed receipt field is bound. |
| `adapter-conformance.json` | Five provider-neutral adapter cases and three executable validator anti-vacuity controls. |

## Adapter conformance

`adapter-conformance.json` adds the store-facing half of conformance. Every
case binds an immutable normative source and exact quotation, declares the
complete expected checkpoint, aggregate, triad, store, and receipt outcome,
requires calls through the exact adapter instance, and names one flattering
mutation with its exact counter-result. An exception is not evidence that a
mutation was caught.

Preservation includes bounded proposition multiplicity. Within an inspectable
synthetic conformance scope, an adapter supplies stable provider-local
proposition identities and active assertion counts. Repair must not increase
the count of a preserved proposition unless the erratum requires another
assertion. Text normalization and embedding similarity are not proposition
identity. An adapter unable to expose identity/count for the isolated fixture
reports that observation as `unknown`; it cannot receive a cardinality pass.

Run:

```bash
python3 -m prototype.cli adapter-conformance \
  --corpus spec/adapter-conformance.json \
  --source-root .
```

For an independently implemented binding in another checkout, add
`--binding module:factory --binding-root /path/to/its/clean/git/checkout`.
Reports bind the LLM Errata runtime commit/tree, exact corpus SHA-256, and the
binding repository commit/tree plus tracked source path and SHA-256 separately.
Binding-package modules are loaded from admitted tracked bytes rather than any
preloaded module cache, and the report binds their dependency-manifest digest.

Exit `0` means the supplied binding and validator controls passed this
internal corpus. Exit `1` means a behavioral or mutation control failed. Exit
`2` means source, corpus, binding, or execution evidence is invalid or
inconclusive. No result is G2 or G4 evidence by itself.

Rastislav Drahos/DanceNitra reported the adapter-coverage gap,
duplicate-preservation counterexample, candidate behaviors, and anti-vacuity
attacks in the MIT-licensed artifact at
`DanceNitra/agora@2ba1e299b3483b9038d03387345702427608b90b`. Inspeximus is a
G4 candidate, so this is interested-party input. The LLM Errata corpus and
validator are independently authored; the external runner and fixtures are
not copied or vendored.

Receipt conformance evaluates two independent properties. D1 authenticity
verifies the importer and every signable byte. D2 coverage truthfulness checks
that signed stores, aggregate, and limitations match the declared required
scope. A correctly signed receipt that overstates coverage passes D1 and fails
D2; signature validity never upgrades missing or opaque evidence.

The reference adapter contract treats an empty enumeration without explicit
root-specific lineage-completeness evidence as `unknown`. Receipts also carry a
signed limitation that importer-local sequencing cannot establish global owner
non-equivocation across split views. The wire coverage vocabulary remains the
four terminal results `verified`, `partial`, `unknown`, and `failed`.

The importer-local checkpoint uses the same terminal vocabulary but measures a
different phase: whether the known affected set is durably gated before repair.
It records adapter-supplied quarantine coverage, and the final signed receipt
cannot improve past a worse checkpoint result. Final `coverage(root)` measures
post-repair dispositions and substrate evidence.

## Offline semantic-probe fixtures

The semantic fixtures exercise provider-neutral behavioral evidence without a
network connection, API key, or raw model output. The approved invocation runs
the default `verified-correction` case:

```bash
python3 -m prototype.cli semantic-test \
  --probes spec/semantic/probes.json \
  --config spec/semantic/verifier-config.json \
  --observations spec/semantic/observations.json
```

`probes.json` and `observations.json` are strict objects containing only a
`cases` object. `--case NAME` selects a non-default case; selected cases must
exist in both files. A probe case is an
array of strict `SemanticProbe` records. An observation case is an array of
strict `SemanticObservation` records. `verifier-config.json` is one strict
`VerifierConfig` record. Unknown fields, malformed JSON, missing cases, and
invalid record fields are refused rather than interpreted.

The included synthetic cases are `verified-correction`,
`failed-supersession`, `unknown-erasure`, `provider-error`,
`missing-response`, `duplicate-response`, `configuration-drift`, and
`nonconforming-output`. The latter five prove coverage refuses provider error,
missing evidence, duplicate evidence, binding drift, and a structurally
parseable operation mismatch. They are semantic `unknown` outcomes, unlike
malformed manifest shape, which is invalid CLI input. The command prints one
canonical JSON `SemanticProbeReport` and exits `0` for `verified`, `1` for
`failed` or invalid input, and `2` for `unknown`.

Erasure fixtures carry only fixed content-free protocol labels, timestamps,
verdicts, and digests. They never contain a retired value or raw provider
response. A live provider adapter belongs at the `SemanticVerifier` seam in
`prototype/semantic.py`; its confidential prompts and raw output must remain
outside persisted manifests and reports.

## Running the vectors

```bash
make check
```

A vector is not satisfied merely by being rejected. `tests/test_schema.py`
requires each invalid vector to be rejected **for the stated reason**, and
requires the invalid set to trip at least four distinct rules, so the suite
cannot be one rule wearing many hats.

Stateful vectors are executed, not parsed as schema instances. The feed cases
construct synthetic signed events and key schedules, then require the exact
accept/refuse behavior. Confidentiality case requires forbidden erased content
to remain absent from serialized receipt evidence. Receipt-binding mutations
rebuild a receipt with one field changed while retaining original signature;
verification must fail for every signable field.

The Phase 2 CLI adds a local checkpoint evidence object implemented in
`prototype/checkpoints.py`. It is not a third wire schema yet: independent
review must settle whether checkpoints are importer-local evidence or a
portable conformance artifact. Its canonical JSON and SHA-256 binding are
nevertheless tested so missing, mutated, consumed, replayed, or drifted local
evidence cannot authorize repair.

## What the bundled validator supports

`prototype/schema.py` implements a subset, because the repository installs
nothing and `jsonschema` is therefore unavailable. The subset is
`SUPPORTED_KEYWORDS` in that module, and **anything outside it raises rather
than being ignored**. A validator that skips a keyword it does not implement
accepts instances the published schema rejects, which is worse than no
validator: implementers would build against a contract nobody enforces.

Known limitations, stated rather than discovered later:

- **Regular expressions.** JSON Schema specifies ECMA-262. Python's `re` is not
  ECMA-262 — Unicode property escapes such as the `\p{...}` class do not
  compile. A pattern that Python cannot compile raises, rather than being
  treated as a non-match, because a check that could not run must never look
  like a check that passed.
- **`$ref`** resolves local pointers only. Remote references raise.
- **Vocabularies, annotations, and dynamic references** are not implemented at
  all.

## Why the official suite is vendored

The same author wrote these schemas and that validator. A matching pair of
mistakes would cancel out and every test would still pass. The vendored suite
was written by neither, and it found four real bugs on first run: `enum` and
`const` treating `False` as equal to `0`, `$ref` dropping its sibling keywords,
`1.0` not being accepted as an integer, and uncompilable patterns crashing
instead of refusing.

Cases whose schema uses an unimplemented keyword are skipped and counted, and
the test asserts that fewer cases are skipped than run — so "skip everything"
is not a way to pass.
