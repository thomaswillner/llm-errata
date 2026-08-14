"""Durable evidence that a signed erratum's known descendants are gated."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any


class CheckpointError(ValueError):
    """A checkpoint is malformed, unsafe, or no longer trustworthy."""


_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_DIGEST = re.compile(r"[0-9a-f]{64}")
_COVERAGE = {"verified", "partial", "unknown", "failed"}


def _utc_timestamp(value: object, label: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.endswith("Z"):
        raise CheckpointError(f"{label} must be an ISO UTC timestamp")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise CheckpointError(f"{label} must be an ISO UTC timestamp") from error
    return value


@dataclass(frozen=True)
class AdapterCheckpoint:
    name: str
    required: bool
    artifact_ids: tuple[str, ...]
    coverage: str
    limitation: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _SAFE_ID.fullmatch(self.name):
            raise CheckpointError("adapter name is unsafe")
        if not isinstance(self.required, bool):
            raise CheckpointError("adapter required must be boolean")
        if (
            not isinstance(self.artifact_ids, tuple)
            or not all(isinstance(item, str) and item for item in self.artifact_ids)
            or tuple(sorted(set(self.artifact_ids))) != self.artifact_ids
        ):
            raise CheckpointError("adapter artifact IDs must be unique and sorted")
        if self.coverage not in _COVERAGE:
            raise CheckpointError("adapter coverage is invalid")
        if self.limitation is not None and (
            not isinstance(self.limitation, str) or not self.limitation.strip()
        ):
            raise CheckpointError("adapter limitation must be non-empty")
        if self.coverage == "unknown" and self.limitation is None:
            raise CheckpointError("unknown adapter coverage requires a limitation")

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "required": self.required,
            "artifact_ids": list(self.artifact_ids),
            "coverage": self.coverage,
            "limitation": self.limitation,
        }

    @classmethod
    def from_dict(cls, value: object) -> AdapterCheckpoint:
        if not isinstance(value, dict) or set(value) != {
            "name", "required", "artifact_ids", "coverage", "limitation"
        }:
            raise CheckpointError("adapter checkpoint fields are invalid")
        artifacts = value["artifact_ids"]
        if not isinstance(artifacts, list):
            raise CheckpointError("adapter artifact IDs must be an array")
        return cls(
            name=value["name"],
            required=value["required"],
            artifact_ids=tuple(artifacts),
            coverage=value["coverage"],
            limitation=value["limitation"],
        )


@dataclass(frozen=True)
class QuarantineCheckpoint:
    schema_version: int
    erratum_id: str
    sequence: int
    target_root: str
    pre_state_root: str
    adapters: tuple[AdapterCheckpoint, ...]
    created_at: str
    consumed: bool
    consumed_at: str | None
    checkpoint_digest: str

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise CheckpointError("checkpoint schema version must be 1")
        if not isinstance(self.erratum_id, str) or not _SAFE_ID.fullmatch(self.erratum_id):
            raise CheckpointError("erratum ID is unsafe")
        if type(self.sequence) is not int or self.sequence < 1:
            raise CheckpointError("checkpoint sequence must be a positive integer")
        if not isinstance(self.target_root, str) or not self.target_root:
            raise CheckpointError("checkpoint target root is invalid")
        if not isinstance(self.pre_state_root, str) or not _DIGEST.fullmatch(
            self.pre_state_root
        ):
            raise CheckpointError("checkpoint pre-state root is invalid")
        if not isinstance(self.adapters, tuple) or not self.adapters:
            raise CheckpointError("checkpoint adapters must be non-empty")
        names = tuple(adapter.name for adapter in self.adapters)
        if tuple(sorted(set(names))) != names:
            raise CheckpointError("checkpoint adapters must be unique and sorted")
        _utc_timestamp(self.created_at, "created_at")
        if not isinstance(self.consumed, bool):
            raise CheckpointError("checkpoint consumed must be boolean")
        _utc_timestamp(self.consumed_at, "consumed_at", optional=True)
        if self.consumed != (self.consumed_at is not None):
            raise CheckpointError("checkpoint consumption fields disagree")
        if not isinstance(self.checkpoint_digest, str) or not _DIGEST.fullmatch(
            self.checkpoint_digest
        ):
            raise CheckpointError("checkpoint digest is invalid")
        if self.canonical_digest() != self.checkpoint_digest:
            raise CheckpointError("checkpoint digest does not match content")

    @classmethod
    def create(
        cls,
        *,
        erratum_id: str,
        sequence: int,
        target_root: str,
        pre_state_root: str,
        adapters: tuple[AdapterCheckpoint, ...],
        created_at: str,
    ) -> QuarantineCheckpoint:
        provisional = object.__new__(cls)
        object.__setattr__(provisional, "schema_version", 1)
        object.__setattr__(provisional, "erratum_id", erratum_id)
        object.__setattr__(provisional, "sequence", sequence)
        object.__setattr__(provisional, "target_root", target_root)
        object.__setattr__(provisional, "pre_state_root", pre_state_root)
        object.__setattr__(provisional, "adapters", adapters)
        object.__setattr__(provisional, "created_at", created_at)
        object.__setattr__(provisional, "consumed", False)
        object.__setattr__(provisional, "consumed_at", None)
        object.__setattr__(provisional, "checkpoint_digest", "0" * 64)
        digest = provisional.canonical_digest()
        return cls(1, erratum_id, sequence, target_root, pre_state_root, adapters,
                   created_at, False, None, digest)

    def _identity_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "erratum_id": self.erratum_id,
            "sequence": self.sequence,
            "target_root": self.target_root,
            "pre_state_root": self.pre_state_root,
            "adapters": [adapter.to_dict() for adapter in self.adapters],
            "created_at": self.created_at,
        }

    def canonical_digest(self) -> str:
        encoded = json.dumps(
            self._identity_dict(), sort_keys=True, separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            **self._identity_dict(),
            "consumed": self.consumed,
            "consumed_at": self.consumed_at,
            "checkpoint_digest": self.checkpoint_digest,
        }

    @classmethod
    def from_dict(cls, value: object) -> QuarantineCheckpoint:
        keys = {
            "schema_version", "erratum_id", "sequence", "target_root",
            "pre_state_root", "adapters", "created_at", "consumed",
            "consumed_at", "checkpoint_digest",
        }
        if not isinstance(value, dict) or set(value) != keys:
            raise CheckpointError("checkpoint fields are invalid")
        adapters = value["adapters"]
        if not isinstance(adapters, list):
            raise CheckpointError("checkpoint adapters must be an array")
        return cls(
            schema_version=value["schema_version"],
            erratum_id=value["erratum_id"],
            sequence=value["sequence"],
            target_root=value["target_root"],
            pre_state_root=value["pre_state_root"],
            adapters=tuple(AdapterCheckpoint.from_dict(item) for item in adapters),
            created_at=value["created_at"],
            consumed=value["consumed"],
            consumed_at=value["consumed_at"],
            checkpoint_digest=value["checkpoint_digest"],
        )

    def with_consumed(self, timestamp: str) -> QuarantineCheckpoint:
        if self.consumed:
            raise CheckpointError("checkpoint is already consumed")
        return replace(self, consumed=True, consumed_at=timestamp)


class CheckpointStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def path_for(self, checkpoint: QuarantineCheckpoint) -> Path:
        return self.root / f"{checkpoint.sequence:04d}-{checkpoint.erratum_id}.json"

    def write(self, checkpoint: QuarantineCheckpoint) -> Path:
        path = self.path_for(checkpoint)
        self._atomic_write(path, checkpoint.to_dict())
        return path

    def load(self, path: Path) -> QuarantineCheckpoint:
        path = Path(path)
        if path.parent.resolve() != self.root.resolve():
            raise CheckpointError("checkpoint path is outside checkpoint directory")
        try:
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
                raise CheckpointError("checkpoint path must be a regular file")
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
        except CheckpointError:
            raise
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CheckpointError("checkpoint is not readable JSON") from error
        checkpoint = QuarantineCheckpoint.from_dict(payload)
        if path.name != self.path_for(checkpoint).name:
            raise CheckpointError("checkpoint filename does not match content")
        return checkpoint

    def consume(self, path: Path, timestamp: str) -> QuarantineCheckpoint:
        consumed = self.load(path).with_consumed(timestamp)
        self._atomic_write(Path(path), consumed.to_dict())
        return consumed

    def _atomic_write(self, path: Path, payload: dict[str, object]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if path.exists() and (path.is_symlink() or not stat.S_ISREG(path.stat().st_mode)):
            raise CheckpointError("checkpoint target must be a regular file")
        data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
        descriptor, temporary = tempfile.mkstemp(prefix=".checkpoint-", dir=self.root)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, path)
            directory = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError as error:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise CheckpointError("checkpoint atomic write failed") from error
