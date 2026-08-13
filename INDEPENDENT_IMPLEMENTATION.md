# Call for independent implementations

LLM Errata needs independently authored adapters and a separately produced
validator before it can claim interoperability.

Repository: https://github.com/thomaswillner/llm-errata

Current verdict: **NOT_PROD_READY**.

## Requested work

Implement one adapter from the published schemas, vectors, and conformance
requirements without copying implementation code from `prototype/`.

Candidate substrates include:

- file-backed Markdown or knowledge-base memory;
- vector memory;
- graph memory;
- an agent framework's durable memory store; and
- an intentionally opaque or incomplete importer.

The implementation must preserve correction, supersession, and erasure as
different operations; quarantine affected state before repair; run negative,
positive, and preservation checks; and report `partial`, `unknown`, or `failed`
without converting missing evidence into success.

An adapter must state how it establishes root-specific lineage completeness.
Returning an empty artifact list is not enough. If the implementation cannot
show that its enumeration authority was complete for the root, it must report
`unknown` and bind the limitation into its receipt.

## Complete adapter contract

The controller calls the following surface; implementing only enumeration and
coverage is insufficient:

| Method | Required meaning |
|---|---|
| `enumerate(root)` | Return every store artifact reachable from the root through declared lineage. |
| `lineage_complete(root)` | State whether that root-specific walk is complete. Only exact `True` permits verified coverage. |
| `quarantine(ids)` / `is_quarantined(id)` | Gate affected recall, then prove every enumerated artifact remains gated. |
| `quarantine_coverage(root)` | Report `verified`, `partial`, `unknown`, or `failed` for the durable pre-repair checkpoint. This is distinct from final repair coverage. |
| `source_artifact(id)` | Map a store record to its stable lineage node. Return the ID unchanged when they are identical. |
| `repair_inputs(id)` | Return direct store-owned lineage inputs. The adapter need not copy its records into the reference `LineageLedger`. |
| `retire(id, superseded_at=None)` | Retire an invalid root artifact; preserve history only when `superseded_at` is supplied. |
| `rebuild(id, *, inputs, replacement)` | Reconstruct a mixed artifact from surviving inputs plus any replacement. |
| `recall(term)` | Return active hits with a string `.content` field for negative, positive, and preservation probes. |
| `snapshot()` | Return inspectable adapter state for checkpoint drift detection and receipt pre/post-state binding. Missing state binding prevents verified coverage. |
| `coverage(root)` / `dispositions(root)` | Report final post-repair coverage and one disposition for every enumerated artifact. |

Checkpoint coverage is signed evidence, not scratch bookkeeping. A later
`verified` result cannot erase an earlier `partial`, `unknown`, or `failed`
checkpoint. Missing, raising, or malformed quarantine-coverage evidence fails
closed as `unknown`.

Keep independent propositions as independently addressable lineage artifacts.
If one store record combines the corrected proposition with unrelated facts,
the adapter cannot retire one input while preserving the others without an
additional decomposition or rebuild contract; it must report that limit rather
than fabricate complete repair.

Run the adapter corpus against an isolated synthetic store with
`errata adapter-conformance --binding module:factory`. The binding must expose
stable provider-local proposition identities and active counts for that
fixture. A store unable to observe multiplicity reports `unknown`; text
normalization or embedding similarity cannot substitute for identity. A pass
is candidate internal evidence only and still requires a separate producer to
validate both implementations and the validator.

## Independence and evidence

An implementation report must name its authors, repository and commit, supported
specification version, dependencies, test commands, unsupported behavior, and
licence. Shared conformance vectors are expected. Shared reference-adapter code
disqualifies the implementation as independent evidence.

If an earlier version was written from reference code, preserve that history,
identify the affected version, and disclose the clean-room rewrite. A rewrite
may become a candidate independent implementation only after separate review of
its provenance and behavior; author testimony and line-overlap counts are useful
evidence but are not third-party validation.

One producer may supply an adapter and benchmark results, but that producer
cannot also occupy the separately authored third-party validator role for its
own implementation. Commercial interest and other conflicts must be disclosed;
they do not erase technical evidence, but they control how it can satisfy G4.

No per-implementer permission is required for an independently authored
commercial or non-commercial implementation of the specification. The
irrevocable implementation grant requires every product or service to credit
`LLM Errata`, `Thomas Willner`, and the canonical repository in an ordinarily
accessible product location. It does not permit copying code from `prototype/`,
`scripts/`, or `tests/`, and attribution does not imply technical endorsement,
certification, or audit. See [LICENSE](LICENSE).
