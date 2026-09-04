"""GGM 伪随机序列生成器 —— NNL01 §3.2 / Figure 3。

【NNL01 原文】G 是「triples the input」的 PRG，输出长度 = 3 × 输入长度：
- G_L(S) = 左 1/3 → 左孩子的 label
- G_R(S) = 右 1/3 → 右孩子的 label
- G_M(S) = 中 1/3 → 该节点的 key

【ENGINEERING ADAPTATION】原文 G 是抽象 PRG；本实现用 SHA-256 做 domain separation，
G_L/G_R/G_M 各派生 32 字节，等价实现「三路输出」的语义。不声称论文规定 SHA-256。
"""

from __future__ import annotations

import hashlib
import secrets

LABEL_LEN = 32  # 256-bit


def random_label() -> bytes:
    """生成初始随机 label（secrets，密码学安全）。"""
    return secrets.token_bytes(LABEL_LEN)


def _derive(seed: bytes, domain: bytes) -> bytes:
    return hashlib.sha256(domain + seed).digest()


def G_L(seed: bytes) -> bytes:
    """左 1/3：左孩子的 label。"""
    return _derive(seed, b"left")


def G_R(seed: bytes) -> bytes:
    """右 1/3：右孩子的 label。"""
    return _derive(seed, b"right")


def G_M(seed: bytes) -> bytes:
    """中 1/3：该节点的 key。"""
    return _derive(seed, b"middle")
