"""文件级 body 的 AES-256-GCM 加密 —— ENGINEERING ADAPTATION。

与 CS 内部（src/cs/crypto.py）的 AES-GCM 是两层独立的 GCM：
- CS header 层：L_i 加密会话密钥 K（src/cs/crypto.py）
- 文件 body 层：K 加密文件内容（本文件）

两层 nonce 各自独立生成、独立存储，绝不混用。
"""

from __future__ import annotations

import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BODY_NONCE_LEN = 12  # 96-bit


def encrypt_body(session_key: bytes, plaintext: bytes, aad: bytes) -> tuple[bytes, bytes]:
    """AES-256-GCM 加密文件内容，返回 (nonce, ciphertext||tag)。"""
    if len(session_key) != 32:
        raise ValueError("session key 必须为 32 字节")
    nonce = secrets.token_bytes(BODY_NONCE_LEN)
    aesgcm = AESGCM(session_key)
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce, ct


def decrypt_body(session_key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes:
    """AES-256-GCM 解密文件内容；认证失败抛 cryptography.exceptions.InvalidTag。"""
    if len(session_key) != 32:
        raise ValueError("session key 必须为 32 字节")
    if len(nonce) != BODY_NONCE_LEN:
        raise ValueError("body nonce 长度错误")
    aesgcm = AESGCM(session_key)
    return aesgcm.decrypt(nonce, ciphertext, aad)
