"""Ed25519 signatures, per RFC 8032, in the Python standard library.

Why this exists: the repository installs nothing, so a green CI run cannot be
an artefact of the toolchain. That rule previously forced a keyed MAC, which is
symmetric and therefore cannot give an owner a public key that importers verify
against without also being able to forge. A proposal about verifiable repair
cannot rest on that.

**This is a reference implementation, not a hardened one.** It is written for
legibility and for exact agreement with the RFC's published test vectors. It
performs no constant-time arithmetic — Python integers cannot — so it is
unsuitable for signing with a key an attacker can attack by timing. The RFC's
own reference implementation carries the same caveat. For this repository, where
signing keys exist to demonstrate a conformance contract, verifiability matters
and side-channel resistance does not. A deployment should link libsodium.

Correctness is not asserted here. `tests/test_ed25519.py` runs the test vectors
from RFC 8032 section 7.1, including the empty message and the 1023-byte
message, and refuses to pass without them.
"""

from __future__ import annotations

import hashlib

# Curve parameters, RFC 8032 section 5.1.
P = 2**255 - 19
Q = 2**252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
I = pow(2, (P - 1) // 4, P)

# Extended twisted Edwards coordinates: (X, Y, Z, T) with x = X/Z, y = Y/Z.
Point = tuple[int, int, int, int]


def _sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def _inv(x: int) -> int:
    return pow(x, P - 2, P)


def _add(a: Point, b: Point) -> Point:
    x1, y1, z1, t1 = a
    x2, y2, z2, t2 = b
    aa = (y1 - x1) * (y2 - x2) % P
    bb = (y1 + x1) * (y2 + x2) % P
    cc = 2 * t1 * t2 * D % P
    dd = 2 * z1 * z2 % P
    e, f, g, h = bb - aa, dd - cc, dd + cc, bb + aa
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _double(a: Point) -> Point:
    return _add(a, a)


def _scalar_mult(point: Point, scalar: int) -> Point:
    result: Point = (0, 1, 1, 0)
    addend = point
    while scalar > 0:
        if scalar & 1:
            result = _add(result, addend)
        addend = _double(addend)
        scalar >>= 1
    return result


def _recover_x(y: int, sign: int) -> int | None:
    if y >= P:
        return None
    xx = (y * y - 1) * _inv(D * y * y + 1) % P
    if xx == 0:
        return None if sign else 0
    x = pow(xx, (P + 3) // 8, P)
    if (x * x - xx) % P != 0:
        x = x * I % P
    if (x * x - xx) % P != 0:
        return None
    if x & 1 != sign:
        x = P - x
    return x


_BASE_Y = 4 * _inv(5) % P
_BASE_X = _recover_x(_BASE_Y, 0)
assert _BASE_X is not None
BASE: Point = (_BASE_X, _BASE_Y, 1, _BASE_X * _BASE_Y % P)


def _compress(point: Point) -> bytes:
    x, y, z, _ = point
    zi = _inv(z)
    x, y = x * zi % P, y * zi % P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decompress(data: bytes) -> Point | None:
    if len(data) != 32:
        return None
    value = int.from_bytes(data, "little")
    sign = value >> 255
    y = value & ((1 << 255) - 1)
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % P)


def _secret_expand(seed: bytes) -> tuple[int, bytes]:
    if len(seed) != 32:
        raise ValueError("an Ed25519 seed is exactly 32 bytes")
    digest = _sha512(seed)
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    return scalar, digest[32:]


def public_key(seed: bytes) -> bytes:
    """Derive the 32-byte public key for a 32-byte seed."""

    scalar, _ = _secret_expand(seed)
    return _compress(_scalar_mult(BASE, scalar))


def sign(seed: bytes, message: bytes) -> bytes:
    """Produce a 64-byte PureEdDSA signature."""

    scalar, prefix = _secret_expand(seed)
    encoded_public = _compress(_scalar_mult(BASE, scalar))
    r = int.from_bytes(_sha512(prefix + message), "little") % Q
    encoded_r = _compress(_scalar_mult(BASE, r))
    k = int.from_bytes(_sha512(encoded_r + encoded_public + message), "little") % Q
    s = (r + k * scalar) % Q
    return encoded_r + int.to_bytes(s, 32, "little")


def verify(encoded_public: bytes, message: bytes, signature: bytes) -> bool:
    """Verify a signature. Returns False rather than raising on malformed input.

    Every structural failure is a verification failure: a caller must never be
    able to distinguish "malformed" from "wrong key" by catching an exception,
    and must never treat an exception as anything other than a refusal.
    """

    if len(signature) != 64 or len(encoded_public) != 32:
        return False
    point = _decompress(encoded_public)
    if point is None:
        return False
    encoded_r = signature[:32]
    r_point = _decompress(encoded_r)
    if r_point is None:
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= Q:
        # Reject non-canonical scalars: accepting them makes signatures
        # malleable, so a receipt could be altered while still verifying.
        return False
    k = int.from_bytes(_sha512(encoded_r + encoded_public + message), "little") % Q
    left = _scalar_mult(BASE, s)
    right = _add(r_point, _scalar_mult(point, k))
    lx, ly, lz, _ = left
    rx, ry, rz, _ = right
    return (lx * rz - rx * lz) % P == 0 and (ly * rz - ry * lz) % P == 0
