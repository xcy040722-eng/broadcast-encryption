# Complete Subtree Unified Workbench v0.2 Validation Runbook

Target branch:

```text
complete-subtree-unified
```

This milestone adds the first PySide6 workbench for the rebuilt Complete
Subtree backend.  The verified SM2+SM4 source remains unchanged.

## What should now be unified

Both teaching modules now use:

- Python 3 / PySide6;
- the same native `GmsslBackend`;
- SM4-GCM for symmetric authenticated encryption;
- SM3 fingerprints for safe projection;
- explicit state-driven session methods;
- Chinese-first UI with English fallback;
- direct manipulation rather than a prerecorded animation.

The Complete Subtree algorithm itself remains NNL01-style tree revocation:
`R -> ST(R) -> Cover -> E[L_i](K)`.

## Warning cleanup

The two v0.1 `SyntaxWarning: invalid escape sequence` warnings were also
removed by making the affected mathematical docstrings raw strings.

## New UI files

```text
src/complete_subtree_workbench/
  __init__.py
  __main__.py
  i18n.py
  widgets.py
  tree_canvas.py
  window.py

tests/test_complete_subtree_workbench.py
```

## Automated validation

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check

python -m compileall -q   src/complete_subtree_mre   src/complete_subtree_workbench   tests/test_complete_subtree_unified_core.py   tests/test_complete_subtree_unified_session.py   tests/test_complete_subtree_unified_gmssl.py   tests/test_complete_subtree_workbench.py
```

Expected: exit 0 **and no SyntaxWarning**.

Run:

```bash
QT_QPA_PLATFORM=offscreen pytest -q   tests/test_complete_subtree_unified_core.py   tests/test_complete_subtree_unified_session.py   tests/test_complete_subtree_unified_gmssl.py   tests/test_complete_subtree_workbench.py
```

Theoretical target:

```text
15 passed
0 failed
0 skipped
```

Then rerun the frozen SM2+SM4 focused suite.  Expected baseline:

```text
43 passed
0 failed
0 skipped
```

## WSLg launch

```bash
python -m src.complete_subtree_workbench --n 8
```

English:

```bash
python -m src.complete_subtree_workbench --n 8 --lang en_US
```

## Manual scenario

Use:

```text
N=8
R={u3}
```

1. Check u3 under the left-side revocation set.
2. Click **计算 ST(R) / Cover**.
3. Confirm:
   - ST = v1,v2,v5,v10
   - Cover = v3,v4,v11
   - u3 leaf is red
   - Steiner path is yellow/orange
   - Cover roots are green.
4. Generate K.
5. **Drag the K card** onto v3, v4 and v11 individually.
   Each successful drop must call exactly one real
   `CompleteSubtreeSession.wrap_for_node(node_id)`.
6. Wrapped roots get a dark-green marker and the stage reaches HEADER_READY.
7. Recover as u4:
   - status SUCCESS
   - receiver path v1,v2,v5,v11 highlighted
   - matched node v11
   - receiver K fingerprint equals sender K fingerprint.
8. Recover as u3:
   - status REVOKED
   - path v1,v2,v5,v10 highlighted
   - no matched Cover node
   - no recovered K fingerprint.
9. Select target v3 and force try as u3:
   - HEADER_UNWRAP_FAILED
   - real GmSSL SM4-GCM authentication failure
   - no K fingerprint.

## True QDropEvent

The automated test constructs a real `QDropEvent` using MIME:

```text
application/x-complete-subtree-content-key
```

and drops it at v4.  Confirm that exactly one real session wrap occurs.

## Security boundary

Inspect normal `CsSessionSnapshot` and `CsRecoverTrace`:

- raw broadcast K must not appear;
- raw node keys L_i must not appear;
- only SM3 fingerprints, user/node IDs, stage and status are exposed.

## UI semantics

Colors should communicate:

- red fill: revoked user leaf;
- yellow fill: ST(R);
- green fill: Cover root;
- blue border: current receiver root-to-leaf path;
- dark-green strong border: successful matched Cover node;
- red strong border: failed force-try target.

## Regression boundary

Do not edit:

```text
src/sm2_sm4_mre/
src/sm2_sm4_workbench/
tests/test_sm2_sm4_*
```

This branch may import the frozen SM2+SM4 `LIGHT_STYLE` and
`GmsslBackend`, but must not modify them.

Do not commit or push test-side changes.  Report PASS/FAIL with screenshots and
the exact test counts.
