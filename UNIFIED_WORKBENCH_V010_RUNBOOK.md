# Unified Broadcast Encryption Workbench v0.1 — Validation Runbook

Target branch:

```text
complete-subtree-unified
```

This milestone does **not** merge the two cryptographic constructions into one
algorithm. It gives the finished modules one common PySide6 entry point:

```text
Broadcast Encryption & Multi-Recipient Cryptography Workbench
├── Complete Subtree
└── SM2 + SM4
```

The two modules preserve their own verified state machines and cryptographic
semantics.

## New launcher

```text
src/broadcast_encryption_workbench/
  __init__.py
  __main__.py
  launcher.py

tests/test_unified_launcher.py
```

## Launch

Chinese default:

```bash
python -m src.broadcast_encryption_workbench
```

English:

```bash
python -m src.broadcast_encryption_workbench --lang en_US
```

Optional:

```bash
python -m src.broadcast_encryption_workbench   --workspace /tmp/broadcast-encryption-demo   --cs-users 8
```

## Design boundary

The launcher must not execute any cryptographic operation on startup.

It may only open:

- `CompleteSubtreeWorkbenchWindow`
- `DefenseWorkbenchWindow`

The launcher passes a common language to both modules, and passes its workspace
only to the SM2+SM4 workbench.

## Compile

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check

python -W error::SyntaxWarning -m compileall -f -q   src/broadcast_encryption_workbench   tests/test_unified_launcher.py
```

Expected:

```text
exit 0
warning = 0
```

## Launcher automated tests

```bash
QT_QPA_PLATFORM=offscreen pytest -q tests/test_unified_launcher.py
```

Expected theoretical result:

```text
5 passed
0 failed
0 skipped
```

The tests verify:

- launcher starts with zero child workbenches;
- both module cards are present;
- English launcher has zero CJK/full-width-colon leakage;
- Complete Subtree receives the configured language and user count;
- SM2+SM4 receives the configured language and workspace;
- invalid non-power-of-two CS user counts are rejected.

## Existing module regression

Run the Complete Subtree frozen suite:

```bash
QT_QPA_PLATFORM=offscreen pytest -q   tests/test_complete_subtree_unified_core.py   tests/test_complete_subtree_unified_session.py   tests/test_complete_subtree_unified_gmssl.py   tests/test_complete_subtree_workbench.py   tests/test_complete_subtree_compile_clean.py   tests/test_complete_subtree_principle_inspector.py   tests/test_complete_subtree_result_presenter.py   tests/test_complete_subtree_defense_guide.py
```

Expected:

```text
30 passed
0 failed
0 skipped
```

Run the frozen SM2+SM4 suite:

```bash
QT_QPA_PLATFORM=offscreen pytest -q   tests/test_sm2_sm4_mre_core.py   tests/test_sm2_sm4_mre_package_validation.py   tests/test_sm2_sm4_interactive_session.py   tests/test_sm2_sm4_mre_gmssl_integration.py   tests/test_sm2_sm4_workbench_smoke.py   tests/test_sm2_sm4_workbench_gmssl.py   tests/test_sm2_sm4_workbench_qt6_regressions.py   tests/test_sm2_sm4_relation_canvas.py   tests/test_sm2_sm4_receiver_canvas.py   tests/test_sm2_sm4_principle_inspector.py   tests/test_sm2_sm4_result_presenter.py   tests/test_sm2_sm4_defense_guide.py
```

Expected:

```text
43 passed
0 failed
0 skipped
```

Combined theoretical total:

```text
78 passed
0 failed
0 skipped
```

## Manual launcher validation

Launch Chinese mode:

```bash
python -m src.broadcast_encryption_workbench
```

The launcher should show two cards.

### Complete Subtree card

It must describe:

```text
classic broadcast revocation
R -> ST(R) -> Cover
real GmSSL SM4-GCM E[L_i](K)
SUCCESS / REVOKED / HEADER_UNWRAP_FAILED
```

Click the card button and confirm the already-validated Complete Subtree
workbench opens in Chinese. Run a quick `R={u3}` scenario if desired.

### SM2 + SM4 card

It must describe:

```text
multi-recipient hybrid encryption
one media ciphertext
per-authorized-user SM2 wrapped K
SUCCESS / NOT_RECIPIENT / SM2_UNWRAP_FAILED
```

Click the card button and confirm the already-validated SM2+SM4 workbench opens
in Chinese and uses the launcher workspace.

Both child windows may remain open at the same time.

## English launcher

```bash
python -m src.broadcast_encryption_workbench --lang en_US
```

Check launcher and both opened child windows:

```text
CJK leakage = 0
full-width colon = 0
```

## Terminology

The launcher must make the distinction visible:

- Complete Subtree = classic tree-based broadcast revocation.
- SM2+SM4 = multi-recipient hybrid encryption / broadcast-style distribution.

Do not describe SM2+SM4 as a constant-header Broadcast Encryption construction.

## Repository boundary

The launcher milestone should add a new top-level UI package and tests. It
should not alter cryptographic backend semantics in either module.

Do not modify, commit, or push from the validator. Report exact counts,
screenshots, and any integration issue.
