# SM2 + SM4 Multi-Recipient Hybrid Encryption — Backend v1

## Scope

This backend replaces the abandoned Matrix-Commitment/CHW25 direction for the second course scheme.
It intentionally implements **multi-recipient hybrid encryption**, not a constant-size-header broadcast-encryption primitive.

For a recipient set `S`, the media is encrypted **once** with a fresh SM4-GCM key `K`. `K` is then independently wrapped with each recipient's SM2 public key. Therefore the media ciphertext is single-copy while the key header grows as `O(|S|)`.

## Cryptographic flow

1. Each user owns an SM2 key pair `(PK_i, SK_i)`.
2. Sender generates a fresh 16-byte SM4 content key `K`, 16-byte package ID, and fresh GCM IV.
3. For each `i in S`, build a compact envelope containing `(package_id, user_id, K)` and compute `E_i = SM2.Enc(PK_i, envelope_i)`.
4. Build a canonical JSON manifest. The exact canonical bytes are used as GCM AAD.
5. Encrypt the media once with SM4-GCM: `C_media || tag = Enc(K, IV, media, AAD)`.
6. Store one `.smre` ZIP container containing the manifest, one wrapped-key entry per authorized user, and one encrypted payload.
7. An authorized user decrypts their own `E_i`, verifies the envelope binding, then uses recovered `K` for SM4-GCM. Plaintext is released only after authentication succeeds.
8. A non-recipient has no wrapped-key entry. For teaching, `force_try_wrapped_key()` can deliberately apply the wrong SM2 private key to another user's envelope; the real backend rejects it (or, defensively, GCM rejects any wrong key before plaintext is released).

## Package layout

```text
package.smre (ZIP, stored/no compression)
├── manifest.json
├── wrapped_keys/
│   ├── 000000.bin
│   └── 000001.bin
└── payload.bin
```

`manifest.json` is canonicalized with UTF-8, sorted keys, and compact separators before being used as GCM AAD. Changing recipients, filename, size, MIME, IV, or wrapped-key entry mapping therefore changes the AAD and breaks authentication for a correctly recovered content key.

## Why the envelope is not raw `K`

The SM2 plaintext is a small binary `KeyEnvelope`:

```text
magic(4) | version(1) | package_id(16) | user_id_len(1) | user_id | SM4_key(16)
```

This binds a wrapped key to both the package and the intended user. It also keeps the SM2 plaintext short, which matches the intended use of public-key encryption for key material.

## Production backend

`src/sm2_sm4_mre/gmssl_backend.py` targets the official GmSSL-Python binding:

- `Sm2Key.generate_key()`
- encrypted private-key PEM import/export
- public-key PEM import/export
- `Sm2Key.encrypt()` / `decrypt()`
- `rand_bytes()`
- `Sm3()`
- streaming `Sm4Gcm.update()` / `finish()`

GmSSL-Python uses `ctypes`; install the native GmSSL shared library first, then:

```bash
pip install gmssl-python
```

On Ubuntu/WSL, after installing GmSSL under `/usr/local/lib`, run `sudo ldconfig` if the shared library is not found.

## CLI smoke test

```bash
# Generate four users
python -m src.sm2_sm4_mre keygen --user u1 --password pass-u1 --key-root keys
python -m src.sm2_sm4_mre keygen --user u2 --password pass-u2 --key-root keys
python -m src.sm2_sm4_mre keygen --user u3 --password pass-u3 --key-root keys
python -m src.sm2_sm4_mre keygen --user u4 --password pass-u4 --key-root keys

# Broadcast to S={u2,u4}
python -m src.sm2_sm4_mre encrypt \
  --input demo.png \
  --output demo.smre \
  --recipient u2=keys/u2/sm2_public.pem \
  --recipient u4=keys/u4/sm2_public.pem

# Authorized recipient
python -m src.sm2_sm4_mre decrypt \
  --package demo.smre \
  --user u2 \
  --private-key keys/u2/sm2_private.pem \
  --password pass-u2 \
  --output recovered.png

# Negative path: u1 deliberately attacks u2's wrapped key
python -m src.sm2_sm4_mre force-try \
  --package demo.smre \
  --attacker-user u1 \
  --attacker-private-key keys/u1/sm2_private.pem \
  --password pass-u1 \
  --target-recipient u2 \
  --output should-not-exist.png
```

## Backend/API design for the later interactive UI

The UI must call real backend operations rather than replaying a canned animation. The important granular APIs already exist:

- `generate_user_keys()`
- `generate_encryption_material()`
- `wrap_content_key()`
- `unwrap_content_key()`
- `encrypt_media()` / `decrypt_media()`
- `force_try_wrapped_key()`
- `inspect_package()`

The later frontend can expose these as direct-manipulation actions (e.g. drag a generated content-key object onto `PK_u2` to trigger the real `wrap_content_key()` call).

## Security/engineering notes

- Private keys are stored as password-protected PEM through GmSSL.
- The default trace never exposes the raw private key or raw SM4 content key; it records SM3 fingerprints instead.
- Decryption writes to a temporary `.part` file and only atomically releases plaintext after GCM authentication succeeds.
- Ciphertext is stored without ZIP compression because encrypted data is incompressible.
- This is course/research software. It is not a production key-management system.
