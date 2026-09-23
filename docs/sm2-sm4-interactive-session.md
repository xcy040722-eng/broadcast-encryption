# SM2 + SM4 Interactive Session Layer

## Purpose

`InteractiveSession` is the bridge between the validated SM2/SM4 backend and the future interactive PySide6 workbench.

It **does not** implement any new cryptography. Instead, it exposes the real backend as manual actions so the frontend can map one user gesture to one backend operation.

Core mapping:

```text
UI gesture
   -> InteractiveSession method
   -> existing service/backend call
   -> real GmSSL operation
   -> updated session state
```

The frontend must never reimplement SM2/SM4 logic, synthesize fake cryptographic state, or call the monolithic `encrypt_media()` merely to replay precomputed results.

## State model

The session derives one of these stages:

```text
EMPTY
CONFIGURING
READY_FOR_MATERIAL
MATERIAL_READY
WRAPPING
PAYLOAD_ENCRYPTED
READY_TO_ASSEMBLE
PACKAGE_ASSEMBLED
```

The flow is intentionally only partially ordered after material generation: SM2 key wrapping and SM4 payload encryption may happen in either order. Package assembly requires both to be complete.

## Public actions

```python
session.generate_user_key("u2", "password")
session.set_media(Path("demo.png"))
session.select_recipient("u2")
session.select_recipient("u4")
session.generate_content_material()
session.wrap_for("u2")
session.wrap_for("u4")
session.encrypt_payload()
session.assemble_package(Path("demo.smre"))
session.decrypt_as("u2", "password", Path("recovered.png"))
session.force_try(
    attacker_user_id="u1",
    password="password-u1",
    target_recipient_id="u2",
    output_path=Path("must-not-exist.png"),
)
```

`reset_broadcast()` discards ephemeral broadcast state while preserving generated user key pairs.

## Frozen crypto-state invariant

Once `generate_content_material()` runs, the following values belong to one immutable broadcast state:

- recipient set `S`
- selected media metadata
- package ID
- SM4 content key `K`
- SM4-GCM IV
- canonical manifest/AAD

Therefore recipient selection and media selection are locked until `reset_broadcast()`.

This prevents an interactive UI from visually changing `S` while using a content key/AAD generated for an earlier state.

## Exact-key invariant

A session generates exactly one secret SM4 content key for the broadcast.

That same internal key is used by:

```text
wrap_for(u_i)
    -> SM2.Enc(PK_i, envelope(package_id, user_id, K))

and

encrypt_payload()
    -> SM4-GCM.Enc(K, IV, media, AAD)
```

`assemble_package()` only copies the already encrypted staged payload. It never performs a second SM4 encryption.

`SessionSnapshot.payload_encryption_count` exists specifically so headless/UI tests can assert that the media was encrypted exactly once.

## Safe UI snapshot

The UI should render from `session.snapshot()`.

The snapshot intentionally contains:

- public user IDs
- recipient set
- package ID
- IV
- SM3 fingerprint of `K`
- SM3 fingerprints of wrapped-key ciphertexts
- payload path/size
- package path
- current stage

It does **not** expose the raw SM4 content key or any SM2 private-key material.

For teaching, a key object can be represented visually by its fingerprint/handle rather than displaying secret bytes.

## Receiver tests

After package assembly:

```python
result = session.decrypt_as("u2", "pw-u2", output)
```

calls the already validated `decrypt_media()` path.

The negative-path action:

```python
session.force_try(attacker_user_id="u1", target_recipient_id="u2", ...)
```

calls the real `force_try_wrapped_key()` path. The frontend must allow this action instead of merely disabling the UI for non-recipients.

## Headless acceptance tests

Run:

```bash
pytest -q tests/test_sm2_sm4_interactive_session.py
```

The tests verify:

1. four users can be generated;
2. `S={u2,u4}` is frozen into one session;
3. u2 and u4 each receive a real wrapped-key object;
4. media is encrypted exactly once;
5. package assembly copies staged ciphertext without re-encrypting;
6. u2 and u4 recover byte-identical media;
7. recovered content-key fingerprint equals the original session key fingerprint;
8. u1 receives `NOT_RECIPIENT`;
9. u1 forcing `SK1` against u2's wrapped key fails;
10. illegal state changes are rejected;
11. reset removes ephemeral state while preserving user keys.

Only after these headless tests pass should PySide6 frontend work begin.

## Frontend rule

The intended frontend is an **interactive cryptography workbench**, not a slide/video player.

Examples of the eventual mapping:

```text
click user u2
    -> select_recipient("u2")

drag content-key object onto PK2
    -> wrap_for("u2")

drop media + content-key into SM4 engine
    -> encrypt_payload()

drop E2 + E4 + payload into package object
    -> assemble_package(...)

drag SK2 onto E2
    -> decrypt_as("u2", ...)

drag SK1 onto E2
    -> force_try(attacker="u1", target="u2", ...)
```

Visual animation is feedback for those state changes; it is never the source of truth.
