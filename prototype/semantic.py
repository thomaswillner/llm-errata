"""Provider-neutral semantic probe evidence.

This module records scoped behavioural evidence.  It deliberately does not
interpret provider prose: an adapter must return a structured verdict bound to
one declared probe and one exact verifier configuration.  Structural repair
checks remain the controller's separate responsibility.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Protocol, Sequence

from prototype.errata import Operation


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True)
    except (TypeError, ValueError) as error:
        raise ValueError("value must be JSON-serializable") from error


def _mapping(value: object, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be an object with string keys")
    return value


def _exact_fields(value: object, *, fields: frozenset[str], name: str) -> Mapping[str, Any]:
    payload = _mapping(value, name=name)
    received = frozenset(payload)
    if received != fields:
        missing = sorted(fields - received)
        unexpected = sorted(received - fields)
        raise ValueError(f"{name} fields mismatch: missing={missing}, unexpected={unexpected}")
    return payload


def _nonempty_string(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _probe_id(value: object, *, name: str) -> str:
    text = _nonempty_string(value, name=name)
    if _PROBE_ID.fullmatch(text) is None:
        raise ValueError(f"{name} must be a safe protocol identifier")
    return text


def _erasure_probe_id(kind: ProbeKind) -> str:
    if kind is ProbeKind.NEGATIVE:
        return ERASURE_NEGATIVE_PROBE_ID
    if kind is ProbeKind.PRESERVATION:
        return ERASURE_PRESERVATION_PROBE_ID
    raise ValueError("erasure has no positive replacement probe")


def _sha256(value: object, *, name: str) -> str:
    text = _nonempty_string(value, name=name)
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return text


def _timestamp(value: object, *, name: str) -> str:
    text = _nonempty_string(value, name=name)
    if not text.endswith("Z"):
        raise ValueError(f"{name} must be an RFC 3339 UTC timestamp")
    try:
        datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(f"{name} must be an RFC 3339 UTC timestamp") from error
    return text


def _freeze_json(value: object) -> object:
    """Copy and recursively freeze JSON-compatible configuration values."""

    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


class ProbeKind(str, Enum):
    """The repair-triad question represented by a semantic probe."""

    NEGATIVE = "negative"
    POSITIVE = "positive"
    PRESERVATION = "preservation"


class ObservationVerdict(str, Enum):
    """A verifier's explicit result.  Prose cannot substitute for one."""

    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"


class SemanticCoverage(str, Enum):
    """Terminal coverage of declared required semantic probes."""

    VERIFIED = "verified"
    UNKNOWN = "unknown"
    FAILED = "failed"


ERASURE_PROMPT_TEMPLATE = "erasure-content-free-v1"
ERASURE_SCOPE = "declared-store-set-v1"
ERASURE_NEGATIVE_PROBE_ID = "erase-negative-v1"
ERASURE_PRESERVATION_PROBE_ID = "erase-preservation-v1"
_PROBE_ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")


