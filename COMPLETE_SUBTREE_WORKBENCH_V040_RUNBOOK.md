# Complete Subtree Unified v0.4 — Defense Polish Validation

Target branch:

```text
complete-subtree-unified
```

This milestone freezes the v0.3 principle layer and adds two presentation-only
features:

1. localized receiver result presentation;
2. a state-driven manual defense guide.

No Complete Subtree cryptographic backend behavior is changed.

## New / changed files

```text
src/complete_subtree_workbench/result_presenter.py
src/complete_subtree_workbench/defense_guide.py
src/complete_subtree_workbench/window.py

tests/test_complete_subtree_result_presenter.py
tests/test_complete_subtree_defense_guide.py
tests/test_complete_subtree_workbench.py

COMPLETE_SUBTREE_PROJECT_GUIDE.md
```

## Compile

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check

find src/complete_subtree_mre src/complete_subtree_workbench   -type d -name __pycache__ -prune -exec rm -rf {} +

python -W error::SyntaxWarning -m compileall -f -q   src/complete_subtree_mre   src/complete_subtree_workbench   tests/test_complete_subtree_result_presenter.py   tests/test_complete_subtree_defense_guide.py
```

Expected:

```text
exit 0
warning = 0
```

## Focused suite

```bash
QT_QPA_PLATFORM=offscreen pytest -q   tests/test_complete_subtree_unified_core.py   tests/test_complete_subtree_unified_session.py   tests/test_complete_subtree_unified_gmssl.py   tests/test_complete_subtree_workbench.py   tests/test_complete_subtree_compile_clean.py   tests/test_complete_subtree_principle_inspector.py   tests/test_complete_subtree_result_presenter.py   tests/test_complete_subtree_defense_guide.py
```

Theoretical target:

```text
30 passed
0 failed
0 skipped
```

## Chinese UI

Launch:

```bash
python -m src.complete_subtree_workbench --n 8
```

Use the standard scenario:

```text
R={u3}
ST(R)={v1,v2,v5,v10}
Cover={v3,v4,v11}
```

After Header Ready, the guide should ask for:

```text
u4 SUCCESS
u3 REVOKED
u3 -> v3 HEADER_UNWRAP_FAILED
```

Verify receiver result text is localized while status codes remain unchanged.

Expected examples:

```text
SUCCESS
授权验证通过：u4 的路径命中 Cover 节点 v11，并成功恢复广播内容密钥 K。

REVOKED
撤销生效：u3 的根到叶路径未命中任何 Cover 节点，因此无法获得可用于恢复 K 的 Header 密钥。

HEADER_UNWRAP_FAILED
错误路径密钥：L[10] 无法解开 E[L3](K)，SM4-GCM 认证失败。
```

The bottom status line must use the same localized explanation.

## Defense guide

The yellow guide is read-only presentation logic. It must not call any session
mutation method.

Expected progression:

```text
CONFIGURING
-> choose R={u3}

COVER_READY
-> generate the one K

MATERIAL_READY / WRAPPING
-> drag K to remaining Cover roots

HEADER_READY, no result
-> u4 SUCCESS, u3 REVOKED, u3 -> v3 force try

after SUCCESS
-> guide u3 recovery

after REVOKED
-> guide u3 -> v3 force try

after HEADER_UNWRAP_FAILED
-> core demo complete; explain principle pages and compare with SM2+SM4
```

## English fallback

Launch:

```bash
python -m src.complete_subtree_workbench --n 8 --lang en_US
```

Verify receiver result, status line, guide and principle inspector contain:

```text
CJK leakage = 0
full-width colon = 0
```

Machine status names such as `SUCCESS`, `REVOKED`, and
`HEADER_UNWRAP_FAILED` remain unchanged.

## Regression

Rerun the frozen SM2+SM4 focused suite.

Expected:

```text
43 passed
0 failed
0 skipped
```

Confirm no source diff in:

```text
src/sm2_sm4_mre/
src/sm2_sm4_workbench/
tests/test_sm2_sm4_*
```

Do not modify, commit, or push from the validator.
