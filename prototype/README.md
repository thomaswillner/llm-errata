# Phase 1: file-backed proof

```bash
make demo
```

Standard library only. No network, no API key, no dependencies, reproducible
from a clean checkout.

The demo exits `2`, on purpose. Both inspectable stores are fully repaired, all
three probes pass, and the aggregate result is still `partial`, because one
required store cannot show its own state. **That refusal is the deliverable.**
A demo where everything passes proves only that the demo was built to pass.

## What it demonstrates

One root, `is vegetarian`, copied into three stores and mixed into a summary
alongside two unrelated preferences. Then one supersession.

| Store | Kind | Behaviour |
|---|---|---|
| `markdown` | exact root-to-artifact lineage | enumerates, quarantines, rebuilds deterministically |
| `vector` | entries with derivation metadata | retrieved by similarity, so quarantine is about retrieval, not keys |
| `prompt_cache` | opaque | acknowledges the erratum, cannot enumerate, always reports `unknown` |

The opaque adapter is the control, not an edge case. Remove it and the same
repair reports `verified` — there is a test that asserts exactly that, so the
non-green result cannot be mistaken for a bug in the aggregation.

## The parts

| Module | Responsibility |
|---|---|
| `errata.py` | The importer-view trust boundary. Rejects forgery, tampering, rollback, sequence gaps, conflicts visible to that importer, unknown targets, and operations that carry the wrong shape. It cannot detect a different signed view delivered only to another importer. |
| `lineage.py` | Exact lineage recorded at import and derivation time, not reconstructed afterwards. Supplies the known derivation closure and the inputs that survive a retirement. |
| `adapters.py` | The three stores, plus the four coverage results. |
| `strategies.py` | How a repair is carried out. One conforming strategy and three that are not, because a conformance suite where nothing can fail has not tested anything. |
| `controller.py` | observe → quarantine → rebuild → test → attest, with a journal that makes the ordering observable. |
| `checkpoints.py` | Canonical, atomically persisted proof binding CLI quarantine to erratum, state, adapters, and gated artifacts. |
| `receipts.py` | Coverage-aware receipts and the aggregation rule. |
| `scenario.py` | The synthetic fixture. |
| `demo.py` | The narrated run. |
| `schema.py` | The dependency-free validator for the published wire schema. |
| `sqlite_store.py` | A real transactional store, with durable quarantine and a residue scan. |
| `residue.py` | Substrate evidence: `verified` requires a clean scan, not an API acknowledgement. |
| `cli.py`, `workspace.py` | The `errata` command line over an on-disk workspace. |

## The eight scenarios

All in `tests/test_controller.py`, one acceptance criterion per test class.

| Scenario | What it proves |
|---|---|
| Correction | The false history is not preserved. `history_retained` is false. |
| Supersession | The old value is retained for its valid interval and the new state activates. |
| Erasure | No positive leg, and the receipt does not repeat the erased value. |
| Mixed-source summary | Rebuilt from the two retained inputs plus the replacement, not deleted and not appended to. |
| Feed rollback | An older erratum after a newer one is refused. |
| Stale reimport | Re-importing the original export is refused, so the next sync does not undo the repair. |
| Unknown store | Aggregate is not `verified` even though every executed probe passed. |
| Interrupted repair | A rebuild that raises leaves affected state quarantined, and the repair resumes from there. |

Two non-conforming repairs are tested as first-class strategies, because they
are the cheap tricks the repair triad exists to defeat:

- **Wipe** — delete the whole profile. The negative probe passes; preservation
  catches it.
- **Append-only** — add the replacement and leave the old value retrievable.
  The positive probe passes; the negative probe catches it.

## The command line

```bash
make cli-demo
```

A full lifecycle without importing Python: `init`, `export`, `derive`,
`publish`, `pull`, `plan`, `quarantine`, `repair`, `test`, `attest`, `audit`,
`verify`.

`quarantine` authenticates exactly the next pending erratum, gates every
enumerable descendant, records each adapter's own quarantine-phase coverage,
records opaque or missing checkpoint evidence as `unknown`, and atomically
writes `checkpoints/<sequence>-<erratum>.json`. Its canonical digest binds the
erratum, target, inspectable pre-state root, adapter inventory, limitations,
gated artifact set, and reported checkpoint coverage. `repair` re-authenticates and refuses missing, mutated,
consumed, wrong-target, state-drifted, adapter-drifted, or ungated evidence.
Consumption happens only after receipt and applied-state writeback, so an
interrupted rebuild retains an unconsumed checkpoint for safe resume.

Enumeration is necessary but not sufficient for verified coverage. An adapter
must also expose `lineage_complete(root) -> True`, backed by a write-time or
audited root-specific lineage authority. Missing or false evidence makes that
required store `unknown`, even when enumeration returns an empty tuple and the
adapter's own coverage method claims `verified`. This is an adapter attestation,
not independent proof against a dishonest store.

