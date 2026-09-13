"""CHW25 DBE Visualization Lab（Streamlit 多页）。

主流程：Setup → KeyGen → Select S → Encrypt → Broadcast → Decrypt
        → Recover Session Key → AES-GCM Media Recovery

- 所有数值来自 src/chw25_dbe 的真实 API 与 trace。
- 前端组件只读 payload；播放控制在组件内（避免 rerun 闪烁）。
- **不改 web/app.py**（CS 页面）；通过 Streamlit 多页机制并存。
"""

from __future__ import annotations

import streamlit as st

from demo.media_data import PNG_BYTES
from web.components.chw25_visualizer import build_hybrid_payload, build_payload, render

st.set_page_config(page_title="CHW25 DBE Lab", layout="wide")

st.title("CHW25 Broadcast Encryption Visualization Lab")
st.caption(
    "CHW25 Construction 6.4（Distributed Broadcast Encryption）· 教学实现 · "
    "所有数值来自真实运行 trace"
)

# ---------- 侧边栏：控制面板 ----------
with st.sidebar:
    st.header("控制面板")

    N = st.selectbox("用户数 N", [4, 8], index=0)
    default_S = [i for i in (2, 4) if i <= N]
    S_sel = st.multiselect(
        "广播集合 S（默认 {2,4}）", list(range(1, N + 1)), default=default_S
    )
    mu = st.radio("消息 bit μ", [0, 1], index=1, horizontal=True)

    st.divider()
    run_bit = st.button("▶ 运行 Bit Demo", use_container_width=True, type="primary")

    st.divider()
    st.subheader("Hybrid Media")
    up = st.file_uploader("上传图片 / 二进制（默认内置 PNG）", type=None)
    run_hybrid = st.button("▶ 运行 Hybrid Demo", use_container_width=True)

    st.divider()
    show_internal = st.checkbox("教学模式：显示内部变量", value=False)
    st.caption("关闭时仅显示指纹与派生标量；**私钥与会话密钥永不显示明文**。")

    st.divider()
    st.caption("播放控制（Play/Pause/Prev/Next/Replay）在中央舞台底部——"
               "动画在组件内完成，不触发 Streamlit rerun。")

# ---------- 状态 ----------
if "chw25_payload" not in st.session_state:
    st.session_state.chw25_payload = build_payload(N=4, s_set={2, 4}, mu=1)

if run_bit:
    s_set = set(S_sel) if S_sel else {2, 4}
    st.session_state.chw25_payload = build_payload(N=N, s_set=s_set, mu=mu)

if run_hybrid:
    media = up.read() if up is not None else PNG_BYTES
    fname = up.name if up is not None else "builtin.png"
    base = st.session_state.chw25_payload
    with st.spinner("运行 hybrid demo（256 bit 包装 + AES-GCM）…"):
        st.session_state.chw25_payload = build_hybrid_payload(base, media, fname)

payload = st.session_state.chw25_payload

# ---------- 顶部：参数与阶段进度 ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("N / m / q", f"{payload['params']['N']} / {payload['params']['m']} / {payload['params']['q']}")
c2.metric("params_id", payload["params_id"])
c3.metric("keyset_id", payload["keyset"]["value"][:8] + "…")
c4.metric("S（recipients）", "{" + ", ".join(map(str, payload["recipient_ids"])) + "}")

st.markdown(
    "阶段： " + " → ".join(f"**{i+1}. {s}**" for i, s in enumerate(payload["stages"]))
)

# ---------- 中央：动画舞台 ----------
render(payload, height=580)

# ---------- 下方：真实变量 / 公式解释 ----------
with st.expander("真实变量 / 公式解释面板", expanded=False):
    left, right = st.columns(2)
    with left:
        st.markdown("**公开变量**")
        st.json({
            "params": payload["params"],
            "params_id": payload["params_id"],
            "keyset_id": payload["keyset"]["value"][:16] + "…",
            "keyset_reveal_stage": payload["keyset"]["reveal_stage"],
            "scenario_id": payload["scenario_id"],
            "recipient_ids": payload["recipient_ids"],
            "ciphertext": {
                "xi": payload["ciphertext"]["xi_hex"][:16] + "…",
                "c1": payload["ciphertext"]["c1"],
                "c2": payload["ciphertext"]["c2"],
                "c3": payload["ciphertext"]["c3"],
                "W_S_parts": payload["ciphertext"]["W_S_parts"],
            },
        })
    with right:
        st.markdown("**Decrypt trace（真实值）**")
        for uid, tr in payload["traces"].items():
            if tr["authorized"]:
                st.markdown(
                    f"**u{uid}** authorized · z_centered=`{tr['z_centered']}` · "
                    f"noise=`{tr['noise_residual']}` · decoded μ=`{tr['decoded_mu']}` "
                    f"(q/4=`{tr['threshold']}`)"
                )
            else:
                st.markdown(f"**u{uid}** NotRecipient（u{uid} ∉ S）")

    st.markdown("---")
    st.markdown("**公式**")
    st.latex(r"z = c_3 + c_2^T r_i - c_1^T\Big(y_{i,i} + y_{0,i} + \sum_{j\in S\setminus\{i\}} y_{j,i}\Big)")
    st.latex(r"\lfloor z\rfloor = 0 \iff -q/4 \le z < q/4;\quad \text{否则 } 1")
    st.caption(
        "本页只调用 src/chw25_dbe 的现有 API 与 trace；前端不重新实现任何密码学公式。"
        "非接收者显示为 NotRecipient（authorized=false, bit=None），**不会**显示为「解密为 0」。"
    )
