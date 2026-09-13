"""CHW25 Construction 6.4 的教学实现（relation-preserving）。

忠实保留：五算法接口、密钥结构、Eq. (6.6)/(6.7)/(6.8)、密文/解密公式、阈值判定。
教学替代：r_i = e_i（取代 SuccinctTrapGen/Transform/DimRed）、反向构造 W、
         确定性 rerandomization（取代 explainable DGS）。

**论文公式 ↔ 命名 helper 对照**（encrypt/decrypt 与 UI 都只调用这些 helper）：
    (1)  W_S = Σ_{j∈S} W_j                    ↔ build_ws
    (2)  c1^T = s^T A + e^T                    ↔ compute_c1
    (3)  c2^T = s^T (W0+W_S) + e^T K_W         ↔ compute_c2
    (4)  c3   = s^T p + e^T k_p + μ⌊q/2⌋       ↔ compute_c3
    (5)  Y_i  = y_ii + y_0i + Σ_{j∈S\\{i}} y_ji ↔ build_decryption_term
    (6)  z    = c3 + c2^T r_i − c1^T Y_i       ↔ compute_z
    (7)  −q/4 ≤ z < q/4 ⇒ 0，否则 1            ↔ decode_z
"""

from __future__ import annotations

import numpy as np

from .algebra import (
    center_scalar,
    det_rng,
    det_vec_small,
    mod_q,
    rand_mat_binary,
    rand_vec_binary,
    rand_vec_small,
    rand_vec_uniform,
)
from .types import Ciphertext, Params, PublicKey, PublicParams, SecretKey


# ---------- Setup ----------


def setup(params: Params) -> PublicParams:
    """Setup(1^λ, 1^N) → pp = (A, p, R, {t_i})。

    【课程实现】略去 SuccinctTrapGen / Transform；
    取 r_i = e_i ∈ Z^m（标准基向量）。
    """
    n, m, q, N = params.n, params.m, params.q, params.N

    A = np.array(
        [[__import__("secrets").randbelow(q) for _ in range(m)] for _ in range(n)],
        dtype=np.int64,
    )
    p = rand_vec_uniform(n, q)
    t = np.array([rand_vec_uniform(n, q) for _ in range(N)], dtype=np.int64).T  # (n, N)

    R = np.zeros((m, N), dtype=np.int64)
    for i in range(1, N + 1):
        R[i - 1, i - 1] = 1  # r_i = e_i

    return PublicParams(params=params, A=A, p=p, R=R, t=t)


# ---------- KeyGen ----------


def keygen(pp: PublicParams, i: int) -> tuple[PublicKey, SecretKey]:
    """KeyGen(pp, i) → (pk_i = (W_i, {y_{i,j}}_{j≠i}), sk_i = y_{i,i})。

    【课程实现】反向构造 W_i 使 Eq. (6.6)/(6.7) 精确成立：
        W_i[:, i] = A·y_{i,i} − p
        W_i[:, j] = A·y_{i,j}      (j ≠ i)
    """
    params = pp.params
    n, m, q, N = params.n, params.m, params.q, params.N
    if not 1 <= i <= N:
        raise ValueError(f"用户索引越界：{i}")

    ys: dict[int, np.ndarray] = {
        j: rand_vec_small(m, params.y_bound) for j in range(1, N + 1)
    }

    W = np.zeros((n, m), dtype=np.int64)
    for j in range(1, N + 1):
        col = mod_q(pp.A @ ys[j], q)
        if j == i:
            col = mod_q(col - pp.p, q)
        W[:, j - 1] = col

    pk = PublicKey(W=W, ys={j: ys[j] for j in range(1, N + 1) if j != i})
    sk = SecretKey(y=ys[i])
    return pk, sk


# ---------- IsValid ----------


def is_valid(pp: PublicParams, i: int, pk: PublicKey) -> bool:
    """IsValid(pp, i, pk_i) → 1 iff ∀j≠i: A·y_{i,j} = W_i·r_j 且 ‖y_{i,j}‖ ≤ β_key。"""
    params = pp.params
    q, m = params.q, params.m

    for j, y in pk.ys.items():
        if j == i:
            return False  # pk 不应包含自己的分量
        if not np.array_equal(mod_q(pp.A @ y, q), mod_q(pk.W @ pp.R[:, j - 1], q)):
            return False
        if float(np.linalg.norm(y)) > params.y_bound * np.sqrt(m) + 1e-9:
            return False
    return True


# ---------- Encryption-time rerandomization（教学替代 Eq. (6.5)）----------


def derive_rerandomization(
    pp: PublicParams, s_set: set[int], xi: bytes
) -> tuple[np.ndarray, dict[int, np.ndarray]]:
    """以 (ξ ‖ S) 为确定性随机源，构造满足 Eq. (6.8) 的 (W_0, {y_{0,i}})。

    【课程实现】论文用 DGS.SamplePre(…; H_ρ(ξ)) + explainable 性质；
    此处是**教学替代**，不声称 explainable DGS。
        A·y_{0,i} = W_0·r_i ,  i ∈ S
    """
    params = pp.params
    n, m, q = params.n, params.m, params.q

    rng = det_rng(xi, s_set)
    y0 = {i: det_vec_small(rng, m, params.y_bound) for i in sorted(s_set)}

    W0 = np.zeros((n, m), dtype=np.int64)
    for i in s_set:
        W0[:, i - 1] = mod_q(pp.A @ y0[i], q)
    return W0, y0


