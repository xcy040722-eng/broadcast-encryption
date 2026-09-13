"""CHW25 Construction 6.4 的数据类型。

与论文接口对应：
    Π_DBE = (Setup, KeyGen, IsValid, Encrypt, Decrypt)
    pk_i = (W_i, {y_{i,j}}_{j≠i}),  sk_i = y_{i,i}
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Params:
    """课程 TOY 参数（集中配置，代码中不散落 magic number）。

    【课程实现】非论文正式参数。
    """

    n: int = 4           # 格维度
    m: int = 8           # ≥ N（供 N 个位置使用）
    q: int = 104729      # toy prime
    N: int = 4           # 用户数
    noise_bound: int = 1  # e 的采样范围 {−bound..bound}
    y_bound: int = 1      # y_{i,j} 的采样范围 {−bound..bound}
    xi_bytes: int = 16    # rerandomization 种子长度

    @property
    def half_q(self) -> int:
        return self.q // 2

    def __post_init__(self):
        if self.m < self.N:
            raise ValueError(f"需要 m >= N（m={self.m}, N={self.N}）")


@dataclass
class PublicParams:
    """pp = (A, p, R, {t_i})。

    【课程实现】论文的 pp = (A, p, V, Z, {r_i, t_i}, T_V, T_Ẑ)；
    V / Z / T_V / T_Ẑ 由 r_i = e_i 的教学替代绕过（见 implementation spec §3）。
    """

    params: Params
    A: np.ndarray          # (n, m)
    p: np.ndarray          # (n,)
    R: np.ndarray          # (m, N)  第 i 列 = r_i = e_i
    t: np.ndarray          # (n, N)  【忠实保留但不在正确性路径使用】


@dataclass
class PublicKey:
    """pk_i = (W_i, {y_{i,j}}_{j≠i})。"""

    W: np.ndarray                       # (n, m)
    ys: dict[int, np.ndarray] = field(default_factory=dict)  # {j: y_{i,j}, j != i}


@dataclass
class SecretKey:
    """sk_i = y_{i,i}。"""

    y: np.ndarray   # (m,)


@dataclass
class Ciphertext:
    """ct = (ξ, c_1^T, c_2^T, c_3)。"""

    xi: bytes
    c1: np.ndarray   # (m,)
    c2: np.ndarray   # (m,)
    c3: int


# ---------- 应用层状态（论文 i∉S → 输出 0；应用层必须区分）----------


@dataclass
class DecryptResult:
    """单 bit 解密结果。

    【论文】Construction 6.4 在 i ∉ S 时 Decrypt 输出 0。
    应用层必须区分「真 0」与「非接收者」：
        authorized=True,  bit=0/1   ← 真值
        authorized=False, bit=None  ← 非接收者（i ∉ S）
    """

    authorized: bool
    bit: int | None = None


@dataclass
class SessionKeyResult:
    """会话密钥层结果（256 bit 聚合）。"""

    authorized: bool
    key: bytes | None = None


@dataclass
class FileResult:
    """文件层结果。"""

    authorized: bool
    output_path: str | None = None
