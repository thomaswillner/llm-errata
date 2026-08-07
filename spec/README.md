# The LLM Errata wire schema

Two JSON Schemas and a set of conformance vectors, so an implementation other
than this one can be built and checked against the same contract.

| File | What it is |
|---|---|
| `erratum.schema.json` | The signed preimage of an erratum. The signature travels alongside and is not part of what it covers. |
| `receipt.schema.json` | What an importer returns after acting on one. |
| `vectors/manifest.json` | Every vector, which schema it belongs to, whether it must validate, and — for an invalid vector — the text that must appear in the rejection. |
| `vendor/json-schema-test-suite/` | Cases from the official JSON-Schema-Test-Suite, vendored unmodified. |

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
