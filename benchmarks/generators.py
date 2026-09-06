"""撤销集合生成器（随机 + 结构化，固定 seed 可复现）。"""

from __future__ import annotations

import random


def random_revoked(n: int, r: int, seed: int) -> set[int]:
    """Case A：随机撤销。固定 seed，可复现。"""
    rng = random.Random(seed)
    return set(rng.sample(range(1, n + 1), r))


def contiguous_revoked(n: int, r: int) -> set[int]:
    """Case B：连续撤销。用户 1..r（最左端连续块，共享最长前缀路径）。"""
    return set(range(1, r + 1))


def uniform_revoked(n: int, r: int) -> set[int]:
    """Case C：均匀分布撤销。步长 n//r，尽可能分散。"""
    step = max(1, n // r)
    return {1 + i * step for i in range(r)}


def clustered_revoked(n: int, r: int) -> set[int]:
    """Case D：局部聚集撤销。集中在右半子树（v3 子树，用户 n/2+1..n）。"""
    half = n // 2
    assert r <= half, "clustered 要求 r <= N/2"
    start = half + 1
    return set(range(start, start + r))