@dataclass(frozen=True)
class SemanticProbe:
    """One declared, provider-neutral question over a bounded scope.

    Erasure records intentionally have no retired-value field.  Provider
    adapters may receive confidential material ephemerally, but persisted
    probes, observations, and reports cannot carry it through this interface.
    """

    probe_id: str
    kind: ProbeKind
    operation: Operation
    scope: str
    prompt_template: str
    required: bool = True

    def __post_init__(self) -> None:
        _probe_id(self.probe_id, name="probe_id")
        if not isinstance(self.kind, ProbeKind):
            raise ValueError("kind must be a ProbeKind")
        if not isinstance(self.operation, Operation):
            raise ValueError("operation must be an Operation")
        _nonempty_string(self.scope, name="scope")
        _nonempty_string(self.prompt_template, name="prompt_template")
        if not isinstance(self.required, bool):
            raise ValueError("required must be boolean")
        if self.operation is Operation.ERASE and self.kind is ProbeKind.POSITIVE:
            raise ValueError("erasure has no positive replacement probe")
        if (
            self.operation is Operation.ERASE
            and (
                self.prompt_template != ERASURE_PROMPT_TEMPLATE
                or self.scope != ERASURE_SCOPE
                or self.probe_id != _erasure_probe_id(self.kind)
            )
        ):
            raise ValueError("erasure probes require fixed content-free protocol fields")

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "kind": self.kind.value,
            "operation": self.operation.value,
            "scope": self.scope,
            "prompt_template": self.prompt_template,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, value: object) -> "SemanticProbe":
        payload = _exact_fields(
            value,
            fields=frozenset(
                {"probe_id", "kind", "operation", "scope", "prompt_template", "required"}
            ),
            name="semantic probe",
        )
        try:
            kind = ProbeKind(payload["kind"])
        except (TypeError, ValueError) as error:
            raise ValueError("semantic probe kind is invalid") from error
        try:
            operation = Operation(payload["operation"])
        except (TypeError, ValueError) as error:
            raise ValueError("semantic probe operation is invalid") from error
        return cls(
            probe_id=_probe_id(payload["probe_id"], name="probe_id"),
            kind=kind,
            operation=operation,
            scope=_nonempty_string(payload["scope"], name="scope"),
            prompt_template=_nonempty_string(
                payload["prompt_template"], name="prompt_template"
            ),
            required=payload["required"],
        )


@dataclass(frozen=True)
class VerifierConfig:
    """Exact configuration that binds observations to one verifier setup."""

    provider: str
    model: str
    prompt_template_version: str
    sampling: Mapping[str, Any]
    seed: int | None = None

    def __post_init__(self) -> None:
        _nonempty_string(self.provider, name="provider")
        _nonempty_string(self.model, name="model")
        _nonempty_string(self.prompt_template_version, name="prompt_template_version")
        sampling = _mapping(self.sampling, name="sampling")
        # Serializing here rejects NaN, functions, and other non-portable values
        # before a digest can be advertised as a stable binding.
        normalized = json.loads(_canonical_json(dict(sampling)))
        object.__setattr__(self, "sampling", _freeze_json(normalized))
        if self.seed is not None and (not isinstance(self.seed, int) or isinstance(self.seed, bool)):
            raise ValueError("seed must be an integer or null")

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_template_version": self.prompt_template_version,
            "sampling": _thaw_json(self.sampling),
            "seed": self.seed,
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, value: object) -> "VerifierConfig":
        payload = _exact_fields(
            value,
            fields=frozenset(
                {"provider", "model", "prompt_template_version", "sampling", "seed"}
            ),
            name="verifier config",
        )
        return cls(
            provider=_nonempty_string(payload["provider"], name="provider"),
            model=_nonempty_string(payload["model"], name="model"),
            prompt_template_version=_nonempty_string(
                payload["prompt_template_version"], name="prompt_template_version"
            ),
            sampling=_mapping(payload["sampling"], name="sampling"),
            seed=payload["seed"],
        )


@dataclass(frozen=True)
class SemanticObservation:
    """Persistable verifier result, excluding raw provider output."""

    probe_id: str
    operation: Operation
    verdict: ObservationVerdict
    config_digest: str
    observed_at: str
    response_digest: str

    def __post_init__(self) -> None:
        _probe_id(self.probe_id, name="probe_id")
        if not isinstance(self.operation, Operation):
            raise ValueError("operation must be an Operation")
        if (
            self.operation is Operation.ERASE
            and self.probe_id
            not in {ERASURE_NEGATIVE_PROBE_ID, ERASURE_PRESERVATION_PROBE_ID}
        ):
            raise ValueError("erasure observations require fixed content-free probe identifiers")
        if not isinstance(self.verdict, ObservationVerdict):
            raise ValueError("verdict must be an ObservationVerdict")
        _sha256(self.config_digest, name="config_digest")
        _timestamp(self.observed_at, name="observed_at")
        _sha256(self.response_digest, name="response_digest")

    def to_dict(self) -> dict[str, str]:
        return {
            "probe_id": self.probe_id,
            "operation": self.operation.value,
            "verdict": self.verdict.value,
            "config_digest": self.config_digest,
            "observed_at": self.observed_at,
            "response_digest": self.response_digest,
        }

    @classmethod
    def from_dict(cls, value: object) -> "SemanticObservation":
        payload = _exact_fields(
            value,
            fields=frozenset(
                {
                    "probe_id",
                    "operation",
                    "verdict",
                    "config_digest",
                    "observed_at",
                    "response_digest",
                }
            ),
            name="semantic observation",
        )
        try:
            operation = Operation(payload["operation"])
        except (TypeError, ValueError) as error:
            raise ValueError("semantic observation operation is invalid") from error
        try:
            verdict = ObservationVerdict(payload["verdict"])
        except (TypeError, ValueError) as error:
            raise ValueError("semantic observation verdict is invalid") from error
        return cls(
            probe_id=_probe_id(payload["probe_id"], name="probe_id"),
            operation=operation,
            verdict=verdict,
            config_digest=_sha256(payload["config_digest"], name="config_digest"),
            observed_at=_timestamp(payload["observed_at"], name="observed_at"),
            response_digest=_sha256(payload["response_digest"], name="response_digest"),
        )