Checkpoint coverage and final repair coverage are different observations. The
adapter supplies both through `quarantine_coverage(root)` and `coverage(root)`;
the controller carries the worse result into the signed receipt, so a later
success cannot erase an earlier partial or failed gate. Repair planning also
uses adapter-owned `source_artifact(id)` and `repair_inputs(id)` rather than
requiring independent store records to be copied into the reference ledger.

Exit codes are part of the interface. `0` is success, `1` is a refusal or a
failed check, and **`2` means the repair ran and the result is not verified**.
`2` is not a lesser `1`: it is the case the whole proposal exists to make
expressible, so it is a distinct code rather than a warning on stdout.

### Offline semantic conformance

Semantic probes are separate behavioral evidence, not a change to Phase 1
receipts. Checked-in synthetic fixtures run without a provider, network, or API
key:

```bash
python3 -m prototype.cli semantic-test \
  --probes spec/semantic/probes.json \
  --config spec/semantic/verifier-config.json \
  --observations spec/semantic/observations.json
```

This exact invocation defaults to `verified-correction`. Pass `--case NAME` to
run named cases. The fixtures demonstrate verified correction (`0`), failed
supersession (`1`), and unknown erasure, provider error, missing response,
duplicate response, configuration drift, and structurally parseable
nonconforming output (`2`). Output is one canonical JSON semantic report.
Malformed manifests exit `1` without a traceback; an unexpected structured
verifier record is semantic uncertainty, not an argument-parser error. Fixture
format and privacy constraints are documented in
[spec/README.md](../spec/README.md#offline-semantic-probe-fixtures).

The offline runner consumes `RecordedSemanticVerifier`; production adapters
implement `SemanticVerifier` in `semantic.py`. They may evaluate confidential
inputs ephemerally, but only the structured verdict, binding digest, timestamp,
and response digest may enter an observation. Raw output and erased values are
not persisted.

Running it against a real SQLite store produces the result that matters:

```text
test      negative=pass  positive=pass  preserve=pass
stores    prompt_cache   unknown
          sqlite         failed
aggregate FAILED
```

Every probe passed. The store still reports `failed`, because the residue scan
finds the retired value in `store.sqlite3-wal` after the row is gone and the API
reports it deleted. That is Ghost Vectors, reproduced with nothing but the
standard library.

## What this is not

- **A published wire schema, with limits.** `spec/` carries JSON Schemas for the
  erratum and the receipt plus 19 conformance vectors, so another implementation
  can be checked against the same contract. The bundled validator implements a
  subset and refuses unknown keywords rather than ignoring them. See
  [spec/README.md](../spec/README.md).
- **Real signatures, with one caveat.** `ed25519.py` is Ed25519 per RFC 8032,
  standard library only, checked against the RFC's published test vectors
  including the 1023-byte message. An owner publishes a verification key and no
  holder of it can forge — the property a MAC cannot give and the erratum feed
  requires. It is a reference implementation and **not constant-time**, so a
  deployment with attacker-facing signing keys should link libsodium and
  substitute a `Signer`. No caller changes.
- **Not proof that a repair happened.** The signature says who attested to
  which bytes. A compromised importer can sign an honest-looking receipt over a
  repair it never performed. See [THREAT_MODEL.md](../THREAT_MODEL.md).
- **Not a semantic guarantee.** The probes are behavioural checks over a
  declared scope. They are evidence that the retired proposition did not
  surface in this sample, and nothing more. The embedding is a deterministic
  bag-of-terms, not a model, which keeps the run reproducible and means the
  vector results say nothing about how a real embedding would behave.
- **Not evidence that a real vector store deleted anything.** `VectorAdapter`
  reports `verified` from its own bookkeeping over an in-memory dictionary.
  [Ghost Vectors](https://arxiv.org/abs/2606.18497v1) demonstrates that
  soft-deleted embeddings remain reconstructible from HNSW index files in
  ChromaDB, FAISS and Weaviate after the API reports the record gone. A real
  adapter that trusts a delete response would be honest and wrong. Any
  production adapter needs substrate-level evidence, not an API acknowledgement,
  before it may report `verified`.
- **Not evidence about unregistered copies.** The closure is *known* because
  lineage was written at derivation time. Copies nobody registered are outside
  it, permanently.

## Interpreting a run

`partial` here is the honest answer to a specific question, not a failure of
the implementation. The uncomfortable part is that a real deployment would
report `partial` or `unknown` far more often than this fixture does, because
lineage through an uninstrumented summariser is usually severed.

The argument is not that the receipt will usually be green. It is that a
receipt which says `unknown` is worth more than silence, because it turns an
invisible failure into a visible one.
