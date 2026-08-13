"""Authentication for errata and receipts.

Signatures are real Ed25519, per RFC 8032, implemented in
[`ed25519.py`](ed25519.py) using only the standard library and checked against
the RFC's published test vectors. That matters for this proposal specifically:
an owner publishes a public key, and any importer verifies an erratum against
it without being able to forge one. A symmetric MAC cannot provide that, and an
earlier version of this module used one.

What the signature does and does not establish is the same either way, and the
distinction is load-bearing:

- It authenticates **who** attested to **which bytes**.
- It says nothing about whether the attestation is truthful or complete. A
  compromised importer can sign an honest-looking receipt over a repair it
  never performed. That is a trust boundary, not a bug, and `THREAT_MODEL.md`
  treats it as one.

`Signer` and `VerificationKey` are the seam. The bundled implementation is a
reference, not a hardened one: it is not constant-time, so a deployment holding
keys an attacker can attack by timing should link libsodium and substitute a
signer here. No caller changes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from prototype import ed25519


if TYPE_CHECKING:  # pragma: no cover - typing only
    from prototype.errata import Erratum


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    """Serialise deterministically so a signature is reproducible."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def commitment(*parts: str) -> str:
    """A short, stable digest used to bind states and identify artifacts.

    This is never applied to an erased value. Committing to a low-entropy
    proposition — "vegetarian" — would produce a digest an attacker can confirm
    by guessing, which is the opposite of content-free evidence. Erasure
    evidence records that a descendant was retired, and nothing about what it
    said.
    """

    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\x1f")
    return digest.hexdigest()[:32]


@dataclass(frozen=True)
class VerificationKey:
    """A published Ed25519 public key. Safe to distribute: it cannot sign."""

    key_id: str
    public_bytes: bytes

    def verify(self, payload: dict[str, Any], signature: str) -> bool:
        try:
            raw = bytes.fromhex(signature)
        except ValueError:
            return False
        return ed25519.verify(self.public_bytes, canonical_bytes(payload), raw)

    def to_hex(self) -> str:
        return self.public_bytes.hex()


class Signer(Protocol):  # pragma: no cover - structural type
    """What the controller and the fixtures are typed against.

    `DemoSigner` is the only implementation today. The point of naming the
    protocol is that `controller.Importer` and `scenario.build_importer` accept
    it rather than the concrete class, so an Ed25519 signer substitutes without
    touching either.
    """

    @property
    def public(self) -> VerificationKey: ...

    def sign(self, payload: dict[str, Any]) -> str: ...

    def sign_erratum(self, erratum: Erratum) -> Erratum: ...


class Ed25519Signer:
    """Holds a seed and signs with it. The seed never leaves this object."""

    def __init__(self, seed: bytes, key_id: str = "key-1") -> None:
        if len(seed) != 32:
            # Deterministic derivation from a short label keeps fixtures
            # readable and reproducible. Real keys are generated, not derived
            # from a string, and nothing here should be reused outside tests.
            seed = hashlib.sha256(seed).digest()
        self._seed = seed
        self._key_id = key_id

    @property
    def public(self) -> VerificationKey:
        return VerificationKey(
            key_id=self._key_id, public_bytes=ed25519.public_key(self._seed)
        )

    def sign(self, payload: dict[str, Any]) -> str:
        return ed25519.sign(self._seed, canonical_bytes(payload)).hex()

    def sign_erratum(self, erratum: Erratum) -> Erratum:
        bound = erratum.replace(signing_key_id=self._key_id, signature=None)
        return bound.replace(signature=self.sign(bound.signable()))


#: Retained so existing fixtures keep working. The name is deliberately no
#: longer accurate about the algorithm: what was demo-grade was the MAC, and
#: that is gone.
DemoSigner = Ed25519Signer
