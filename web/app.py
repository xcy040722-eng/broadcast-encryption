"""CS 广播加密可视化演示（Streamlit）。

启动：streamlit run web/app.py
"""

from __future__ import annotations

import streamlit as st

from src.cs import (
    cover,
    decrypt_session_key,
    encrypt_session_key,
    keygen,
    random_key,
    setup,
)
from web.cs_visualize import fingerprint, hidden_key, tree_to_dot, verify_cover
from web.media_page import render_media_page

st.set_page_config(page_title="CS 广播加密演示", layout="wide")
st.title("Complete Subtree 广播加密 — 可视化演示")
st.caption("Naor–Naor–Lotspiech 2001（NNL01）§3.1 Complete Subtree Method")


def _reset_session():
    for k in ("session_key", "header", "cover_roots", "media_enc"):
        st.session_state.pop(k, None)


# ---------- 侧边栏 ----------
with st.sidebar:
    st.header("系统参数")
    N = st.selectbox("用户数 N", [8, 16, 32], index=0)
    if st.button("⚙️ 生成系统", use_container_width=True):
        tree, node_keys = setup(N)
        st.session_state.tree = tree
        st.session_state.node_keys = node_keys
        st.session_state.revoked = set()
        _reset_session()
    st.divider()
    st.caption("一键演示：N=8，撤销 R={3,5}")

# ---------- Run Demo ----------
if st.button("▶ Run Demo（N=8, R={3,5}）", type="primary", use_container_width=True):
    tree, node_keys = setup(8)
    st.session_state.tree = tree
    st.session_state.node_keys = node_keys
    st.session_state.revoked = {3, 5}
    _reset_session()
    K = random_key()
    cover_roots = cover(tree, {3, 5})
    header = encrypt_session_key(node_keys, cover_roots, K)
    st.session_state.session_key = K
    st.session_state.header = header
    st.session_state.cover_roots = cover_roots

# ---------- 主区 ----------
if "tree" not in st.session_state:
    st.info("在侧边栏选择 N 并点击「生成系统」，或点击上方「▶ Run Demo」一键开始。")
else:
    tree = st.session_state.tree
    node_keys = st.session_state.node_keys
    revoked = st.session_state.revoked

    tab1, tab2, tab3, tab4 = st.tabs(
        ["① Setup & KeyGen", "② Revocation & Cover", "③ Encrypt / Decrypt", "④ 媒体 Demo"]
    )

    # ---- Tab 1：Setup + KeyGen ----
    with tab1:
        st.subheader("完全二叉树（用户 = 叶子）")
        st.caption("叶子显示「用户编号 u_j + 节点编号 v_i」；内部节点显示「节点编号 v_i」")
        u_sel = st.selectbox("选择用户查看 KeyGen 根→叶路径", list(range(1, tree.N + 1)))
        leaf = tree.leaf_of_user(u_sel)
        path_nodes = set(tree.ancestors(leaf))
        st.graphviz_chart(tree_to_dot(tree, path_nodes=path_nodes))
        st.markdown(
            f"蓝色 = 用户 **u{u_sel}** 的根→叶密钥路径（共 **{len(path_nodes)}** 个节点密钥："
            f"`{sorted(path_nodes)}`）"
        )

    # ---- Tab 2：Revocation + Cover ----
    with tab2:
        st.subheader("撤销集合 R 与 Complete Subtree Cover")
        revoked_list = st.multiselect(
            "选择撤销用户 R", list(range(1, tree.N + 1)), default=sorted(revoked)
        )
        revoked = set(revoked_list)
        st.session_state.revoked = revoked

        cover_roots = cover(tree, revoked)
        st.graphviz_chart(tree_to_dot(tree, revoked_users=revoked, cover_roots=cover_roots))
        st.caption("红色 = 撤销用户；深绿 = cover root；浅绿 = cover 子树（覆盖 N\\R）")

        st.markdown(f"**Cover 数量 = {len(cover_roots)}**　cover roots = `{cover_roots}`")
        result = verify_cover(tree, cover_roots, revoked)
        st.markdown("**Correctness 验证：**")
        st.markdown(f"- Union(Cover) = N − R：`{'✓' if result['union_ok'] else '✗'}`")
        st.markdown(f"- Cover ∩ R = ∅：`{'✓' if result['no_revoked_ok'] else '✗'}`")
        st.markdown(f"- pairwise disjoint：`{'✓' if result['disjoint_ok'] else '✗'}`")

    # ---- Tab 3：Encrypt / Decrypt ----
    with tab3:
        st.subheader("Broadcast Encrypt / Decrypt（同一个 Header）")
        if st.button("🔑 生成会话密钥并广播加密"):
            cover_roots = cover(tree, revoked)
            K = random_key()
            header = encrypt_session_key(node_keys, cover_roots, K)
            st.session_state.session_key = K
            st.session_state.header = header
            st.session_state.cover_roots = cover_roots

        if "session_key" in st.session_state:
            K = st.session_state.session_key
            header = st.session_state.header
            st.markdown(f"**Session Key K**：`{hidden_key(K)}`（明文永不显示）")
            st.markdown(
                f"**Broadcast Header**：{len(header['indices'])} 个 entry，"
                f"indices = `{header['indices']}`"
            )
            st.caption("同一份 Header，依次选择任意用户尝试解密：")
            u_try = st.selectbox("选择尝试解密的用户", list(range(1, tree.N + 1)))
            got = decrypt_session_key(keygen(tree, node_keys, u_try), header)
            if got is not None and got == K:
                st.success(
                    f"用户 u{u_try}：**Recovered ✓**（恢复的 K 指纹 = `{fingerprint(got)}`）"
                )
            else:
                st.error(f"用户 u{u_try}：**Rejected ✗**（无权限恢复会话密钥）")
        else:
            st.info("点击上方按钮生成会话密钥与 Header（或先 Run Demo）。")

    # ---- Tab 4：媒体 Demo ----
    with tab4:
        render_media_page(tree, node_keys, revoked)
