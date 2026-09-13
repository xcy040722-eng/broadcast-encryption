"""解密中间值 trace（供后续动态可视化）。

输出 CHW25 Construction 6.4 解密过程的每一步中间量。
不涉及任何私钥/会话密钥的对外暴露；仅供项目内部可视化使用。
"""

from __future__ import annotations

import numpy as np

from .algebra import center_scalar, mod_q
from .construction import derive_rerandomization
from .types import Ciphertext, PublicKey, PublicParams, SecretKey


def decrypt_with_trace(
    pp: PublicParams,
    pks: dict[int, PublicKey],
    s_set: set[int],
    ct: Ciphertext,
    i: int,
    sk: SecretKey,
) -> tuple[int, dict]:
    """执行解密并返回 (μ̂, trace)。

    trace 键：
        c3, c2_dot_r_i, c1_dot_y_ii, c1_dot_y_0i, c1_dot_y_ji{},
        c1_term_total, z_before_center, z_centered, noise_residual,
        decoded_mu, threshold, in_S
    """
    q = pp.params.q
    half_q = pp.params.half_q

    trace: dict = {
        "in_S": i in s_set,
        "threshold": q // 4,
        "half_q": half_q,
        "c3": int(ct.c3),
    }

    if i not in s_set:
        trace["decoded_mu"] = 0
        trace["reason"] = "i ∉ S，按论文 Decrypt 输出 0"
        return 0, trace

    _, y0 = derive_rerandomization(pp, s_set, ct.xi)
    r_i = pp.R[:, i - 1]  # = e_i

    c2_dot_r_i = int(ct.c2 @ r_i)
    c1_dot_y_ii = int(ct.c1 @ np.asarray(sk.y, dtype=np.int64))
    c1_dot_y_0i = int(ct.c1 @ y0[i])
    c1_dot_y_ji = {
        j: int(ct.c1 @ pks[j].ys[i]) for j in sorted(s_set) if j != i
    }

    # 各分项之和（用未归约的短向量，使 trace 恒等式精确成立）
    c1_term_total = c1_dot_y_ii + c1_dot_y_0i + sum(c1_dot_y_ji.values())

    z_before_center = int(mod_q(ct.c3 + c2_dot_r_i - c1_term_total, q))
    z_centered = center_scalar(z_before_center, q)
    decoded_mu = 0 if -q // 4 <= z_centered < q // 4 else 1
    # 噪声 = (z − μ̂⌊q/2⌋) 在 Z_q 中的中心代表（避免 ⌊q/2⌋ 处代表翻转带来的歧义）
    noise_residual = center_scalar(z_before_center - decoded_mu * half_q, q)

    trace.update(
        {
            "c2_dot_r_i": c2_dot_r_i,
            "c1_dot_y_ii": c1_dot_y_ii,
            "c1_dot_y_0i": c1_dot_y_0i,
            "c1_dot_y_ji": c1_dot_y_ji,
            "c1_term_total": c1_term_total,
            "c3_plus_c2_term": int(mod_q(ct.c3 + c2_dot_r_i, q)),  # 抵消前
            "z_before_center": z_before_center,
            "z_centered": z_centered,
            "noise_residual": noise_residual,
            "decoded_mu": decoded_mu,
        }
    )
    return decoded_mu, trace
