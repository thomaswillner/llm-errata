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

## Offline semantic-probe fixtures

The semantic fixtures exercise provider-neutral behavioral evidence without a
network connection, API key, or raw model output. Run one named case with:

```bash
python3 -m prototype.cli semantic-test \
  --probes spec/semantic/probes.json \
  --config spec/semantic/verifier-config.json \
  --observations spec/semantic/observations.json \
  --case verified-correction
```

`probes.json` and `observations.json` are strict objects containing only a
`cases` object. The selected case must exist in both files. A probe case is an
array of strict `SemanticProbe` records. An observation case is an array of
strict `SemanticObservation` records. `verifier-config.json` is one strict
`VerifierConfig` record. Unknown fields, malformed JSON, missing cases, and
invalid record fields are refused rather than interpreted.

The included synthetic cases are `verified-correction`,
`failed-supersession`, and `unknown-erasure`. The command prints one canonical
JSON `SemanticProbeReport` and exits `0` for `verified`, `1` for `failed` or
invalid input, and `2` for `unknown`.

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