# ================= 论文公式 helper（(1)–(7)）=================
# UI / DemoEngine 必须调用这些函数，禁止在界面层复制公式。


def build_ws(pp: PublicParams, pks: dict[int, PublicKey], s_set: set[int]) -> np.ndarray:
    """(1)  W_S = Σ_{j∈S} W_j   —— Construction 6.4, Encrypt 中的聚合。"""
    params = pp.params
    n, m, q = params.n, params.m, params.q
    W_S = np.zeros((n, m), dtype=np.int64)
    for j in sorted(s_set):
        W_S = mod_q(W_S + pks[j].W, q)
    return W_S


def compute_c1(pp: PublicParams, s: np.ndarray, e: np.ndarray) -> np.ndarray:
    """(2)  c1^T = s^T A + e^T。"""
    return mod_q(pp.A.T @ s + e, pp.params.q)


def compute_c2(
    pp: PublicParams,
    W0: np.ndarray,
    W_S: np.ndarray,
    s: np.ndarray,
    K_W: np.ndarray,
    e: np.ndarray,
) -> np.ndarray:
    """(3)  c2^T = s^T (W_0 + W_S) + e^T K_W。"""
    return mod_q((W0 + W_S).T @ s + K_W.T @ e, pp.params.q)


def compute_c3(
    pp: PublicParams, s: np.ndarray, e: np.ndarray, k_p: np.ndarray, mu: int
) -> int:
    """(4)  c3 = s^T p + e^T k_p + μ·⌊q/2⌋。"""
    params = pp.params
    return int(
        mod_q(int(pp.p @ s) + int(k_p @ e) + mu * params.half_q, params.q)
    )


def build_decryption_term(
    pp: PublicParams,
    pks: dict[int, PublicKey],
    s_set: set[int],
    i: int,
    sk: SecretKey,
    y0: dict[int, np.ndarray],
) -> np.ndarray:
    """(5)  Y_i = y_{i,i} + y_{0,i} + Σ_{j∈S\\{i}} y_{j,i}   —— construction 6.4, Decrypt 中的括号项。"""
    params = pp.params
    term = np.array(sk.y, dtype=np.int64) + y0[i]
    for j in sorted(s_set):
        if j != i:
            term = term + pks[j].ys[i]
    return mod_q(term, params.q)


def compute_z(ct: Ciphertext, r_i: np.ndarray, term: np.ndarray) -> int:
    """(6)  z = c3 + c2^T r_i − c1^T Y_i（原始整数；∈ Z_q 的归约由调用方完成）。"""
    return int(ct.c3 + int(ct.c2 @ r_i) - int(ct.c1 @ term))


def decode_z(z: int, q: int) -> int:
    """(7)  ⌊z⌉ = 0 若 −q/4 ≤ z < q/4（取中心代表），否则 1。"""
    zc = center_scalar(z, q)
    return 0 if -q // 4 <= zc < q // 4 else 1


# ---------- Encrypt ----------


def encrypt(
    pp: PublicParams,
    pks: dict[int, PublicKey],
    s_set: set[int],
    mu: int,
    xi: bytes | None = None,
) -> Ciphertext:
    """Encrypt(pp, {(j,pk_j)}_{j∈S}, μ) → ct = (ξ, c_1^T, c_2^T, c_3)。"""
    params = pp.params
    n, m, q = params.n, params.m, params.q
    if mu not in (0, 1):
        raise ValueError(f"第一版只支持单 bit μ∈{{0,1}}，得到 {mu}")
    if xi is None:
        xi = __import__("os").urandom(params.xi_bytes)

    s = rand_vec_uniform(n, q)                 # (n,)
    e = rand_vec_small(m, params.noise_bound)  # (m,)
    K_W = rand_mat_binary(m, m)                # (m, m)
    k_p = rand_vec_binary(m)                   # (m,)

    W0, _ = derive_rerandomization(pp, s_set, xi)
    W_S = build_ws(pp, pks, s_set)                                   # (1)

    c1 = compute_c1(pp, s, e)                                        # (2)
    c2 = compute_c2(pp, W0, W_S, s, K_W, e)                          # (3)
    c3 = compute_c3(pp, s, e, k_p, mu)                               # (4)
    return Ciphertext(xi=xi, c1=c1, c2=c2, c3=c3)


# ---------- Decrypt ----------


def decrypt(
    pp: PublicParams,
    pks: dict[int, PublicKey],
    s_set: set[int],
    ct: Ciphertext,
    i: int,
    sk: SecretKey,
) -> int:
    """Decrypt → μ ∈ {0,1}；i ∉ S 输出 0。

    z = c_3 + c_2^T r_i − c_1^T ( y_{i,i} + y_{0,i} + Σ_{j∈S\\{i}} y_{j,i} )
    """
    if i not in s_set:
        return 0

    q = pp.params.q
    _, y0 = derive_rerandomization(pp, s_set, ct.xi)
    term = build_decryption_term(pp, pks, s_set, i, sk, y0)          # (5)
    r_i = pp.R[:, i - 1]  # = e_i
    z = mod_q(compute_z(ct, r_i, term), q)                           # (6)
    return decode_z(z, q)                                            # (7)
