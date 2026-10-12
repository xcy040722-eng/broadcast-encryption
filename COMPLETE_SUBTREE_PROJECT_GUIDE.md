# Complete Subtree Unified — Project / Defense Guide

## 1. Project role

This module is the **classic tree-based broadcast-revocation** side of the
course project.  It is intentionally separate from the SM2+SM4
multi-recipient hybrid-encryption scheme:

- **Complete Subtree**: symmetric tree-key revocation and subset cover.
- **SM2+SM4**: public-key per-recipient wrapping plus one SM4-GCM payload.

Both modules now share the same engineering foundation:

- Python 3
- PySide6
- GmSSL native backend
- SM3 fingerprints for safe display
- SM4-GCM for authenticated symmetric protection
- state-driven InteractiveSession APIs
- safe Snapshot / Trace projections
- Chinese-first UI with English fallback

## 2. Complete Subtree algorithm

For `N=2^h` users, construct a full binary tree. User `u_i` is assigned to
one leaf. Every tree node `v_j` owns an independent long-lived 128-bit key
`L_j`.

User `u_i` receives the node keys on its root-to-leaf path.

For a revocation set `R`:

1. Compute the Steiner tree

   ```text
   ST(R) = union of root-to-revoked-leaf paths
   ```

2. Select the complete subtrees hanging off `ST(R)`.

3. Their roots form `Cover(R)`.

4. The selected subtrees are disjoint and cover exactly `U \ R`.

For the standard demo:

```text
N = 8
R = {u3}

ST(R) = {v1,v2,v5,v10}
Cover  = {v3,v4,v11}
```

The three Cover subtrees represent:

```text
v3  -> {u5,u6,u7,u8}
v4  -> {u1,u2}
v11 -> {u4}
```

## 3. Engineering instantiation of E_L(K)

The NNL01 Complete Subtree method treats `E_L(K)` as an abstract symmetric
encryption primitive.

This project instantiates it with real GmSSL SM4-GCM:

```text
H_i = SM4-GCM.Enc(
        L_i,
        IV_i,
        Envelope(package_id, node_id=i, K),
        AAD_i
      )
```

Each Cover root therefore contributes one authenticated Header entry
`E[L_i](K)`.

The Envelope binds the Header to both:

- the current broadcast `package_id`;
- the intended Cover node `node_id`.

## 4. Receiver rule

For user `u`, let `Path(u)` be the root-to-leaf node set.

An authorized receiver has exactly one Cover match:

```text
v* = Path(u) intersect Cover
K  = Dec_{L_v*}(H_v*)
```

A revoked receiver has no Cover match and returns:

```text
REVOKED
```

The teaching workbench also provides a deliberate wrong-key path:

```text
u3 owns L10
target Header = E[L3](K)

L10 -> E[L3](K)
-> real GmSSL SM4-GCM authentication failure
-> HEADER_UNWRAP_FAILED
```

This demonstrates that denial is not only a UI-level revoked check.

## 5. Security display boundary

Normal UI state never displays:

- raw broadcast content key `K`;
- any raw long-lived tree key `L_i`.

The UI receives only:

- node/user IDs;
- Cover / Steiner membership;
- receiver paths;
- machine-stable status values;
- SM3 fingerprints.

## 6. Standard defense demo

Recommended order:

1. Set `R={u3}`.
2. Compute `ST(R)` and `Cover`.
3. Generate one broadcast content key `K`.
4. Drag `K` to `v3`, `v4`, `v11`.
5. Explain each resulting `E[L_i](K)`.
6. Recover as `u4` -> `SUCCESS` through `v11`.
7. Recover as `u3` -> `REVOKED`.
8. Force try `u3 -> v3` -> `HEADER_UNWRAP_FAILED`.
9. Open **Principle / live state** and explain:
   `R`, `ST(R)`, `Cover`, `L_i`, `K`, `E[L_i](K)`, Receiver Path.

## 7. Comparison with SM2+SM4

### Complete Subtree

```text
revocation set R
-> Steiner tree
-> Cover
-> one Header per Cover root
-> receivers reuse shared path keys
```

Header count depends on the Cover size, not directly on the number of authorized
receivers.

### SM2+SM4

```text
authorized set S
-> one SM2 wrapped key E[i] per authorized user
-> one shared SM4-GCM encrypted media payload
```

The wrapped-key Header grows linearly with `|S|`.

### Correct wording

Use:

> The project implements a classic Complete Subtree broadcast-revocation
> mechanism and a separate SM2+SM4 multi-recipient hybrid-encryption /
> broadcast-style distribution scheme.

Do not claim that SM2+SM4 itself is a constant-header Broadcast Encryption
construction.

## 8. High-value interview points

- Explain why Complete Subtree can represent many authorized users using one
  Cover-node Header.
- Explain why a revoked user's path intersects no Cover root.
- Explain why users hold only root-to-leaf path keys rather than all tree keys.
- Explain why the project instantiates abstract `E_L(K)` with SM4-GCM.
- Explain how force-try proves a wrong path key fails cryptographically.
- Explain how Complete Subtree differs structurally from per-user SM2 wrapping.
