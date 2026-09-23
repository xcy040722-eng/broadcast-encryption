# SM2 + SM4 PySide6 Workbench v0.1 — Test Runbook

> Branch: `sm2-sm4-backend`
>
> Scope: validate the first functional PySide6 workbench. Do **not** redesign visuals yet.

## 1. Pull latest branch

```bash
git fetch origin
git switch sm2-sm4-backend
git pull --ff-only origin sm2-sm4-backend
git status --short
```

Worktree must be clean before testing.

## 2. Use the already validated WSL environment

Recommended verified environment:

```text
WSL2 Ubuntu 24.04
GmSSL native commit 24ae4827
gmssl-python==2.2.2
repository ABI patch applied
```

Activate the clean venv created by the backend bootstrap, then install the UI dependency:

```bash
source .venv-sm2-sm4/bin/activate
python -m pip install -r requirements-sm2-sm4-ui.txt
```

Check the native ABI first:

```bash
python tools/patch_gmssl_python_abi.py --check
```

Expected:

```text
ABI CHECK: PASS
sizeof(Sm2Key) = 128
sizeof(Sm4Gcm) = 296
```

## 3. Compile

```bash
python -m compileall -q \
  src/sm2_sm4_mre \
  src/sm2_sm4_workbench \
  tests/test_sm2_sm4_workbench_smoke.py \
  tests/test_sm2_sm4_workbench_gmssl.py
```

Expected: exit 0.

## 4. Headless Qt functional tests

```bash
QT_QPA_PLATFORM=offscreen \
pytest -q tests/test_sm2_sm4_workbench_smoke.py
```

Expected:

```text
3 passed
```

These tests use the existing FakeBackend only to validate the GUI/controller interaction contract. They verify:

- public workbench actions mutate `InteractiveSession`, not fake UI-only state;
- one session key is wrapped for u2/u4;
- payload encryption count remains exactly 1 after package assembly;
- authorized u2/u4 succeed;
- u1 is denied;
- force-try fails;
- raw SM4 key does not appear in rendered UI text;
- reset clears broadcast state but preserves users.

## 5. Real GmSSL through PySide6 action methods

```bash
QT_QPA_PLATFORM=offscreen \
pytest -q -rs tests/test_sm2_sm4_workbench_gmssl.py
```

Expected in the validated environment:

```text
1 passed
0 skipped
```

A skip is not an acceptance result for this machine.

This test performs:

```text
PySide6 WorkbenchWindow method
        ↓
InteractiveSession
        ↓
real GmSSL SM2 / SM4-GCM
```

It covers real SM2 keygen, real SM2 wrapping, real SM4-GCM media encryption, package assembly, authorized decryption, non-recipient denial, and wrong-private-key force-try.

## 6. Focused full suite

```bash
QT_QPA_PLATFORM=offscreen \
pytest -q -rs \
  tests/test_sm2_sm4_mre_core.py \
  tests/test_sm2_sm4_mre_package_validation.py \
  tests/test_sm2_sm4_interactive_session.py \
  tests/test_sm2_sm4_mre_gmssl_integration.py \
  tests/test_sm2_sm4_workbench_smoke.py \
  tests/test_sm2_sm4_workbench_gmssl.py
```

Expected after adding the v0.1 workbench tests:

```text
18 passed
0 failed
0 skipped
```

If the exact count differs because a test was legitimately added later, report the per-file counts; do not hide skips.

## 7. Manual WSLg launch

Do not set `QT_QPA_PLATFORM=offscreen` for this step.

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-demo
```

Expected: a light PySide6 window opens through WSLg.

Manual interaction:

1. Generate SM2 keys for u1, u2, u3, u4. Use disposable demo passwords.
2. Choose a real small PNG/JPG/bin file.
3. Check `Recipient` for u2 and u4.
4. Click `Generate content material`.
5. Drag the SM4 content-key card to u2. A real wrapped key `E[u2]` must appear.
6. Drag the same card to u4. `E[u4]` must appear.
7. Drag the same card to `SM4-GCM engine`. Payload encryption must complete.
8. `Assemble .smre package` becomes enabled. Save the package.
9. Receiver lab: choose u2 and decrypt. Output must match original.
10. Receiver lab: choose u1 and decrypt. Result must be `NOT_RECIPIENT` and no output plaintext should survive.
11. Receiver lab: choose u1, target u2, then `Force try wrong private key`. Expected real cryptographic failure (`SM2_UNWRAP_FAILED` on the currently validated GmSSL build).

## 8. What to inspect manually

This checkpoint is about functional interaction, not aesthetics. Report whether:

- recipient checkboxes really alter the session set before material generation;
- after material generation, recipients/media/keygen controls are frozen until reset;
- the content-key object is draggable only after real material exists;
- drag-to-user produces a wrapped-key object only after `session.wrap_for()` succeeds;
- drag-to-engine performs the real `session.encrypt_payload()` once;
- package assembly does not increment `payload_encryption_count`;
- receiver results come from real backend status values;
- no raw SM4 key/private-key material is rendered in the window/event log;
- Reset preserves SM2 users and clears the broadcast.

## 9. Failure rules

If Qt fails to start under WSLg, report:

```text
$DISPLAY
$WAYLAND_DISPLAY
$XDG_RUNTIME_DIR
python -c "import PySide6; print(PySide6.__version__)"
```

Do not switch the app to a web frontend or move GmSSL to Windows as a workaround during this checkpoint.

If the real GmSSL UI integration test skips, fix the environment first; do not count it as PASS.

If a code defect is found, return the failing test, traceback, minimal reproduction and suggested minimal fix. Do not redesign the UI.

## 10. Report template

```text
## Target
branch:
commit:

## Environment
OS:
Python:
PySide6:
GmSSL native:
GmSSL-Python:
ABI check:

## Tests
compileall:
workbench smoke:
workbench real GmSSL:
focused full suite:
skips:

## Manual WSLg
window launch:
keygen u1-u4:
select S={u2,u4}:
generate material:
drag K -> u2:
drag K -> u4:
drag K -> SM4-GCM:
assemble package:
u2 decrypt:
u1 normal decrypt:
u1 force-try u2:
reset:

## Interaction invariants
media/recipient freeze:
payload_encryption_count:
raw secret exposure:
real backend statuses:

## Repository state
git status --short:

## Conclusion
PASS / FAIL
```

Do not commit/push changes during the test pass unless explicitly asked.
