"""CHW25 Construction 6.4 教学实现测试。

覆盖：Eq. (6.6)/(6.7)/(6.8)、IsValid、授权解密、非授权拒绝、
N=4 S={2,4} 场景、trace 抵消、模运算与 centered representative、rerandomization 确定性。
"""

import secrets

import numpy as np
import pytest

from src.chw25_dbe import (
    Params,
    decrypt,
    decrypt_with_trace,
    derive_rerandomization,
    encrypt,
    is_valid,
    keygen,
    setup,
)
from src.chw25_dbe.algebra import center_scalar, mod_q

P = Params()  # n=4, m=8, q=104729, N=4


@pytest.fixture(scope="module")
def system():
    pp = setup(P)
    pks, sks = {}, {}
    for i in range(1, P.N + 1):
        pk, sk = keygen(pp, i)
        pks[i], sks[i] = pk, sk
    return pp, pks, sks


def _random_s():
    return {i for i in range(1, P.N + 1) if secrets.randbelow(2)} or {1}


# ---- 1. Eq. (6.6) ----


def test_eq_6_6(system):
    """A·y_{i,i} = W_i·r_i + p（Theorem 6.5）"""
    pp, pks, sks = system
    for i in range(1, P.N + 1):
        lhs = mod_q(pp.A @ sks[i].y, P.q)
        rhs = mod_q(pks[i].W @ pp.R[:, i - 1] + pp.p, P.q)
        assert np.array_equal(lhs, rhs), f"Eq.(6.6) 失败 i={i}"


# ---- 2. Eq. (6.7) ----


def test_eq_6_7(system):
    """A·y_{i,j} = W_i·r_j（j ≠ i，Theorem 6.5）"""
    pp, pks, sks = system
    for i in range(1, P.N + 1):
        for j in range(1, P.N + 1):
            if j == i:
                continue
            assert np.array_equal(
                mod_q(pp.A @ pks[i].ys[j], P.q), mod_q(pks[i].W @ pp.R[:, j - 1], P.q)
            ), f"Eq.(6.7) 失败 i={i} j={j}"


# ---- 3. Eq. (6.8) ----


def test_eq_6_8(system):
    """A·y_{0,i} = W_0·r_i（i ∈ S，Theorem 6.6）"""
    pp, _, _ = system
    for _ in range(5):
        S = _random_s()
        xi = secrets.token_bytes(P.xi_bytes)
        W0, y0 = derive_rerandomization(pp, S, xi)
        for i in S:
            assert np.array_equal(
                mod_q(pp.A @ y0[i], P.q), mod_q(W0 @ pp.R[:, i - 1], P.q)
            ), f"Eq.(6.8) 失败 i={i}"


# ---- 4. IsValid 接受诚实公钥 ----


def test_is_valid_accepts_honest(system):
    pp, pks, _ = system
    for i in range(1, P.N + 1):
        assert is_valid(pp, i, pks[i]) == True  # noqa: E712


# ---- 5. IsValid 拒绝篡改公钥 ----


def test_is_valid_rejects_tampered(system):
    pp, pks, _ = system
    pk = pks[1]
    # 篡改 W
    bad_W = type(pk)(W=(pk.W + 1) % P.q, ys=pk.ys)
    assert is_valid(pp, 1, bad_W) is False
    # 篡改 y
    bad_ys = dict(pk.ys)
    j0 = next(iter(bad_ys))
    tampered = bad_ys[j0].copy()
    tampered[0] += 1
    bad_ys[j0] = tampered
    bad_pk = type(pk)(W=pk.W, ys=bad_ys)
    assert is_valid(pp, 1, bad_pk) is False


# ---- 6/7. 授权解密（随机 S、∀i∈S、μ∈{0,1}）----


def test_authorized_decrypt_random_s(system):
    pp, pks, sks = system
    for _ in range(10):
        S = _random_s()
        for mu in (0, 1):
            xi = secrets.token_bytes(P.xi_bytes)
            ct = encrypt(pp, pks, S, mu, xi=xi)
            for i in S:
                assert decrypt(pp, pks, S, ct, i, sks[i]) == mu, f"S={S} mu={mu} i={i}"


