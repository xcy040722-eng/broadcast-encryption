"""Benchmark runner：CS/SD 的 cover/header/keygen/decrypt 执行 + 计时 + correctness gate。"""

from __future__ import annotations

import statistics
import time

from src.cs import (
    cover as cs_cover,
    decrypt_session_key as cs_decrypt,
    encrypt_session_key as cs_encrypt,
    keygen as cs_keygen,
    serialize_header as cs_serialize,
    setup as cs_setup,
)
from src.sd import (
    decrypt_session_key as sd_decrypt,
    encrypt_session_key as sd_encrypt,
    keygen as sd_keygen,
    sd_cover,
    serialize_header as sd_serialize,
    setup as sd_setup,
)


# ---- timing ----


def time_fn(fn, warmup: int, measurement: int) -> tuple[int, int]:
    """执行 fn（warmup 次不记录，measurement 次记录），返回 (median_ns, p95_ns)。"""
    for _ in range(warmup):
        fn()
    samples: list[int] = []
    for _ in range(measurement):
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        samples.append(t1 - t0)
    samples.sort()
    median = samples[len(samples) // 2]
    p95 = samples[min(len(samples) - 1, int(len(samples) * 0.95))]
    return median, p95


# ---- correctness gate ----


def cs_covered_users(tree, cover_roots) -> set[int]:
    covered = set()
    for root in cover_roots:
        covered.update(tree.users_in_subtree(root))
    return covered


def cs_gate(tree, cover_roots, R) -> bool:
    covered = cs_covered_users(tree, cover_roots)
    all_users = set(range(1, tree.N + 1))
    if covered != all_users - R:
        return False
    if covered & R:
        return False
    total = sum(len(tree.users_in_subtree(root)) for root in cover_roots)
    if total != tree.N - len(R):
        return False
    return True


def sd_subset_users(tree, i, j) -> set[int]:
    if j is None:
        return set(tree.subtree_users(i))
    return set(tree.subtree_users(i)) - set(tree.subtree_users(j))


def sd_covered_users(tree, cover) -> set[int]:
    covered = set()
    for (i, j) in cover:
        covered.update(sd_subset_users(tree, i, j))
    return covered


def sd_gate(tree, cover, R) -> bool:
    covered = sd_covered_users(tree, cover)
    all_users = set(range(1, tree.N + 1))
    if covered != all_users - R:
        return False
    if covered & R:
        return False
    total = sum(len(sd_subset_users(tree, i, j)) for (i, j) in cover)
    if total != tree.N - len(R):
        return False
    if R and len(cover) > 2 * len(R) - 1:
        return False
    return True


# ---- runner ----


def run_trial(algorithm: str, N: int, R: set[int], K: bytes, warmup: int, measurement: int) -> dict:
    """对单个 (algorithm, N, R) 执行完整 benchmark，返回核心指标 dict。"""
    if algorithm == "CS":
        return _run_cs(N, R, K, warmup, measurement)
    return _run_sd(N, R, K, warmup, measurement)


def _run_cs(N, R, K, warmup, measurement):
    setup_ns, _ = time_fn(lambda: cs_setup(N), warmup, measurement)
    tree, node_keys = cs_setup(N)

    keygen_ns, _ = time_fn(
        lambda: [cs_keygen(tree, node_keys, u) for u in range(1, N + 1)],
        warmup, measurement,
    )
    materials = [cs_keygen(tree, node_keys, u) for u in range(1, N + 1)]
    key_counts = [len(m) for m in materials]

    cover_ns, _ = time_fn(lambda: cs_cover(tree, R), warmup, measurement)
    cover_roots = cs_cover(tree, R)
    assert cs_gate(tree, cover_roots, R), "CS correctness gate failed"

    header_encrypt_ns, _ = time_fn(lambda: cs_encrypt(node_keys, cover_roots, K), warmup, measurement)
    header = cs_encrypt(node_keys, cover_roots, K)
    serialized = cs_serialize(header)

    # 授权恢复：取第一个非撤销用户（可复现）；R=全部时无授权用户，跳过
    authorized = [u for u in range(1, N + 1) if u not in R]
    recover_ns = None
    if authorized:
        u_auth = authorized[0]
        auth_material = materials[u_auth - 1]
        recover_ns, _ = time_fn(lambda: cs_decrypt(auth_material, header), warmup, measurement)
        assert cs_decrypt(auth_material, header) == K, "CS authorized recovery failed"

    # 撤销拒绝：取第一个撤销用户
    reject_ns = None
    if R:
        u_rev = sorted(R)[0]
        rev_material = materials[u_rev - 1]
        reject_ns, _ = time_fn(lambda: cs_decrypt(rev_material, header), warmup, measurement)
        assert cs_decrypt(rev_material, header) is None, "CS revoked reject failed"

    return {
        "correct": True,
        "cover_count": len(cover_roots),
        "header_bytes": len(serialized),
        "key_material_mean": statistics.mean(key_counts),
        "key_material_max": max(key_counts),
        "setup_ns": setup_ns,
        "keygen_ns": keygen_ns,
        "cover_ns": cover_ns,
        "header_encrypt_ns": header_encrypt_ns,
        "authorized_recover_ns": recover_ns,
        "revoked_reject_ns": reject_ns,
    }


def _run_sd(N, R, K, warmup, measurement):
    setup_ns, _ = time_fn(lambda: sd_setup(N), warmup, measurement)
    tree, labels = sd_setup(N)

    keygen_ns, _ = time_fn(
        lambda: [sd_keygen(tree, labels, u) for u in range(1, N + 1)],
        warmup, measurement,
    )
    materials = [sd_keygen(tree, labels, u) for u in range(1, N + 1)]
    key_counts = [len(m["labels"]) + 1 for m in materials]  # labels + full_tree_key

    cover_ns, _ = time_fn(lambda: sd_cover(tree, R), warmup, measurement)
    cover = sd_cover(tree, R)
    assert sd_gate(tree, cover, R), "SD correctness gate failed"

    header_encrypt_ns, _ = time_fn(lambda: sd_encrypt(labels, tree, cover, K), warmup, measurement)
    header = sd_encrypt(labels, tree, cover, K)
    serialized = sd_serialize(header)

    # 授权恢复：取第一个非撤销用户（可复现）；R=全部时无授权用户，跳过
    authorized = [u for u in range(1, N + 1) if u not in R]
    recover_ns = None
    if authorized:
        u_auth = authorized[0]
        auth_material = materials[u_auth - 1]
        recover_ns, _ = time_fn(lambda: sd_decrypt(auth_material, tree, header), warmup, measurement)
        assert sd_decrypt(auth_material, tree, header) == K, "SD authorized recovery failed"

    reject_ns = None
    if R:
        u_rev = sorted(R)[0]
        rev_material = materials[u_rev - 1]
        reject_ns, _ = time_fn(lambda: sd_decrypt(rev_material, tree, header), warmup, measurement)
        assert sd_decrypt(rev_material, tree, header) is None, "SD revoked reject failed"

    return {
        "correct": True,
        "cover_count": len(cover),
        "header_bytes": len(serialized),
        "key_material_mean": statistics.mean(key_counts),
        "key_material_max": max(key_counts),
        "setup_ns": setup_ns,
        "keygen_ns": keygen_ns,
        "cover_ns": cover_ns,
        "header_encrypt_ns": header_encrypt_ns,
        "authorized_recover_ns": recover_ns,
        "revoked_reject_ns": reject_ns,
    }
