"""Encrypt 与 Decrypt —— 会话密钥的广播加密（NNL01 header 部分）。"""

from __future__ import annotations

from cryptography.exceptions import InvalidTag

from .crypto import decrypt_key, encrypt_key


def encrypt_session_key(
    node_keys: dict[int, bytes], cover_roots: list[int], session_key: bytes
) -> dict:
    """用覆盖子集密钥加密会话密钥，构成 header。

    对应原文 header = ( [i_1..i_m], E_{L_i1}(K), ..., E_{L_im}(K) )。
    session_key 只以 AES-GCM 密文形式出现，从不明文存入 header。
    """
    indices = list(cover_roots)
    encrypted = [encrypt_key(node_keys[i], session_key) for i in indices]
    return {"indices": indices, "encrypted": encrypted}


def decrypt_session_key(user_key: dict[int, bytes], header: dict) -> bytes | None:
    """用户用私钥从 header 恢复会话密钥。

    命中条件：header 中某索引 i 在用户路径密钥中（即 v_i 是用户祖先 / 用户 ∈ S_i）。
    返回 None 表示无法恢复（用户被撤销无命中，或命中的 GCM 认证失败）。
    结构错误（indices/encrypted 长度不一致等）会抛出异常，不吞掉。
    """
    indices = header["indices"]
    encrypted = header["encrypted"]
    if len(indices) != len(encrypted):
        raise ValueError(
            f"header 字段长度不一致：indices={len(indices)}, encrypted={len(encrypted)}"
        )
    for i, blob in zip(indices, encrypted):
        if i in user_key:
            try:
                return decrypt_key(user_key[i], blob)
            except InvalidTag:
                return None
    return None
