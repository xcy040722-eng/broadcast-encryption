"""CHW25 DBE 压力测试：随机 (S, μ, user) 数千组，验证正确性与非接收者识别。"""

import secrets

import pytest

from src.chw25_dbe import (
    Params,
    decrypt_bit,
    decrypt_with_trace,
    encrypt,
    keygen,
    setup,
)

P = Params()
GROUPS = 3000


@pytest.fixture(scope="module")
def system():
    pp = setup(P)
    pks, sks = {}, {}
    for i in range(1, P.N + 1):
        pk, sk = keygen(pp, i)
        pks[i], sks[i] = pk, sk
    return pp, pks, sks


def test_stress_correctness_and_noise(system):
    pp, pks, sks = system
    max_noise = 0
    n_auth = 0
    n_nonrec = 0

    for _ in range(GROUPS):
        # 随机非空 S
        S = {i for i in range(1, P.N + 1) if secrets.randbelow(2)} or {1}
        user = 1 + secrets.randbelow(P.N)
        mu = secrets.randbelow(2)
        ct = encrypt(pp, pks, S, mu)

        if user in S:
            got, tr = decrypt_with_trace(pp, pks, S, ct, user, sks[user])
            assert got == mu, f"授权恢复失败 S={S} user={user} mu={mu} got={got}"
            assert tr["authorized"] if "authorized" in tr else True
            max_noise = max(max_noise, abs(tr["noise_residual"]))
            n_auth += 1
        else:
            res = decrypt_bit(pp, pks, S, ct, user, sks[user])
            assert res.authorized is False and res.bit is None, (
                f"非接收者未被识别 S={S} user={user} -> {res}"
            )
            n_nonrec += 1

    # 断言噪声始终 < q/4
    assert max_noise < P.q // 4, f"噪声超界：{max_noise} >= {P.q // 4}"

    margin = P.q // 4 - max_noise
    ratio = max_noise / (P.q // 4)
    print(
        f"\n[stress] groups={GROUPS} authorized={n_auth} non_recipient={n_nonrec}\n"
        f"[stress] max |noise_residual| = {max_noise}\n"
        f"[stress] threshold q/4 = {P.q // 4}\n"
        f"[stress] margin = {margin}  (noise uses {ratio*100:.4f}% of threshold)"
    )

    # 授权/非接收者两组都要有足够样本
    assert n_auth > GROUPS * 0.2
    assert n_nonrec > GROUPS * 0.2
