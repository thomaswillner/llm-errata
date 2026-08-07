"""Authentication for errata and receipts.

**This is a demo signer, and it is not the real thing.**

`DemoSigner` is a keyed MAC over a canonical serialisation. It authenticates
that a message came from a holder of the key and detects any tampering, which
is what the Phase 1 scenarios need to exercise: forgery, replay, rollback, and
post-signature edits.

It is symmetric, so it gives no third-party non-repudiation. A verifier must
hold the same secret the signer holds, which means it cannot support the
property a real deployment needs — an owner publishing a public key that any
importer can verify against without being able to forge.

Two reasons it ships this way rather than using Ed25519:

- The repository installs nothing. Every checker and this prototype are Python
  standard library only, so a green run cannot be an artefact of the toolchain,
  and `hashlib`/`hmac` are the strongest primitives available under that rule.
- Hand-rolling Ed25519 inside a repository about verification honesty would be
  a worse trade than declaring the limitation.

`Signer` and `VerificationKey` are the seam. Phase 2 replaces `DemoSigner` with
an Ed25519 implementation without touching any caller.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol


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
    """What a verifier needs in order to check a signature.

    In the demo this carries the shared secret, because `DemoSigner` is
    symmetric. `key_id` is the field that survives the move to Ed25519.
    """

    key_id: str
    _secret: bytes

    def verify(self, payload: dict[str, Any], signature: str) -> bool:
        expected = hmac.new(
            self._secret, canonical_bytes(payload), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


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


class DemoSigner:
    def __init__(self, secret: bytes, key_id: str = "demo-key-1") -> None:
        self._secret = secret
        self._key_id = key_id

    @property
    def public(self) -> VerificationKey:
        return VerificationKey(key_id=self._key_id, _secret=self._secret)

    def sign(self, payload: dict[str, Any]) -> str:
        return hmac.new(
            self._secret, canonical_bytes(payload), hashlib.sha256
        ).hexdigest()

    def sign_erratum(self, erratum: Erratum) -> Erratum:
        return erratum.replace(signature=self.sign(erratum.signable()))
