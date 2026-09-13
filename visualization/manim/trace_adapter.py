"""把真实 CHW25 后端输出转换为 Manim scene data。

**Manim 不重新实现密码学**：所有数值均来自
`src/chw25_dbe` 的 setup / keygen / encrypt / decrypt_with_trace / hybrid API。

见 docs/chw25-visualization-design.md（数据契约）。
"""

from __future__ import annotations

import hashlib
import os
import tempfile

import numpy as np

from src.chw25_dbe import (
    KEY_LEN,
    Params,
    decrypt_file_for_user,
    decrypt_with_trace,
    encrypt,
    encrypt_file_for_set,
    encrypt_session_key,
    keygen,
    keyset_id,
    params_id,
    setup,
)


def _fp(arr) -> str:
    return hashlib.sha256(np.asarray(arr, dtype=np.int64).tobytes()).hexdigest()[:8]


def _head(arr, k=3):
    return [int(x) for x in np.asarray(arr, dtype=np.int64).ravel()[:k]]


def build_scene_data(
    N: int = 4,
    s_set: set[int] | None = None,
    mu: int = 1,
    focus_user: int = 2,
    media_bytes: bytes | None = None,
    media_name: str = "image.png",
) -> dict:
    """运行一次真实 demo，返回 Manim scene 所需的全部数值。"""
    s_set = {2, 4} if s_set is None else set(s_set)
    params = Params(N=N, m=max(8, N))
    pp = setup(params)

    pks, sks = {}, {}
    for i in range(1, N + 1):
        pk, sk = keygen(pp, i)
        pks[i], sks[i] = pk, sk

    ct = encrypt(pp, pks, s_set, mu)

    W_S = np.zeros_like(pks[1].W)
    for j in s_set:
        W_S = (W_S + pks[j].W) % params.q

    # 焦点用户的真实 trace
    got, tr = decrypt_with_trace(pp, pks, s_set, ct, focus_user, sks[focus_user])

    users = []
    for i in range(1, N + 1):
        users.append({
            "id": i,
            "W_fp": _fp(pks[i].W),
            "y_ii_fp": _fp(sks[i].y),
            "cross_fp": {str(j): _fp(y) for j, y in sorted(pks[i].ys.items())},
            "is_recipient": i in s_set,
        })

    trace = {
        "user": focus_user,
        "c3": tr["c3"],
        "c2_dot_r_i": tr["c2_dot_r_i"],
        "c1_dot_y_ii": tr["c1_dot_y_ii"],
        "c1_dot_y_0i": tr["c1_dot_y_0i"],
        "c1_dot_y_ji": {str(k): v for k, v in tr["c1_dot_y_ji"].items()},
        "c1_term_total": tr["c1_term_total"],
        "c3_plus_c2_term": tr["c3_plus_c2_term"],
        "z_before_center": tr["z_before_center"],
        "z_centered": tr["z_centered"],
        "noise_residual": tr["noise_residual"],
        "decoded_mu": tr["decoded_mu"],
        "threshold": tr["threshold"],
        "half_q": tr["half_q"],
        "ok": got == mu,
    }

    data = {
        "params": {
            "n": params.n, "m": params.m, "q": params.q, "N": params.N,
            "half_q": params.half_q, "threshold": params.q // 4,
        },
        "params_id": params_id(params),
        "keyset_id": keyset_id(pp, pks),
        "A_shape": list(pp.A.shape), "A_head": _head(pp.A),
        "p_shape": list(pp.p.shape), "p_head": _head(pp.p),
        "users": users,
        "recipient_ids": sorted(s_set),
        "mu": mu,
        "ct": {
            "xi_hex": ct.xi.hex(),
            "c1": [int(x) for x in ct.c1],
            "c2": [int(x) for x in ct.c2],
            "c3": int(ct.c3),
        },
        "W_S_parts": sorted(s_set),
        "W_S_fp": _fp(W_S),
        "trace": trace,
        "hybrid": None,
    }

    if media_bytes is not None:
        data["hybrid"] = _hybrid(pp, pks, sks, s_set, media_bytes, media_name)
    return data


def _hybrid(pp, pks, sks, s_set, media_bytes: bytes, media_name: str) -> dict:
    """真实 hybrid 闭环，并产出「已恢复的媒体文件路径」供 Manim 显示。"""
    key = os.urandom(KEY_LEN)
    wrapped = encrypt_session_key(pp, pks, s_set, key)
    auth_user = sorted(s_set)[0]

    tmp = tempfile.mkdtemp(prefix="chw25manim_")
    src = os.path.join(tmp, "locked.bin")
    with open(src, "wb") as f:
        f.write(media_bytes)
    enc = os.path.join(tmp, "locked.enc")
    encrypt_file_for_set(pp, pks, s_set, src, enc)

    rec = os.path.join(tmp, media_name)
    freq = decrypt_file_for_user(
        pp, pks, s_set, open(enc, "rb").read(), auth_user, sks[auth_user], rec
    )
    recovered = open(rec, "rb").read() if freq.authorized else None

    return {
        "bit_count": 256,
        "key_fingerprint": hashlib.sha256(key).hexdigest()[:8],
        "key_length_bytes": KEY_LEN,
        "media_name": media_name,
        "media_size": len(media_bytes),
        "original_sha256": hashlib.sha256(media_bytes).hexdigest(),
        "recovered_sha256": hashlib.sha256(recovered).hexdigest() if recovered else None,
        "match": recovered == media_bytes,
        "recovered_image_path": rec if freq.authorized else None,
        "original_image_path": src,
    }