class SemanticVerifier(Protocol):
    """Provider adapter seam.  SDKs and confidential runtime inputs stay out."""

    def evaluate(
        self, probe: SemanticProbe, config: VerifierConfig
    ) -> SemanticObservation | None: ...


class RecordedSemanticVerifier:
    """Offline verifier backed by checked-in structured observations."""

    def __init__(self, observations: Iterable[SemanticObservation]) -> None:
        self._observations = tuple(observations)
        if not all(isinstance(item, SemanticObservation) for item in self._observations):
            raise ValueError("recorded observations must be SemanticObservation instances")

    @property
    def observations(self) -> tuple[SemanticObservation, ...]:
        return self._observations

    def evaluate(
        self, probe: SemanticProbe, config: VerifierConfig
    ) -> SemanticObservation | None:
        matches = [
            item
            for item in self._observations
            if item.probe_id == probe.probe_id
            and item.operation is probe.operation
            and item.config_digest == config.digest
        ]
        return matches[0] if len(matches) == 1 else None


@dataclass(frozen=True)
class SemanticProbeReport:
    """Canonical, coverage-aware semantic evidence report."""

    config_digest: str
    coverage: SemanticCoverage
    probes: tuple[SemanticProbe, ...]
    observations: tuple[SemanticObservation, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self, *, adapter_diagnostics: Sequence[str] = ()) -> None:
        _sha256(self.config_digest, name="config_digest")
        if not isinstance(self.coverage, SemanticCoverage):
            raise ValueError("coverage must be a SemanticCoverage")
        if not all(isinstance(item, SemanticProbe) for item in self.probes):
            raise ValueError("probes must be SemanticProbe instances")
        if not all(isinstance(item, SemanticObservation) for item in self.observations):
            raise ValueError("observations must be SemanticObservation instances")
        if not all(isinstance(item, str) and item for item in self.limitations):
            raise ValueError("limitations must contain non-empty strings")
        if not all(isinstance(item, str) and item for item in adapter_diagnostics):
            raise ValueError("adapter diagnostics must contain non-empty strings")
        evidence_coverage, evidence_limitations, accepted = _evaluate_evidence(
            self.probes,
            self.observations,
            self.config_digest,
        )
        expected_limitations = tuple(
            sorted(set(evidence_limitations).union(adapter_diagnostics))
        )
        expected_coverage = (
            SemanticCoverage.FAILED
            if evidence_coverage is SemanticCoverage.FAILED
            else SemanticCoverage.UNKNOWN
            if expected_limitations
            else SemanticCoverage.VERIFIED
        )
        if self.observations != accepted:
            raise ValueError(
                "semantic probe report observations must uniquely match declared probes, "
                "operations, and configuration"
            )
        if self.limitations != expected_limitations:
            raise ValueError("semantic probe report limitations contradict its evidence")
        if self.coverage is not expected_coverage:
            raise ValueError("semantic probe report coverage contradicts its evidence")

    @classmethod
    def _from_runner_evidence(
        cls,
        *,
        config_digest: str,
        probes: Sequence[SemanticProbe],
        observations: Sequence[SemanticObservation],
        adapter_diagnostics: Sequence[str],
    ) -> "SemanticProbeReport":
        """Build a report from trusted runner diagnostics and serialized evidence."""

        evidence_coverage, evidence_limitations, accepted = _evaluate_evidence(
            probes, observations, config_digest
        )
        # Evidence rejected before persistence (duplicates, unexpected IDs,
        # operation/configuration mismatches) cannot be rediscovered by
        # validating the accepted observation subset. Carry only the
        # evaluator-produced, sanitized messages through this private runner
        # path; public construction and parsing still derive their limitations
        # exclusively from the serialized evidence they receive.
        diagnostics = tuple(
            sorted(set(adapter_diagnostics).union(evidence_limitations))
        )
        limitations = tuple(sorted(set(evidence_limitations).union(diagnostics)))
        coverage = (
            SemanticCoverage.FAILED
            if evidence_coverage is SemanticCoverage.FAILED
            else SemanticCoverage.UNKNOWN
            if limitations
            else SemanticCoverage.VERIFIED
        )
        report = object.__new__(cls)
        object.__setattr__(report, "config_digest", config_digest)
        object.__setattr__(report, "coverage", coverage)
        object.__setattr__(report, "probes", tuple(probes))
        object.__setattr__(report, "observations", accepted)
        object.__setattr__(report, "limitations", limitations)
        report._validate(adapter_diagnostics=diagnostics)
        return report

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_digest": self.config_digest,
            "coverage": self.coverage.value,
            "probes": [item.to_dict() for item in sorted(self.probes, key=lambda item: item.probe_id)],
            "observations": [
                item.to_dict()
                for item in sorted(
                    self.observations,
                    key=lambda item: (item.probe_id, item.observed_at, item.response_digest),
                )
            ],
            "limitations": list(sorted(self.limitations)),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: object) -> "SemanticProbeReport":
        payload = _exact_fields(
            value,
            fields=frozenset(
                {"config_digest", "coverage", "probes", "observations", "limitations"}
            ),
            name="semantic probe report",
        )
        if not isinstance(payload["probes"], list) or not isinstance(payload["observations"], list):
            raise ValueError("semantic probe report probes and observations must be arrays")
        if not isinstance(payload["limitations"], list):
            raise ValueError("semantic probe report limitations must be an array")
        try:
            coverage = SemanticCoverage(payload["coverage"])
        except (TypeError, ValueError) as error:
            raise ValueError("semantic probe report coverage is invalid") from error
        report = cls(
            config_digest=_sha256(payload["config_digest"], name="config_digest"),
            coverage=coverage,
            probes=tuple(SemanticProbe.from_dict(item) for item in payload["probes"]),
            observations=tuple(
                SemanticObservation.from_dict(item) for item in payload["observations"]
            ),
            limitations=tuple(
                _nonempty_string(item, name="limitation") for item in payload["limitations"]
            ),
        )
        return report


