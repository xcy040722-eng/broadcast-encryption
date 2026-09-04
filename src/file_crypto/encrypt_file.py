"""文件级混合加密：encrypt_file。"""

from __future__ import annotations

import os

from src.cs.cover import cover
from src.cs.crypto import random_key
from src.cs.encrypt import encrypt_session_key

from .crypto import encrypt_body
from .format import ALGORITHM, VERSION, build_aad, build_package, serialize_package


def encrypt_file(
    input_path: str,
    output_path: str,
    tree,
    node_keys: dict[int, bytes],
    revoked_users: set[int],
    overwrite: bool = False,
) -> None:
    """加密文件：AES-256-GCM 加密内容 + CS 广播加密会话密钥。

    - 每个文件生成新的随机 256-bit 会话密钥 K。
    - CS 只负责保护 K；文件内容由 AES-256-GCM 保护。
    - 不覆盖已存在的输出文件（除非 overwrite=True）。
    """
    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output_path}")

    with open(input_path, "rb") as f:
        plaintext = f.read()

    original_filename = os.path.basename(input_path)
    original_size = len(plaintext)

    session_key = random_key()
    cover_roots = cover(tree, revoked_users)
    cs_header = encrypt_session_key(node_keys, cover_roots, session_key)

    aad = build_aad(VERSION, ALGORITHM, original_filename, original_size, cs_header)
    body_nonce, body_ciphertext = encrypt_body(session_key, plaintext, aad)

    pkg = build_package(original_filename, original_size, cs_header, body_nonce, body_ciphertext)
    data = serialize_package(pkg)

    with open(output_path, "wb") as f:
        f.write(data)
