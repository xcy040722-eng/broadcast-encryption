"""Z_q 代数辅助（模运算、centered representative、范数、采样）。

【课程实现】所有运算统一在 Z_q 中；解码前使用 centered modular representative。
采样使用 secrets（随机性）或确定性 PRNG（rerandomization 的可复现性）。
"""

from __future__ import annotations

import hashlib
import secrets

import numpy as np


def mod_q(x, q: int) -> np.ndarray:
    """统一归约到 Z_q。"""
    return np.mod(np.asarray(x, dtype=np.int64), q)


def center(x, q: int) -> np.ndarray:
    """centered modular representative，范围 [-(q//2), q//2]。"""
    r = mod_q(x, q)
    half = q // 2
    return np.where(r > half, r - q, r)


def center_scalar(x: int, q: int) -> int:
    """标量版 centered representative。"""
    r = x % q
    return r - q if r > q // 2 else r


def l2_norm(v: np.ndarray) -> float:
    """L2 范数（用于 low-norm 检查）。"""
    return float(np.linalg.norm(center(v, 1) if False else np.asarray(v, dtype=np.int64)))


def rand_vec_uniform(length: int, q: int) -> np.ndarray:
    """均匀随机向量 ∈ Z_q^length。"""
    return np.array([secrets.randbelow(q) for _ in range(length)], dtype=np.int64)


def rand_vec_small(length: int, bound: int) -> np.ndarray:
    """低范数向量，元素 ∈ [-bound, bound]。"""
    return np.array(
        [secrets.randbelow(2 * bound + 1) - bound for _ in range(length)], dtype=np.int64
    )


def rand_vec_binary(length: int) -> np.ndarray:
    """二进制向量 ∈ {0,1}^length。"""
    return np.array([secrets.randbelow(2) for _ in range(length)], dtype=np.int64)


def rand_mat_binary(rows: int, cols: int) -> np.ndarray:
    """二进制矩阵 ∈ {0,1}^{rows×cols}。"""
    return np.array(
        [[secrets.randbelow(2) for _ in range(cols)] for _ in range(rows)], dtype=np.int64
    )


def det_rng(xi: bytes, s_set: set[int]):
    """由 (ξ ‖ S) 派生确定性 PRNG（rerandomization 的可复现性）。"""
    from random import Random

    payload = xi + b"|" + ",".join(str(x) for x in sorted(s_set)).encode()
    seed = int.from_bytes(hashlib.sha256(payload).digest(), "big")
    return Random(seed)


def det_vec_small(rng, length: int, bound: int) -> np.ndarray:
    """用给定 PRNG 生成低范数向量（可复现）。"""
    return np.array([rng.randint(-bound, bound) for _ in range(length)], dtype=np.int64)
