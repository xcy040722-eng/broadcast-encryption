# GmSSL-Python ABI Compatibility Note

> Applies to branch `sm2-sm4-backend`.
>
> Read this **before** `SM2_SM4_BACKEND_RUNBOOK.md` when building the real GmSSL environment.

## 1. Why this note exists

During real WSL2/Ubuntu integration testing, the unmodified `gmssl-python==2.2.2` binding successfully imported and completed several crypto calls, but the Python process later terminated with a segmentation fault.

The root cause was a `ctypes` ABI layout mismatch between the Python binding and the tested native GmSSL library.  Two structures used by this project were undersized on the Python side:

| structure | unpatched ctypes | tested native C layout | consequence |
|---|---:|---:|---|
| `Sm2Key` | 96 | 128 | native write may overrun by 32 bytes |
| `Sm4Gcm` | 288 | 296 | native write may overrun by 8 bytes |

This is memory corruption.  A test that prints correct crypto results and crashes only at process shutdown is **not** acceptable.

## 2. Reproducible project profile

This branch freezes the tested environment to:

```text
GmSSL native commit: 24ae4827
GmSSL-Python:         2.2.2
Expected Sm2Key:      128 bytes
Expected Sm4Gcm:      296 bytes
```

`requirements-sm2-sm4.txt` pins the Python binding.  The native commit is pinned by:

```text
scripts/bootstrap_gmssl_wsl.sh
```

## 3. What the project patch changes

The repository contains:

```text
tools/patch_gmssl_python_abi.py
```

It performs only the two compatibility edits required by the current SM2/SM4 backend:

1. append `uint64_t encedlen` to the Python `Sm4Gcm` layout;
2. represent `Sm2Key.public_key` as a 96-byte Jacobian/Z256 point (`X`, `Y`, `Z`, each four `uint64_t`s) so the complete `Sm2Key` layout is 128 bytes.

The script:

- refuses to patch a binding version other than `2.2.2`;
- refuses unexpected source layouts instead of guessing;
- creates `gmssl.py.orig-2.2.2` before modification;
- is idempotent;
- verifies `ctypes.sizeof()` in a **fresh Python process**;
- restores the backup automatically if verification fails.

Apply it with:

```bash
python tools/patch_gmssl_python_abi.py
```

Verify later with:

```bash
python tools/patch_gmssl_python_abi.py --check
```

Expected result:

```text
Sm2Key=128 Sm4Gcm=296
ABI CHECK: PASS
```

## 4. Fail-closed behavior in the project backend

`src/sm2_sm4_mre/gmssl_backend.py` now checks the two ctypes sizes before performing any native crypto operation.

If the layout is unsafe, `GmsslBackend()` raises `BackendUnavailableError` with instructions to apply the patch.  This is deliberate: an ABI mismatch must fail as a normal Python error instead of being allowed to reach native code and possibly corrupt memory.

The real integration test also treats ABI mismatch as a **hard failure**, not a skip.

## 5. Fastest WSL installation path

From the repository root:

```bash
bash scripts/bootstrap_gmssl_wsl.sh
```

The script performs:

```text
install build tools
→ checkout native GmSSL 24ae4827
→ build/test/install native GmSSL
→ create .venv-sm2-sm4
→ install gmssl-python==2.2.2 + pytest
→ apply ABI patch
→ verify ABI in fresh process
→ run real GmSSL integration test
→ run all SM2/SM4 backend tests
```

A successful bootstrap must end with the integration test **passed**, not skipped.

## 6. Manual path

If you follow `SM2_SM4_BACKEND_RUNBOOK.md` manually, insert these commands immediately after `pip install -r requirements-sm2-sm4.txt`:

```bash
python tools/patch_gmssl_python_abi.py
python tools/patch_gmssl_python_abi.py --check
```

Only then execute the real GmSSL integration test.

## 7. Scope of the compatibility patch

The course backend currently uses:

- `Sm2Key` key generation/import/export/encrypt/decrypt;
- `Sm3`;
- `Sm4Gcm`;
- `rand_bytes`.

A separate `Sm2Signature` layout discrepancy was observed during diagnosis, but this project does **not** use SM2 signatures.  This repository therefore does not claim to repair or validate the signature ABI.  If signatures are added later, their native/ctypes layouts must be audited first.

## 8. Upstream status

The compatibility code here is intentionally project-local so the course environment remains reproducible regardless of upstream release timing.

An upstream report should include:

- native GmSSL commit/version;
- gmssl-python version;
- `ctypes.sizeof` vs C `sizeof` evidence;
- minimal reproducer showing delayed process crash;
- both required layout changes;
- confirmation that the patched layout passes SM2 + SM4-GCM round-trip tests.

A draft report is kept in:

```text
docs/gmssl-python-abi-upstream-issue-draft.md
```
