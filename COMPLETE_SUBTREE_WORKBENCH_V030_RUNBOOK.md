# Complete Subtree Unified v0.3 Validation

Branch:

```text
complete-subtree-unified
```

This milestone adds a Principle / live state tab to the Complete Subtree
PySide6 workbench. The cryptographic backend remains unchanged.

## Validate

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check

find src/complete_subtree_mre src/complete_subtree_workbench   -type d -name __pycache__ -prune -exec rm -rf {} +

python -W error::SyntaxWarning -m compileall -f -q   src/complete_subtree_mre   src/complete_subtree_workbench   tests/test_complete_subtree_principle_inspector.py
```

Expected: exit 0 and no warning output.

Run:

```bash
QT_QPA_PLATFORM=offscreen pytest -q   tests/test_complete_subtree_unified_core.py   tests/test_complete_subtree_unified_session.py   tests/test_complete_subtree_unified_gmssl.py   tests/test_complete_subtree_workbench.py   tests/test_complete_subtree_compile_clean.py   tests/test_complete_subtree_principle_inspector.py
```

Theoretical target:

```text
20 passed
0 failed
0 skipped
```

## Manual WSLg scenario

```bash
python -m src.complete_subtree_workbench --n 8
```

Use:

```text
N=8
R={u3}
ST(R)={v1,v2,v5,v10}
Cover={v3,v4,v11}
```

Generate K and wrap v3, v4, v11.

The Principle / live state tab must explain:

- R
- ST(R)
- Cover
- L_i
- K
- E[L_i](K)
- Receiver path

Each page should show role, inputs, formula, outputs, live state and security
boundary.

Tree click mapping:

```text
wrapped Cover node -> E[L_i](K)
unwrapped Cover node -> Cover
Steiner node -> ST(R)
ordinary node -> L_i
```

Receiver checks:

```text
u4 -> SUCCESS via v11
u3 -> REVOKED
u3 force-try v3 -> HEADER_UNWRAP_FAILED
```

The Receiver path page must reflect each real result. The successful receiver K
fingerprint must match the sender K fingerprint. Failed paths must show no
recovered K fingerprint.

The inspector must display only safe projections: fingerprints, node/user IDs,
paths and status values. It must not display raw K or raw node-key bytes.

English:

```bash
python -m src.complete_subtree_workbench --n 8 --lang en_US
```

Check that inspector labels use English ASCII punctuation and contain no Chinese
UI text.

Finally rerun the frozen SM2+SM4 focused suite. Expected baseline remains:

```text
43 passed
0 failed
0 skipped
```

Do not modify or push from the validator.
