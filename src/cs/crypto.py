"""密码原语层 —— ENGINEERING ADAPTATION。

NNL01 原文的 E_L（header 加密会话密钥）是抽象块密码、F_K（body 加密消息）是抽象流密码。
本阶段用 AES-256-GCM 具体化 E_L（认证加密），随机源统一使用 `secrets`（密码学安全）。
F_K（文件内容加密）在 Prompt 06 混合加密阶段实现，此处不涉及。
"""

from __future__ import annotations

import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_LEN = 32  # 256-bit，AES-256
NONCE_LEN = 12  # 96-bit，GCM 推荐 nonce 长度


def random_key() -> bytes:
    """生成随机对称密钥（secrets.token_bytes，密码学安全）。"""
    return secrets.token_bytes(KEY_LEN)


def encrypt_key(key: bytes, plaintext: bytes) -> bytes:
    """用 AES-256-GCM 加密 plaintext，返回 nonce || ciphertext||tag。

    对应 NNL01 的 E_L：用长寿命密钥 key 加密会话密钥 K。
    """
    if len(key) != KEY_LEN:
        raise ValueError(f"密钥长度必须为 {KEY_LEN} 字节")
    nonce = secrets.token_bytes(NONCE_LEN)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ct


def decrypt_key(key: bytes, blob: bytes) -> bytes:
    """解密 encrypt_key 的输出；认证失败抛 InvalidTag。"""
    if len(key) != KEY_LEN:
        raise ValueError(f"密钥长度必须为 {KEY_LEN} 字节")
    if len(blob) < NONCE_LEN + 16:
        raise ValueError("密文过短")
    nonce = blob[:NONCE_LEN]
    ct = blob[NONCE_LEN:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)
