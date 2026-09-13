"""CHW25 DBE 可视化：payload 构造 + HTML/SVG/JS 组件渲染。

设计原则：
- **所有数值来自 src/chw25_dbe 的真实 API 与 trace**；前端 JS 只读 payload，不重算公式。
- 播放控制（Play/Pause/Prev/Next/Replay）在组件内部，避免 Streamlit rerun 导致 SVG 闪烁。
- 组件只读 payload。

见 docs/chw25-visualization-design.md。
"""

from __future__ import annotations

import hashlib
import json
import os

import numpy as np
import streamlit.components.v1 as components

from src.chw25_dbe import (
    BIT_LEN,
    KEY_LEN,
    Params,
    decrypt_bit,
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


def _sha8(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:8]


STAGES = [
    "setup", "keygen", "select_s", "encrypt",
    "broadcast", "decrypt", "recover", "media",
]


def _scenario_id(s_set: set[int], mu: int) -> str:
    """(S, μ) 的签名：用于检测「旧 trace 被复用」。"""
    payload = json.dumps({"S": sorted(s_set), "mu": mu}, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()[:12]


def visible_keyset_id(payload: dict, stage: str) -> str | None:
    """keyset_id 的阶段门控：KeyGen 之前返回 None（前端显示 Pending）。

    keyset_id 依赖公钥目录，Setup 阶段尚不存在。
    """
    ks = payload["keyset"]
    stages = payload["stages"]
    if stages.index(stage) >= stages.index(ks["reveal_stage"]):
        return ks["value"]
    return None


class StageCursor:
    """阶段游标（与前端 JS 语义一致）：Prev / Next / Replay(reset) 可测。"""

    def __init__(self, stages: list[str]):
        self.stages = list(stages)
        self.index = 0
        self.dec_phase = 0          # decrypt 子阶段 0..4

    def next(self) -> int:
        if self.stages[self.index] == "decrypt" and self.dec_phase < 4:
            self.dec_phase += 1
        elif self.index < len(self.stages) - 1:
            self.index += 1
            self.dec_phase = 0
        return self.index

    def prev(self) -> int:
        if self.index > 0:
            self.index -= 1
            self.dec_phase = 0
        return self.index

    def reset(self) -> int:
        """Replay：回到第一阶段并清零 decrypt 子阶段。"""
        self.index = 0
        self.dec_phase = 0
        return self.index


def _mat_fp(arr: np.ndarray) -> str:
    """矩阵/向量的短指纹（不含完整数值）。"""
    return hashlib.sha256(np.asarray(arr, dtype=np.int64).tobytes()).hexdigest()[:8]


def _head(arr, k: int = 3) -> list:
    """仅取前 k 个数值用于展示（避免完整展开）。"""
    flat = np.asarray(arr, dtype=np.int64).ravel()
    return [int(x) for x in flat[:k]]


# ---------- bit-level payload ----------


def build_payload(N: int = 4, s_set: set[int] | None = None, mu: int = 1) -> dict:
    """运行一次真实 bit-level demo，构造前端 payload（全部数值来自真实 trace）。"""
    s_set = {2, 4} if s_set is None else set(s_set)
    params = Params(N=N, m=max(8, N))
    pp = setup(params)

    pks, sks = {}, {}
    for i in range(1, N + 1):
        pk, sk = keygen(pp, i)
        pks[i], sks[i] = pk, sk

    ks_id = keyset_id(pp, pks)

    # 用户卡片（含 Eq.(6.6)/(6.7) 验证结果）
    users = []
    for i in range(1, N + 1):
        eq67 = all(
            bool(np.array_equal(
                (pp.A @ pks[i].ys[j]) % params.q,
                (pks[i].W @ pp.R[:, j - 1]) % params.q,
            ))
            for j in range(1, N + 1) if j != i
        )
        eq66 = bool(np.array_equal(
            (pp.A @ sks[i].y) % params.q,
            (pks[i].W @ pp.R[:, i - 1] + pp.p) % params.q,
        ))
        users.append({
            "id": i,
            "W_shape": list(pks[i].W.shape),
            "W_fingerprint": _mat_fp(pks[i].W),
            "W_head": _head(pks[i].W),
            "cross_terms": {str(j): _mat_fp(y) for j, y in sorted(pks[i].ys.items())},
            "self_term_marker": "PRIVATE",           # y_{i,i} 不展示完整向量
            "self_term_fingerprint": _mat_fp(sks[i].y),
            "eq66_ok": eq66,
            "eq67_ok": eq67,
            "is_recipient": i in s_set,
        })

    # 加密 + 密文
    ct = encrypt(pp, pks, s_set, mu)
    W_S = np.zeros_like(pks[1].W)
    for j in s_set:
        W_S = (W_S + pks[j].W) % params.q

    # trace（授权用 decrypt_with_trace，非授权用 decrypt_bit）
    traces: dict[str, dict] = {}
    for i in range(1, N + 1):
        if i in s_set:
            got, tr = decrypt_with_trace(pp, pks, s_set, ct, i, sks[i])
            traces[str(i)] = {
                "authorized": True,
                "bit": got,
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
            }
        else:
            res = decrypt_bit(pp, pks, s_set, ct, i, sks[i])
            traces[str(i)] = {
                "authorized": False,
                "bit": None,
                "reason": "i ∉ S",
            }

    return {
        "stages": STAGES,
        "params": {
            "n": params.n, "m": params.m, "q": params.q, "N": params.N,
            "half_q": params.half_q, "threshold": params.q // 4,
        },
        "params_id": params_id(params),
        # keyset_id 依赖「公钥目录」，KeyGen 之后才存在 → 阶段门控
        "keyset": {
            "pending_text": "Pending — generated after KeyGen",
            "reveal_stage": "keygen",
            "value": ks_id,
        },
        # 场景签名：S / μ 变化后旧 trace 不得复用
        "scenario": {"S": sorted(s_set), "mu": mu},
        "scenario_id": _scenario_id(s_set, mu),
        "public_values": {
            "A_shape": list(pp.A.shape), "A_head": _head(pp.A),
            "p_shape": list(pp.p.shape), "p_head": _head(pp.p),
            "R_shape": list(pp.R.shape),
        },
        "users": users,
        "recipient_ids": sorted(s_set),
        "mu": mu,
        "ciphertext": {
            "xi_hex": ct.xi.hex(),
            "c1": [int(x) for x in ct.c1],
            "c2": [int(x) for x in ct.c2],
            "c3": int(ct.c3),
            "W_S_fingerprint": _mat_fp(W_S),
            "W_S_parts": [int(j) for j in sorted(s_set)],
        },
        "traces": traces,
        "threshold": {"q": params.q, "half_q": params.half_q, "quarter_q": params.q // 4},
        "hybrid_progress": None,
    }


# ---------- hybrid payload ----------


def build_hybrid_payload(
    payload: dict,
    media_bytes: bytes,
    filename: str,
) -> dict:
    """在已有 bit payload 基础上，加 hybrid（256-bit key + AES-GCM）真实数据。"""
    params = Params(N=payload["params"]["N"], m=max(8, payload["params"]["N"]))
    pp = setup(params)
    pks, sks = {}, {}
    for i in range(1, params.N + 1):
        pk, sk = keygen(pp, i)
        pks[i], sks[i] = pk, sk
    s_set = set(payload["recipient_ids"])

    # 真实 256-bit 会话密钥包装
    key = os.urandom(KEY_LEN)
    wrapped = encrypt_session_key(pp, pks, s_set, key)

    # 真实逐 bit 恢复（授权用户 = S 中第一个）—— 只记录「是否恢复」与进度，不导出 key 内容
    from src.chw25_dbe import decrypt_session_key
    auth_user = sorted(s_set)[0]
    res = decrypt_session_key(pp, pks, s_set, wrapped, auth_user, sks[auth_user])
    recovered_ok = res.authorized and res.key is not None
    # 仅用于一致性校验（不进入 payload）
    assert (res.key == key) if recovered_ok else True

    # 真实媒体闭环
    import tempfile

    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, "media.bin")
    with open(src, "wb") as f:
        f.write(media_bytes)
    enc = os.path.join(tmp, "media.enc")
    encrypt_file_for_set(pp, pks, s_set, src, enc)
    out = os.path.join(tmp, "media.out")
    fres = decrypt_file_for_user(
        pp, pks, s_set, open(enc, "rb").read(), auth_user, sks[auth_user], out
    )
    ok = fres.authorized and open(out, "rb").read() == media_bytes

    # 代表性 bit（默认 bit 0）的完整 trace
    rep_trace = None
    if s_set:
        passed, tr = decrypt_with_trace(pp, pks, s_set, wrapped[0], auth_user, sks[auth_user])
        rep_trace = {
            "authorized": True, "bit": passed,
            "c3": tr["c3"], "c2_dot_r_i": tr["c2_dot_r_i"],
            "c1_dot_y_ii": tr["c1_dot_y_ii"], "c1_dot_y_0i": tr["c1_dot_y_0i"],
            "c1_dot_y_ji": {str(k): v for k, v in tr["c1_dot_y_ji"].items()},
            "c1_term_total": tr["c1_term_total"],
            "z_centered": tr["z_centered"], "noise_residual": tr["noise_residual"],
            "decoded_mu": tr["decoded_mu"], "threshold": tr["threshold"],
            "half_q": tr["half_q"],
        }

    payload = dict(payload)
    payload["hybrid_progress"] = {
        # **不**导出任何 session-key 字节（含前后缀 hex）；仅指纹 + 长度 + 恢复状态
        "key_fingerprint": _sha8(key),
        "key_length_bytes": KEY_LEN,
        "key_recovered": bool(recovered_ok),
        # 网格是 aggregate / progress 可视化（**非**真实逐 bit streaming callback）
        "grid_kind": "aggregate-progress",
        "grid_note": "aggregate / progress visualization — not a real per-bit streaming callback",
        "bit_count": BIT_LEN,
        "recovered_count": BIT_LEN if recovered_ok else 0,
        "auth_user": auth_user,
        "wrapped_size_bytes": len(json.dumps(
            [{"xi": ct.xi.hex(), "c1": [int(x) for x in ct.c1],
              "c2": [int(x) for x in ct.c2], "c3": int(ct.c3)} for ct in wrapped]
        )),
        "representative_bit_trace": rep_trace,
        "media": {
            "filename": filename,
            "size": len(media_bytes),
            "original_sha256": hashlib.sha256(media_bytes).hexdigest(),
            "recovered_sha256": hashlib.sha256(media_bytes).hexdigest() if ok else None,
            "match": ok,
        },
    }
    return payload


# ---------- 渲染 ----------

_HTML_PATH = os.path.join(os.path.dirname(__file__), "chw25_stage.html")


def _load_template() -> str:
    """加载舞台模板（HTML/CSS/SVG/JS）。"""
    with open(_HTML_PATH, encoding="utf-8") as f:
        return f.read()


def render(payload: dict, height: int = 560) -> None:
    """把 payload 嵌入独立 HTML 组件（前端只读）。"""
    blob = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    html = _load_template().replace("__PAYLOAD__", blob).replace("__H__", str(height - 20))
    components.html(html, height=height, scrolling=False)
