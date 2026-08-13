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

## Independence and evidence

An implementation report must name its authors, repository and commit, supported
specification version, dependencies, test commands, unsupported behavior, and
licence. Shared conformance vectors are expected. Shared reference-adapter code
disqualifies the implementation as independent evidence.

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