def _required_triad(probes: Sequence[SemanticProbe]) -> tuple[Operation, set[ProbeKind]]:
    if not probes or not all(isinstance(probe, SemanticProbe) for probe in probes):
        raise ValueError("probes must be SemanticProbe instances")
    probe_ids = [probe.probe_id for probe in probes]
    if len(probe_ids) != len(set(probe_ids)):
        raise ValueError("probe IDs must be unique")
    operations = {probe.operation for probe in probes}
    if len(operations) != 1:
        raise ValueError("all probes in a report must have one operation")
    operation = next(iter(operations))
    required_kinds = {probe.kind for probe in probes if probe.required}
    expected = (
        {ProbeKind.NEGATIVE, ProbeKind.PRESERVATION}
        if operation is Operation.ERASE
        else {ProbeKind.NEGATIVE, ProbeKind.POSITIVE, ProbeKind.PRESERVATION}
    )
    if required_kinds != expected:
        raise ValueError(f"required probe triad must be exactly {sorted(item.value for item in expected)}")
    return operation, expected


def _evaluate_evidence(
    probes: Sequence[SemanticProbe],
    observations: Sequence[SemanticObservation],
    config_digest: str,
) -> tuple[SemanticCoverage, tuple[str, ...], tuple[SemanticObservation, ...]]:
    _required_triad(probes)
    limitations: list[str] = []
    declared = {item.probe_id: item for item in probes}
    grouped: dict[str, list[SemanticObservation]] = {}
    for item in observations:
        grouped.setdefault(item.probe_id, []).append(item)
    valid_fails: set[str] = set()
    accepted: list[SemanticObservation] = []
    accepted_by_id: dict[str, SemanticObservation] = {}
    unexpected_count = 0
    for probe_id, records in grouped.items():
        if probe_id not in declared:
            unexpected_count += len(records)
        elif len(records) != 1:
            limitations.append(f"duplicate observations for probe {probe_id}")
        else:
            record = records[0]
            probe = declared[probe_id]
            if record.operation is not probe.operation:
                limitations.append(f"operation mismatch for probe {probe_id}")
            elif record.config_digest != config_digest:
                limitations.append(f"configuration drift for probe {probe_id}")
            else:
                accepted.append(record)
                accepted_by_id[probe_id] = record
            if (
                record.operation is probe.operation
                and record.config_digest == config_digest
                and record.verdict is ObservationVerdict.FAIL
                and probe.required
            ):
                valid_fails.add(probe_id)
    if unexpected_count:
        limitations.append(f"unexpected observation identifiers: {unexpected_count}")
    for probe in probes:
        record = accepted_by_id.get(probe.probe_id)
        if record is None and probe.required:
            limitations.append(f"missing required observation for probe {probe.probe_id}")
        elif record is not None:
            if probe.required and record.verdict in {
                ObservationVerdict.INCONCLUSIVE, ObservationVerdict.ERROR
            }:
                limitations.append(
                    f"required probe {probe.probe_id} returned {record.verdict.value}"
                )
    normalized = tuple(sorted(set(limitations)))
    persisted = tuple(sorted(accepted, key=lambda item: (item.probe_id, item.observed_at, item.response_digest)))
    if valid_fails:
        return SemanticCoverage.FAILED, normalized, persisted
    return (SemanticCoverage.UNKNOWN if normalized else SemanticCoverage.VERIFIED), normalized, persisted


