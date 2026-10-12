# Complete Subtree Unified v0.1 Validation Runbook

Target branch:

```text
complete-subtree-unified
```

This milestone rebuilds Complete Subtree on the same engineering foundation as
the frozen SM2+SM4 workbench.  It does **not** replace or modify the verified
SM2+SM4 backend.

## Design boundary

Paper-faithful Complete Subtree pieces:

- full binary tree with N=2^h leaves;
- one independent long-lived node key L_i per tree node;
- receiver u_i gets the keys on its root-to-leaf path;
- ST(R) and hanging-subtree cover;
- one header entry per cover root;
- authorized receiver path intersects exactly one cover root;
- revoked receiver path intersects none.

Unified engineering adaptation:

- node keys and broadcast content key K are 128-bit, matching SM4;
- NNL01 abstract E_L(K) is instantiated with **SM4-GCM via the same
  GmSSLBackend** already used by the SM2+SM4 project;
- SM3 fingerprints are used for safe UI/trace projection;
- raw L_i and raw K never appear in CsSessionSnapshot/CsRecoverTrace;
- a wrong receiver path key can be force-tried against a cover entry and must
  fail at SM4-GCM authentication.

## Files

```text
src/complete_subtree_mre/
  tree.py
  cover.py
  types.py
  errors.py
  service.py
  interactive_session.py

tests/
  test_complete_subtree_unified_core.py
  test_complete_subtree_unified_session.py
  test_complete_subtree_unified_gmssl.py
```

## Environment

Use the already verified GmSSL environment:

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check
```

Expected ABI:

```text
sizeof(Sm2Key)=128
sizeof(Sm4Gcm)=296
```

## Compile

```bash
python -m compileall -q src/complete_subtree_mre   tests/test_complete_subtree_unified_core.py   tests/test_complete_subtree_unified_session.py   tests/test_complete_subtree_unified_gmssl.py
```

Expected: exit 0.

## Focused tests

```bash
pytest -q   tests/test_complete_subtree_unified_core.py   tests/test_complete_subtree_unified_session.py   tests/test_complete_subtree_unified_gmssl.py
```

Expected theoretical result:

```text
11 passed
0 failed
0 skipped
```

## Required semantic checks

For N=8 and R={u3}:

```text
ST(R)       = {v1,v2,v5,v10}
Cover roots = {v3,v4,v11}
Covered     = {u1,u2,u4,u5,u6,u7,u8}
```

Receiver checks:

```text
u4 -> SUCCESS through v11
u3 -> REVOKED (no matching cover node)
u3 force-try own path key against E[L3](K)
   -> HEADER_UNWRAP_FAILED
```

Security projection:

- snapshot contains only K fingerprint, never raw K;
- trace contains only K/header fingerprints, node IDs and statuses;
- node-key bytes never enter normal snapshot/trace.

## Regression

After focused tests, rerun the frozen SM2+SM4 suite from the v0.6 baseline.
Expected baseline remains:

```text
43 passed
0 failed
0 skipped
```

This milestone should add new code only; it must not change the existing
SM2+SM4 implementation.
