# SM2 + SM4 Interactive Session — Test Runbook

> Branch: `sm2-sm4-backend`
>
> Scope: validate the new GUI-facing `InteractiveSession` layer. Do **not** start frontend/PySide6 work in this test round.

## 1. Pull latest branch

```bash
git fetch origin
git switch sm2-sm4-backend
git pull --ff-only origin sm2-sm4-backend
git status --short
```

Worktree must be clean before testing.

## 2. Use the already validated GmSSL environment

Activate the clean environment created by the backend bootstrap, for example:

```bash
source .venv-sm2-sm4/bin/activate
```

Then verify ABI:

```bash
python tools/patch_gmssl_python_abi.py --check
```

Expected:

```text
ABI CHECK: PASS
sizeof(Sm2Key) = 128
sizeof(Sm4Gcm) = 296
```

## 3. Compile check

```bash
python -m compileall -q \
  src/sm2_sm4_mre/interactive_session.py \
  tests/test_sm2_sm4_interactive_session.py \
  tests/test_sm2_sm4_mre_gmssl_integration.py
```

Expected: exit code 0.

## 4. Headless interactive-session tests

```bash
pytest -q tests/test_sm2_sm4_interactive_session.py
```

Expected:

```text
3 passed
```

These tests use the existing test-only FakeBackend. They validate state-machine and interaction invariants without requiring native crypto.

## 5. Real GmSSL integration tests

```bash
pytest -q -rs tests/test_sm2_sm4_mre_gmssl_integration.py
```

Expected now:

```text
2 passed
0 skipped
```

The second integration test drives `InteractiveSession` through real native:

```text
SM2 keygen
-> select S={u2,u4}
-> generate one K / package_id / IV
-> wrap K for u2
-> wrap K for u4
-> SM4-GCM encrypt payload exactly once
-> assemble .smre without re-encrypting
-> u2 decrypt success
-> u1 NOT_RECIPIENT
-> u1 force-try u2 fails
```

`skip` is not a final pass in the validated environment.

## 6. Run all SM2/SM4 tests

```bash
pytest -q -rs \
  tests/test_sm2_sm4_mre_core.py \
  tests/test_sm2_sm4_mre_package_validation.py \
  tests/test_sm2_sm4_interactive_session.py \
  tests/test_sm2_sm4_mre_gmssl_integration.py
```

Expected current total:

```text
14 passed
0 failed
0 skipped
```

## 7. Specific invariants to inspect

Confirm from tests/code, not only from final pass count:

1. `generate_content_material()` freezes recipient set and selected media.
2. `wrap_for("u2")` and `wrap_for("u4")` use the session's single internally generated SM4 content key.
3. `encrypt_payload()` uses the same content key.
4. `payload_encryption_count == 1` before and after package assembly.
5. `assemble_package()` copies the staged ciphertext; it does not call SM4-GCM encryption again.
6. u2/u4 recovered key fingerprint equals the original session key fingerprint.
7. u1 cannot decrypt normally.
8. u1 force-trying u2's wrapped key fails through real crypto, not UI policy.
9. `reset_broadcast()` removes ephemeral state but preserves user key pairs.
10. no raw SM4 key or SM2 private key is exposed by `SessionSnapshot`.

## 8. Repository cleanliness

After testing:

```bash
git status --short
```

Do not commit generated keys, packages, media outputs, venvs, or test artifacts.

## 9. Report template

```text
## Target
branch:
commit:

## Compile
compileall:

## Headless session
interactive_session tests:

## Real GmSSL
ABI check:
gmssl integration tests:

## Full SM2/SM4 focused suite
result:
skips:

## Invariants
recipient/media freeze:
same K used for SM2 wrap + SM4 payload:
payload_encryption_count remains 1 after assembly:
u2/u4 success:
u1 NOT_RECIPIENT:
u1 force-try failure:
reset preserves user keys:
snapshot exposes no raw secrets:

## Repository state
git status --short:

## Conclusion
PASS / FAIL
```

If any test fails, return the full traceback and do not start frontend implementation.
