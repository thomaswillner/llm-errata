# Production cryptography qualification

**Assessment date:** 2026-08-12

**Repository verdict:** `NOT_PROD_READY`

**Readiness gate:** G3 remains `BLOCKED`

## Decision

Do not replace the reference signer yet.

PyCA `cryptography` and libsodium are both technically credible Ed25519
backends, but the evidence reviewed here does not prove the complete G3
criterion: an audited, side-channel-resistant production signer plus an
independent review of key generation, custody, rotation, delegation, recovery,
revocation, compromise handling, and deployment.

The leading path is to qualify libsodium 1.0.22 through a small Python binding
or an existing maintained binding, subject to current-version delta review and
the lifecycle design below. PyCA remains a useful interoperability oracle, not
the selected G3 implementation, because its current documentation explicitly
states that the project has not undergone an external audit.

## Evidence collected

### Reference baseline

The repository's `prototype/ed25519.py` is pure Python. It reproduces the
checked RFC 8032 vectors, but Python big-integer operations are not a suitable
side-channel boundary for production signing. The `Signer` protocol in
`prototype/signing.py` isolates replacement from controller and receipt logic.

### Verification refusal evidence

The stronger security-relevant reference evidence is not that five valid
signatures succeed; it is that invalid inputs fail closed. The checked suite
demonstrates refusal of:

- a non-canonical scalar (`S >= L`), preventing signature malleability;
- malformed public-key and signature lengths, returning `False` rather than
  raising into an ambiguous caller path;
- a tampered message;
- a tampered signature; and
- a wrong public key.

The suite also refuses malformed signature strings at the `VerificationKey`
seam and refuses a seed of the wrong length. These are observed reference-code
properties in `tests/test_ed25519.py`, not claims about a future production
binding. They do not prove constant-time behavior, resistance to side channels,
safe key lifecycle, current-library audit status, or G3.

### PyCA `cryptography`

| Item | Observed evidence |
|---|---|
| Installed test version | 49.0.0 |
| Current PyPI release | 50.0.0 |
| Python constraint | `!=3.9.0,!=3.9.1,>=3.9` |
| Licence | Apache-2.0 OR BSD-3-Clause |
| Local backend | OpenSSL 4.0.1; FIPS mode disabled |
| Compatibility | All five checked RFC 8032 vectors produced identical raw public keys and signatures; verification passed |
| Security boundary | PyCA delegates cryptographic operations to OpenSSL |
| Audit status | PyCA documentation says its code and documentation have not undergone an external audit |

Compatibility proves that existing 32-byte seeds, 32-byte public keys, and
64-byte signatures can retain their wire representation. It does not prove
constant-time behavior, safe key custody, a supported deployment build, or G3.

### libsodium

| Item | Observed evidence |
|---|---|
| Local library | 1.0.22 |
| Current release | 1.0.22, published 2026-04-09 |
| Candidate API | `crypto_sign_seed_keypair`, `crypto_sign_detached`, and `crypto_sign_verify_detached` |
| Wire model | Single-part API is Ed25519; seed, public key, and detached signature sizes match the existing profile |
| Published assessment | Independent assessment covered 1.0.12 and 1.0.13, including Ed25519 signatures, and reported no major vulnerabilities in reviewed versions |
| Current-version gap | The 2017 assessment is not an audit of 1.0.22; a documented delta and build-specific review are still required |
| Security maintenance | 1.0.22 post-dates the fix for CVE-2025-69277; this fact does not replace vulnerability scanning or review |

The assessment makes libsodium the stronger audited-lineage candidate. It does
not justify describing 1.0.22 or an application binding as independently
audited without reviewing changes since 1.0.13 and the exact production build.

### Maintainer-provided pure-Python comparison

In response to the review request, libsodium maintainer Frank Denis pointed to
[`jedisct1/ed25519.py`](https://github.com/jedisct1/ed25519.py) at commit
`67902d339ea47418a60fb7684255b81bc4f6d46e`. Its documentation describes RFC
8032 vectors, canonical and small-order refusal, batch verification, and
optional randomized signing countermeasures. This is relevant design and
compatibility evidence, but it does not change the production decision: it is
still pure Python, no independent audit or exact-build side-channel review was
found, and no repository licence file was detected. It may be used as a
comparison oracle after its licensing status is clarified; it is not the G3
production backend.

## Required production design

A qualifying implementation must preserve these contracts:

1. Use raw Ed25519 seeds and public keys without changing canonical payload
   bytes, signatures, receipt schema, or key identifiers.
2. Generate production seeds from an operating-system CSPRNG or approved key
   service. Test fixture labels may remain deterministic; production labels
   must never be converted into keys.
3. Keep private keys outside receipts, logs, command output, test artifacts,
   and repository files. Define process-memory exposure and zeroization limits.
4. Bind every erratum and receipt to an active key identifier and declared key
   validity interval.
5. Represent rotation, delegation, revocation, and recovery as authenticated,
   sequenced lifecycle events. An importer must fail closed on unknown,
   expired, revoked, conflicting, or rollback key state.
6. Preserve the old verification key for historical receipts while preventing
   it from authorizing new events after its terminal sequence.
7. Define compromise recovery independently from ordinary rotation. Recovery
   must identify its trust anchor and cannot be authorized only by the
   compromised key.
8. Pin the library and binding version, record linked library identity, scan
   known vulnerabilities, and reproduce RFC plus repository receipt vectors in
   every supported build.

## Independent review request

A qualifying reviewer should answer, against an exact commit and build:

- Does the chosen Ed25519 path avoid secret-dependent control flow and memory
  access for the supported targets, or clearly identify any residual channel?
- Does the binding preserve raw seed/public/signature compatibility and reject
  malformed or non-canonical signatures consistently?
- Can any rotation, delegation, recovery, replay, sequence-gap, or key-ID
  ambiguity authorize an attacker or strand legitimate historical evidence?
- Are private-key generation, storage, process exposure, backup, recovery,
  destruction, logging, and incident procedures explicit and testable?
- Are library, binding, compiler, platform, and vulnerability evidence pinned
  closely enough to support the production claim?

The report must disclose reviewer identity, relationship and conflicts, date,
reviewed commit, build inputs, scope, tests, findings, residual risks, and
verdict. Invitation, compatibility testing, CI, or this internal assessment is
not independent security evidence.

## Reproduction record

The compatibility probe loaded the five RFC 8032 vectors already published in
`tests/test_ed25519.py`, constructed PyCA private keys from each 32-byte seed,
and compared raw public keys and signatures with literal expected values. It
then verified every signature with the corresponding raw public key. This is a
wire-compatibility oracle; the refusal-path tests above are the stronger
security-relevant evidence about the current reference verifier.

Observed result:

```text
pyca_rfc8032_compatibility=PASS vectors=5
installed_cryptography=49.0.0
openssl_version=OpenSSL 4.0.1 9 Jun 2026
fips_enabled=False
```

This record is local compatibility evidence only. A future implementation must
turn the probe into checked-in tests and run it across every declared platform
before the backend changes.
