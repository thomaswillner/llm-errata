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
| `errata.py` | The trust boundary. Rejects forgery, tampering, rollback, sequence gaps, equivocation, unknown targets, and operations that carry the wrong shape. |
| `lineage.py` | Exact lineage recorded at import and derivation time, not reconstructed afterwards. Supplies the known derivation closure and the inputs that survive a retirement. |
| `adapters.py` | The three stores, plus the four coverage results. |
| `strategies.py` | How a repair is carried out. One conforming strategy and three that are not, because a conformance suite where nothing can fail has not tested anything. |
| `controller.py` | observe → quarantine → rebuild → test → attest, with a journal that makes the ordering observable. |
| `receipts.py` | Coverage-aware receipts and the aggregation rule. |
| `scenario.py` | The synthetic fixture. |
| `demo.py` | The narrated run. |

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

## What this is not

- **Not a wire protocol.** No schema is published yet. That is Phase 2.
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
