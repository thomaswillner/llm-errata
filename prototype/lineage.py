"""Exact lineage, recorded at import and derivation time.

AGENTS.md is explicit that lineage is recorded when an artifact is created,
not reconstructed after an erratum arrives. That ordering is the whole basis
for calling a closure *known*: a ledger written at write time can be trusted to
enumerate what it recorded, whereas a closure inferred afterwards by similarity
search is a guess and must be reviewed rather than silently mutated.

What this ledger gives is structural evidence — these registered descendants
exist and were addressed. It is not evidence about copies nobody registered.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    store: str
    content: str
    inputs: tuple[str, ...] = ()
    root: str | None = None


class LineageLedger:
    """Maps roots to the local artifacts derived from them, transitively."""

    def __init__(self) -> None:
        self._artifacts: dict[str, Artifact] = {}
        self._root_of: dict[str, str] = {}

    # -- writing -------------------------------------------------------

    def register_import(
        self, root: str, artifact_id: str, *, store: str, content: str
    ) -> Artifact:
        artifact = Artifact(
            artifact_id=artifact_id, store=store, content=content, root=root
        )
        self._artifacts[artifact_id] = artifact
        self._root_of[artifact_id] = root
        return artifact

    def register_derivation(
        self, artifact_id: str, *, store: str, inputs: tuple[str, ...], content: str
    ) -> Artifact:
        unknown = [item for item in inputs if item not in self._artifacts]
        if unknown:
            raise KeyError(
                f"{artifact_id}: derives from unregistered inputs {unknown}. "
                "Lineage must be recorded at derivation time, not reconstructed."
            )
        artifact = Artifact(
            artifact_id=artifact_id, store=store, content=content, inputs=inputs
        )
        self._artifacts[artifact_id] = artifact
        return artifact

    # -- reading -------------------------------------------------------

    def artifact(self, artifact_id: str) -> Artifact:
        return self._artifacts[artifact_id]

    def artifacts(self) -> tuple[Artifact, ...]:
        return tuple(self._artifacts.values())

    def descendants(self, root: str) -> set[str]:
        """Every artifact reachable from `root` through recorded derivation."""

        direct = {
            artifact_id
            for artifact_id, owner in self._root_of.items()
            if owner == root
        }
        closure = set(direct)
        changed = True
        while changed:
            changed = False
            for artifact in self._artifacts.values():
                if artifact.artifact_id in closure:
                    continue
                if any(item in closure for item in artifact.inputs):
                    closure.add(artifact.artifact_id)
                    changed = True
        return closure

    def valid_inputs(
        self, artifact_id: str, *, retired: set[str]
    ) -> tuple[str, ...]:
        """The inputs of `artifact_id` that survive a retirement.

        This is what makes a rebuild a rebuild rather than a deletion: a
        summary mixing three facts, one of which is retired, is reconstructed
        from the other two plus any replacement, not thrown away.
        """

        artifact = self._artifacts[artifact_id]
        return tuple(item for item in artifact.inputs if item not in retired)

    def store_of(self, artifact_id: str) -> str:
        return self._artifacts[artifact_id].store

    def set_content(self, artifact_id: str, content: str) -> None:
        artifact = self._artifacts[artifact_id]
        self._artifacts[artifact_id] = Artifact(
            artifact_id=artifact.artifact_id,
            store=artifact.store,
            content=content,
            inputs=artifact.inputs,
            root=artifact.root,
        )