# ---- 8. i∉S 被拒绝 ----


def test_non_recipient_rejected(system):
    pp, pks, sks = system
    S = {2, 4}
    ct = encrypt(pp, pks, S, mu=1, xi=secrets.token_bytes(P.xi_bytes))
    for i in (1, 3):
        assert decrypt(pp, pks, S, ct, i, sks[i]) == 0  # 论文：i∉S 输出 0


# ---- 9. N=4, S={2,4} ----


def test_n4_s24(system):
    """u2/u4 成功；u1/u3 不属于广播集合。"""
    pp, pks, sks = system
    S = {2, 4}
    for mu in (0, 1):
        ct = encrypt(pp, pks, S, mu, xi=secrets.token_bytes(P.xi_bytes))
        assert decrypt(pp, pks, S, ct, 2, sks[2]) == mu
        assert decrypt(pp, pks, S, ct, 4, sks[4]) == mu
        # u1/u3 输出 0；当 mu=1 时与真值不符 → 证明被拒
        assert decrypt(pp, pks, S, ct, 1, sks[1]) == 0
        assert decrypt(pp, pks, S, ct, 3, sks[3]) == 0


# ---- 10. trace 抵消 ----


def test_trace_cancellation(system):
    """z_centered ≈ μ⌊q/2⌋，noise_residual 小。"""
    pp, pks, sks = system
    S = {2, 4}
    for mu in (0, 1):
        ct = encrypt(pp, pks, S, mu, xi=secrets.token_bytes(P.xi_bytes))
        got, tr = decrypt_with_trace(pp, pks, S, ct, 2, sks[2])
        assert got == mu
        assert tr["decoded_mu"] == mu
        # c1 项 = y_ii + y_0i + Σ y_ji 的线性组合
        assert tr["c1_term_total"] == tr["c1_dot_y_ii"] + tr["c1_dot_y_0i"] + sum(
            tr["c1_dot_y_ji"].values()
        )
        # 抵消后噪声很小；且 z_centered ≡ μ⌊q/2⌋ + noise (mod q)
        assert abs(tr["noise_residual"]) < P.q // 4
        assert (tr["z_centered"] - mu * P.half_q - tr["noise_residual"]) % P.q == 0


def test_trace_non_recipient(system):
    pp, pks, sks = system
    S = {2, 4}
    ct = encrypt(pp, pks, S, 1, xi=secrets.token_bytes(P.xi_bytes))
    _, tr = decrypt_with_trace(pp, pks, S, ct, 1, sks[1])
    assert tr["in_S"] is False and tr["decoded_mu"] == 0


# ---- 11. 模运算 / centered representative ----


def test_centered_representative():
    q = P.q
    assert center_scalar(0, q) == 0
    assert center_scalar(q // 4, q) == q // 4
    # q-1 的中心代表应为 -1
    assert center_scalar(q - 1, q) == -1
    # 解码边界：q/4 处为 1，q/4-1 处为 0
    assert (0 if -q // 4 <= center_scalar(q // 4, q) < q // 4 else 1) == 1
    assert (0 if -q // 4 <= center_scalar(q // 4 - 1, q) < q // 4 else 1) == 0


# ---- 12. rerandomization 确定性 ----


def test_rerandomization_deterministic(system):
    pp, _, _ = system
    S = {2, 4}
    xi = b"fixed-seed-123456"
    W0a, y0a = derive_rerandomization(pp, S, xi)
    W0b, y0b = derive_rerandomization(pp, S, xi)
    assert np.array_equal(W0a, W0b)
    for i in S:
        assert np.array_equal(y0a[i], y0b[i])
    # 换 ξ → 不同
    W0c, y0c = derive_rerandomization(pp, S, b"different-seed!!")
    assert not np.array_equal(W0a, W0c)


# ---- 补充：参数约束 ----


def test_params_constraint():
    with pytest.raises(ValueError):
        Params(n=4, m=2, q=104729, N=4)  # m < N
