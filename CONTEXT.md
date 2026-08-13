# LLM Errata Publication Context

This context defines the language used to distinguish current public instructions
from retained publication history without weakening evidence provenance.

## Language

**Active surface**:
A tracked public artifact that currently instructs a reviewer, implementer,
validator, or system operator which immutable target and evidence role to use.
_Avoid_: Latest comment, current main, final link

**Historical surface**:
A retained public artifact that accurately records an earlier project state but
must not be used as current instructions.
_Avoid_: Bad comment, deleted record

**Frozen review target**:
An immutable source commit paired with the canonical G2 surface digest that a
review or independent implementation must bind.
_Avoid_: Branch head, latest build

**Supersession**:
An append-only correction that explicitly marks an earlier public instruction
historical and publishes its current replacement.
_Avoid_: Rewrite, deletion

**Evidence role**:
One independently attributable responsibility in the readiness program, such as
reviewer, adapter author, validator author, or operated-system owner.
_Avoid_: Contributor, interested party

**Recruitment evidence**:
Proof that a bounded request was published to a relevant party. It is not proof
that the party accepted, performed, or passed the requested work.
_Avoid_: External evidence, review evidence
