"""媒体 Demo 页面（PNG/JPEG/MP4 闭环）。"""

from __future__ import annotations

import hashlib
import os
import tempfile

import streamlit as st

from src.cs.keys import keygen
from src.file_crypto import DecryptionError, decrypt_file, encrypt_file
from demo.media_data import MEDIA


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def render_media_page(tree, node_keys, revoked_users: set[int]) -> None:
    st.subheader("媒体文件闭环（CS + AES-256-GCM）")
    st.caption("文件 → AES-GCM 加密 → CS 广播加密会话密钥 K → 授权恢复 → 文件解密")

    media_name = st.selectbox("选择媒体文件", list(MEDIA.keys()))
    data = MEDIA[media_name]

    authorized = [u for u in range(1, tree.N + 1) if u not in revoked_users]
    u_auth = st.selectbox("授权解密用户", authorized)

    if st.button("🔒 加密媒体文件"):
        tmp = tempfile.mkdtemp()
        src = os.path.join(tmp, "media.bin")
        enc = os.path.join(tmp, "media.enc")
        with open(src, "wb") as f:
            f.write(data)
        encrypt_file(src, enc, tree, node_keys, revoked_users)
        st.session_state.media_enc = enc
        st.session_state.media_data = data
        st.session_state.media_name = media_name
        st.session_state.media_src_sha = _sha256(data)

    if "media_enc" not in st.session_state:
        st.info("点击上方按钮，生成「同一份广播密文」后再解密。")
        return

    enc = st.session_state.media_enc
    src_sha = st.session_state.media_src_sha

    out = os.path.join(os.path.dirname(enc), "dec.bin")
    decrypt_file(enc, out, keygen(tree, node_keys, u_auth))
    with open(out, "rb") as f:
        dec_data = f.read()
    dec_sha = _sha256(dec_data)

    st.markdown("**同一份密文** 的 SHA-256 校验：")
    st.markdown(f"- Original SHA-256: `{src_sha}`")
    st.markdown(f"- Decrypted SHA-256: `{dec_sha}`")
    if dec_sha == src_sha:
        st.success("Original SHA-256 == Decrypted SHA-256 ✓")
    else:
        st.error("SHA-256 不一致 ✗")

    if media_name in ("image_png", "image_jpeg"):
        c1, c2 = st.columns(2)
        with c1:
            st.image(st.session_state.media_data, caption="原文件")
        with c2:
            st.image(dec_data, caption="解密文件")
    else:
        st.caption("（MP4 为演示字节，只做 SHA-256 校验，不播放）")

    if revoked_users:
        u_rev = sorted(revoked_users)[0]
        try:
            decrypt_file(
                enc, os.path.join(os.path.dirname(enc), "rev.bin"), keygen(tree, node_keys, u_rev)
            )
            st.error(f"撤销用户 u{u_rev} 意外解密成功 ✗")
        except DecryptionError:
            st.warning(f"撤销用户 u{u_rev} 无法解密（DecryptionError）✓")
