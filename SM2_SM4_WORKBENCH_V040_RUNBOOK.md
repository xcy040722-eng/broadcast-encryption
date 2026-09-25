# SM2 + SM4 Workbench v0.4.0 validation runbook

This iteration is presentation polish only.  The cryptographic backend, sender
relationship canvas, receiver path, and principle inspector are unchanged.
The new behavior localizes the *primary receiver result text* while preserving
stable machine-readable backend status codes such as `SUCCESS`,
`NOT_RECIPIENT`, and `SM2_UNWRAP_FAILED`.

## Target

Branch:

```text
sm2-sm4-backend
```

Read `git rev-parse HEAD` after pulling and report the exact commit tested.

## Environment

Use the already validated WSL/WSLg environment:

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check
```

The ABI check must pass before any real GmSSL test.

## Automated checks

Compile the touched modules:

```bash
python -m compileall -q \
  src/sm2_sm4_workbench/result_presenter.py \
  src/sm2_sm4_workbench/defense_workbench.py \
  tests/test_sm2_sm4_result_presenter.py
```

Run the new pure presentation tests:

```bash
pytest -q tests/test_sm2_sm4_result_presenter.py
```

Expected:

```text
4 passed
```

Then run the complete focused suite used by the previous validation, plus the
new result-presenter test file.  The previous validated count was 34 tests, so
the expected total is:

```text
38 passed
0 failed
0 skipped
```

## Manual Chinese WSLg validation

Start the default Chinese UI:

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v040
```

Prepare one real package for `S={u2,u4}` exactly as in earlier runbooks.

### Authorized receiver

Decrypt as `u2`.

The right-side receiver result must keep the code:

```text
SUCCESS
```

but the explanation underneath must be Chinese, for example:

```text
授权验证通过：SM2 成功恢复内容密钥，SM4-GCM 解密与认证成功。
```

The bottom status line must also be Chinese while retaining `SUCCESS`.
The recovered plaintext must still equal the source byte-for-byte.

### Non-recipient

Try normal decryption as `u1`.

Expected code:

```text
NOT_RECIPIENT
```

Expected Chinese explanation must explicitly state that the package contains no
`E[u1]` for `u1`.

No plaintext file may survive.

### Wrong-key force try

Set current user to `u1`, force target to `u2`, and run the real force try.

Expected code:

```text
SM2_UNWRAP_FAILED
```

Expected Chinese explanation must identify the logical mismatch:

```text
SK[u1] ... E[u2]
```

No plaintext file may survive.

## English fallback

Start:

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v040-en \
  --lang en_US
```

Repeat at least one success and one failure.  The status codes stay unchanged,
but the explanations must be English and contain no CJK leakage/full-width
colon.

## Important boundary

Do **not** change backend `DecryptStatus` values and do not translate the raw
backend trace itself.  This iteration only changes the primary human-facing
result presentation in the defense workbench.

The relation canvas, receiver-flow canvas, and principle inspector must still
consume the same real backend state as before.

## Report template

```text
## Target
branch:
commit:
worktree:

## Automated
compileall:
result presenter tests:
focused total:
skips:

## Chinese receiver results
u2 SUCCESS text:
u1 NOT_RECIPIENT text:
u1 -> u2 force text:
plaintext safety:

## English fallback
success text:
failure text:
CJK leakage:

## Regression
sender relation canvas:
receiver path:
principle inspector:
real GmSSL round trip:

## Repository state
git status --short:
commit/push performed:

## Conclusion
PASS / FAIL
```
