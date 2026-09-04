"""文件级混合解密：decrypt_file。"""

from __future__ import annotations

import os

from cryptography.exceptions import InvalidTag

from src.cs.encrypt import decrypt_session_key

from .crypto import decrypt_body
from .format import DecryptionError, build_aad, deserialize_package


def decrypt_file(
    encrypted_path: str,
    output_path: str,
    user_key: dict[int, bytes],
    overwrite: bool = False,
) -> None:
    """解密文件：CS 恢复会话密钥 + AES-256-GCM 解密内容。

    安全保证：
    - 撤销用户 / header 篡改 → 无法恢复 K → DecryptionError。
    - body / nonce / AAD 篡改 → GCM 认证失败 → DecryptionError。
    - 仅在内存完成 GCM 认证通过后才写输出文件，绝不留下部分明文。
    - 不覆盖已存在的输出文件（除非 overwrite=True）。
    """
    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output_path}")

    with open(encrypted_path, "rb") as f:
        data = f.read()

    pkg = deserialize_package(data)

    # 1) CS 恢复会话密钥 K
    try:
        session_key = decrypt_session_key(user_key, pkg["cs_header"])
    except ValueError as exc:
        raise DecryptionError("CS header 结构错误") from exc
    if session_key is None:
        raise DecryptionError("无法恢复会话密钥（用户被撤销或 header 被篡改）")

    # 2) AES-256-GCM 解密（内存认证）
    aad = build_aad(
        pkg["version"],
        pkg["algorithm"],
        pkg["original_filename"],
        pkg["original_size"],
        pkg["cs_header"],
    )
    try:
        plaintext = decrypt_body(
            session_key, pkg["body"]["nonce"], pkg["body"]["ciphertext"], aad
        )
    except InvalidTag as exc:
        raise DecryptionError("AES-GCM 认证失败（body/nonce/AAD 被篡改）") from exc

    # 3) 长度一致性校验
    if len(plaintext) != pkg["original_size"]:
        raise DecryptionError("解密结果长度与 original_size 不一致")

    # 4) 认证通过后才写文件
    with open(output_path, "wb") as f:
        f.write(plaintext)
