# SM2 + SM4 Workbench v0.3.1 — i18n regression runbook

This pass is intentionally small. It verifies the English punctuation fix in the principle/live-state inspector and confirms that the validated cryptographic workflows did not regress.

## Target

Use branch `sm2-sm4-backend` and the latest commit containing this runbook.

## Environment

Reuse the already validated WSL2 environment:

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check
```

The ABI check must pass.

## Compile

```bash
python -m compileall -q \
  src/sm2_sm4_mre \
  src/sm2_sm4_workbench \
  tests/test_sm2_sm4_principle_inspector.py
```

## Focused regression

```bash
QT_QPA_PLATFORM=offscreen \
pytest -q tests/test_sm2_sm4_principle_inspector.py
```

Expected:

```text
4 passed
```

The new regression assertion requires English output to contain ASCII labels such as `Role:` and to contain zero full-width colons `：`.

## Full focused suite

Run the same focused suite used for v0.3, including all existing SM2/SM4, interactive-session, Qt, sender-canvas, receiver-canvas, and principle-inspector tests.

Expected total after this change:

```text
34 passed
0 failed
0 skipped
```

## Manual English check

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v031-en \
  --lang en_US
```

Generate a session far enough to inspect at least `K` and `Broadcast package`, then open `Principle / live state`.

Required:

- `Role:`
- `Inputs:`
- `Core relation / operation:`
- `Outputs:`
- `Live state:`
- `Security boundary:`
- no `：`
- no Chinese explanatory text

## Manual Chinese sanity check

Launch without `--lang en_US` and confirm Chinese labels still use natural full-width punctuation such as `作用：` and render normally.

## Repository policy

Do not modify, commit, or push during validation. If any failure occurs, return the failing command, traceback/assertion, minimal reproduction, and screenshot when relevant.

## Report template

```text
## Target
branch:
commit:
worktree:

## Automated
compileall:
principle inspector tests:
focused total:
skips:

## English i18n
ASCII colons:
full-width colon count:
CJK leakage:

## Chinese sanity
Chinese punctuation/rendering:

## Repository state
git status --short:
commit/push performed:

## Conclusion
PASS / FAIL
```
