# SM2 + SM4 Interactive Workbench v0.1

## Purpose

This is the first **functional** PySide6 prototype for the SM2 + SM4 multi-recipient hybrid-encryption project.

The design rule is strict:

```text
mouse / button action
        ↓
WorkbenchWindow public action method
        ↓
InteractiveSession
        ↓
real GmSSL backend
```

The UI must not reproduce SM2/SM4 math, invent fake objects, or precompute a full package and replay it as animation.

Visual polish is deliberately postponed. The current checkpoint asks only whether screen objects correspond to real backend state and whether direct manipulation triggers real crypto operations.

## Runtime architecture

Recommended runtime for v0.1:

```text
Windows 11 host
  └─ WSL2 Ubuntu + WSLg
       └─ one Python process
            ├─ PySide6
            ├─ InteractiveSession
            ├─ GmSSL-Python 2.2.2 (repository ABI patch)
            └─ native GmSSL commit 24ae4827
```

This avoids a Windows-Qt / WSL-GmSSL RPC boundary during the first prototype.

## UI objects

The first prototype exposes six conceptual object types:

1. `UserCard` — user identity, SM2 key-pair readiness, recipient membership, public-key wrap drop target.
2. `ContentKeyCard` — the one real session SM4 key represented only by its SM3 fingerprint.
3. `Media` — the selected real input file.
4. `WrappedKeyChip` — one actual SM2 ciphertext `E_i` created by `session.wrap_for(i)`.
5. `Sm4EngineCard` — drop target that invokes `session.encrypt_payload()`.
6. `PackageCard` — assembles the already-created wrapped keys and encrypted payload into one `.smre` package.

The receiver lab adds real authorized / unauthorized decrypt attempts after package assembly.

## Direct manipulation

After generating content material, the `ContentKeyCard` is draggable using MIME type:

```text
application/x-sm2-sm4-content-key
```

Dropping it on a selected `UserCard` calls:

```python
session.wrap_for(user_id)
```

Dropping it on the SM4-GCM engine calls:

```python
session.encrypt_payload()
```

No raw content-key bytes are inserted into Qt MIME data; the drag contains only a local semantic marker. The real key remains inside `InteractiveSession`.

## Manual workflow

A typical demo is:

```text
Generate SM2 keys for u1-u4
        ↓
Choose media
        ↓
select S={u2,u4}
        ↓
Generate content material
        ↓
drag K → u2        => real SM2 wrap E2
drag K → u4        => real SM2 wrap E4
drag K → SM4-GCM   => real payload encryption
        ↓
Assemble .smre package
        ↓
Receiver lab:
  u2 => SUCCESS
  u4 => SUCCESS
  u1 => NOT_RECIPIENT
  u1 force-try E2 => cryptographic failure
```

## Secret handling

The UI reads `session.snapshot()` for display state. The snapshot contains only the SM3 fingerprint of the SM4 content key, not the raw key.

Generated SM2 private keys remain password-protected PEM files. The workbench keeps passwords only in process memory for keys created during the current UI process so the receiver demo can reuse them without repeated prompts. Passwords are not placed in the snapshot, event log, package, or drag payload.

## Tests

Headless Qt functional test:

```bash
QT_QPA_PLATFORM=offscreen pytest -q tests/test_sm2_sm4_workbench_smoke.py
```

Real GmSSL through the workbench action path:

```bash
QT_QPA_PLATFORM=offscreen pytest -q -rs tests/test_sm2_sm4_workbench_gmssl.py
```

The real integration test must not be counted as a pass when GmSSL is absent. In the validated WSL environment it should run, not skip.

## Not in v0.1

The following are intentionally deferred:

- polished research/PPT visual language;
- animation choreography;
- formula/source drawers;
- image/video thumbnail preview;
- Tamper Lab;
- draggable wrapped-key/package composition;
- responsive layout refinement;
- packaging as a standalone Windows executable.

First prove the real interaction path. Then redesign the visuals around the working behavior.