class SemanticProbeRunner:
    """Validate probe evidence and aggregate it without upgrading uncertainty."""

    def run(
        self,
        probes: Sequence[SemanticProbe],
        config: VerifierConfig,
        verifier: SemanticVerifier | Iterable[SemanticObservation],
    ) -> SemanticProbeReport:
        declared = tuple(probes)
        if not all(isinstance(item, SemanticProbe) for item in declared):
            raise ValueError("probes must be SemanticProbe instances")
        ids = [item.probe_id for item in declared]
        if len(ids) != len(set(ids)):
            raise ValueError("probe IDs must be unique")
        adapter_limitations: list[str] = []

        if isinstance(verifier, RecordedSemanticVerifier):
            received = verifier.observations
        elif hasattr(verifier, "evaluate"):
            received_items: list[SemanticObservation] = []
            adapter_limitations = []
            for item in declared:
                try:
                    result = verifier.evaluate(item, config)  # type: ignore[union-attr]
                except Exception:
                    # Provider exceptions are untrusted input. Their messages
                    # and even dynamically created class names can contain
                    # retired or confidential content, so persist only this
                    # closed diagnostic code plus the declared protocol ID.
                    adapter_limitations.append(
                        f"provider error for probe {item.probe_id}"
                    )
                    continue
                if result is None:
                    continue
                if not isinstance(result, SemanticObservation):
                    adapter_limitations.append(
                        f"malformed verifier result for probe {item.probe_id}"
                    )
                    continue
                received_items.append(result)
            received = tuple(received_items)
        else:
            received = tuple(verifier)
            adapter_limitations = []
        if not all(isinstance(item, SemanticObservation) for item in received):
            raise ValueError("observations must be SemanticObservation instances")

        return SemanticProbeReport._from_runner_evidence(
            config_digest=config.digest,
            probes=declared,
            observations=received,
            adapter_diagnostics=adapter_limitations,
        )
