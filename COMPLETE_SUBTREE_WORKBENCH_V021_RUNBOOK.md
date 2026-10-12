# Complete Subtree Unified Workbench v0.2.1 Validation Runbook

Target branch:

```text
complete-subtree-unified
```

This patch fixes the only v0.2 acceptance failure: two invalid-escape
`SyntaxWarning` messages in Complete Subtree mathematical docstrings.

No cryptographic behavior, state machine, UI behavior, or SM2+SM4 source is
changed.

## Patch

Changed:

```text
src/complete_subtree_mre/cover.py
src/complete_subtree_mre/service.py
```

The affected mathematical docstrings are now raw strings.

Added regression test:

```text
tests/test_complete_subtree_compile_clean.py
```

The regression test recompiles both source files with `SyntaxWarning` promoted
to an exception, so the warning cannot silently reappear.

## Validate environment

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check
```

Expected:

```text
sizeof(Sm2Key)=128
sizeof(Sm4Gcm)=296
```

## Force a clean compile

Delete cached bytecode first:

```bash
find src/complete_subtree_mre src/complete_subtree_workbench -type d -name __pycache__ -prune -exec rm -rf {} +
```

Then force recompilation:

```bash
python -W error::SyntaxWarning -m compileall -f -q   src/complete_subtree_mre   src/complete_subtree_workbench
```

Expected:

```text
exit 0
no SyntaxWarning
no warning output
```

## Complete Subtree focused tests

```bash
QT_QPA_PLATFORM=offscreen pytest -q   tests/test_complete_subtree_unified_core.py   tests/test_complete_subtree_unified_session.py   tests/test_complete_subtree_unified_gmssl.py   tests/test_complete_subtree_workbench.py   tests/test_complete_subtree_compile_clean.py
```

Expected theoretical result:

```text
16 passed
0 failed
0 skipped
```

The existing v0.2 manual WSLg scenario remains unchanged:

```text
N=8
R={u3}
ST(R)={v1,v2,v5,v10}
Cover={v3,v4,v11}
u4 -> SUCCESS via v11
u3 -> REVOKED
u3 force-try v3 -> HEADER_UNWRAP_FAILED
```

## SM2+SM4 regression

Rerun the frozen focused suite.

Expected:

```text
43 passed
0 failed
0 skipped
```

## Repository boundary

Confirm the patch does not modify:

```text
src/sm2_sm4_mre/
src/sm2_sm4_workbench/
tests/test_sm2_sm4_*
```

Do not modify, commit, or push from the validator.

If all checks pass, mark Complete Subtree Unified Workbench v0.2.1 PASS and
freeze the v0.2 UI behavior before starting the principle-inspector milestone.
