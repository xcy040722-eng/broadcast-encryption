"""CHW25 DBE → AES-256 会话密钥 → AES-GCM 文件（Hybrid 层）。

设计：
- 256 次独立 CHW25 单 bit 加密，包装一个随机 32-byte AES-256 session key。
  （**不**把 Construction 6.4 的 c3 推广为未经论文证明的 multi-bit 编码。）
- 每个 bit 加密使用独立的 ξ / s / e / K_W / k_p（每次都调用 encrypt()）。
- 复用 src/file_crypto 的 AES-256-GCM 文件加密能力，不重新实现 AES。
- 广播包显式包含 recipient_ids = S，并作为 AES-GCM 的 AAD 被认证。

【课程实现】见 docs/chw25-dbe-implementation-spec.md（教学替代项）。
"""

from __future__ import annotations

import base64
import hashlib
import json
import os

import numpy as np
from cryptography.exceptions import InvalidTag

from src.file_crypto.crypto import decrypt_body, encrypt_body
from src.file_crypto.format import DecryptionError

from .construction import decrypt, encrypt
from .types import (
    Ciphertext,
    DecryptResult,
    FileResult,
    Params,
    PublicKey,
    PublicParams,
    SecretKey,
    SessionKeyResult,
)

VERSION = 1
ALGORITHM = "CHW25-DBE-AES256GCM"
KEY_LEN = 32
BIT_LEN = KEY_LEN * 8  # 256


class KeysetMismatchError(Exception):
    """广播包的 keyset_id 与当前 public parameters / 公钥目录不一致。"""


__all__ = [
    "VERSION",
    "ALGORITHM",
    "KEY_LEN",
    "BIT_LEN",
    "KeysetMismatchError",
    "bytes_to_bits",
    "bits_to_bytes",
    "params_id",
    "keyset_id",
    "decrypt_bit",
    "encrypt_session_key",
    "decrypt_session_key",
    "serialize_wrapped_key",
    "deserialize_wrapped_key",
    "serialize_package",
    "deserialize_package",
    "package_aad",
    "build_package",
    "encrypt_file_for_set",
    "decrypt_file_for_user",
]


# ---------- keyset_id：canonical pp + 公钥目录 的 SHA-256 指纹 ----------


def _canonical_matrix(arr) -> list:
    a = np.atleast_2d(np.asarray(arr, dtype=np.int64))
    return [[int(x) for x in row] for row in a]


def _canonical_pp(pp: PublicParams) -> dict:
    params = pp.params
    return {
        "params": {"n": params.n, "m": params.m, "q": params.q, "N": params.N},
        "A": _canonical_matrix(pp.A),
        "p": [int(x) for x in pp.p],
        "R": _canonical_matrix(pp.R),
        "t": _canonical_matrix(pp.t),
    }


def _canonical_directory(public_keys: dict[int, PublicKey]) -> list:
    return [
        {
            "i": int(i),
            "W": _canonical_matrix(pk.W),
            "ys": {str(j): [int(x) for x in y] for j, y in sorted(pk.ys.items())},
        }
        for i, pk in sorted(public_keys.items())
    ]


def keyset_id(pp: PublicParams, public_keys: dict[int, PublicKey]) -> str:
    """canonical public parameters + 公钥目录 的 SHA-256 指纹（64 hex）。

    用于确保旧的 broadcast ciphertext 不会被**新的 key directory** 错误解释。
    """
    doc = {"pp": _canonical_pp(pp), "directory": _canonical_directory(public_keys)}
    blob = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return hashlib.sha256(blob).hexdigest()


# ---------- bit ordering（bytes ⇄ 256 bits，完全可逆）----------


def bytes_to_bits(data: bytes) -> list[int]:
    """bytes → 256 bits，MSB-first（每字节高位在前）。"""
    bits: list[int] = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def bits_to_bytes(bits: list[int]) -> bytes:
    """256 bits → bytes（MSB-first），是 bytes_to_bits 的逆。"""
    if len(bits) % 8 != 0:
        raise ValueError(f"bit 数必须是 8 的倍数，得到 {len(bits)}")
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i : i + 8]:
            byte = (byte << 1) | (b & 1)
        out.append(byte)
    return bytes(out)


def params_id(params: Params) -> str:
    return f"n{params.n}-m{params.m}-q{params.q}-N{params.N}"


# ---------- 单 bit（区分「真 0」与「非接收者」）----------


def decrypt_bit(
    pp: PublicParams,
    public_keys: dict[int, PublicKey],
    s_set: set[int],
    ct: Ciphertext,
    user_id: int,
    sk: SecretKey,
) -> DecryptResult:
    """单 bit 解密，返回应用层状态。

    非接收者 → authorized=False, bit=None（**不是** bit=0）。
    """
    if user_id not in s_set:
        return DecryptResult(authorized=False, bit=None)
    return DecryptResult(authorized=True, bit=decrypt(pp, public_keys, s_set, ct, user_id, sk))


# ---------- session key 包装（256 次独立 bit 加密）----------


def encrypt_session_key(
    pp: PublicParams,
    public_keys: dict[int, PublicKey],
    s_set: set[int],
    key_bytes: bytes,
) -> list[Ciphertext]:
    """把 32-byte 会话密钥包装成 256 个独立 CHW25 密文。"""
    if len(key_bytes) != KEY_LEN:
        raise ValueError(f"session key 必须为 {KEY_LEN} 字节，得到 {len(key_bytes)}")
    # 每个 bit 一次独立 encrypt()：内部各自采样 ξ / s / e / K_W / k_p
    return [encrypt(pp, public_keys, s_set, bit) for bit in bytes_to_bits(key_bytes)]


def decrypt_session_key(
    pp: PublicParams,
    public_keys: dict[int, PublicKey],
    s_set: set[int],
    wrapped_key: list[Ciphertext],
    user_id: int,
    sk: SecretKey,
) -> SessionKeyResult:
    """恢复 32-byte 会话密钥；非接收者 → authorized=False, key=None。"""
    if user_id not in s_set:
        return SessionKeyResult(authorized=False, key=None)
    if len(wrapped_key) != BIT_LEN:
        raise ValueError(f"wrapped_key 必须含 {BIT_LEN} 个密文，得到 {len(wrapped_key)}")
    bits = [
        decrypt(pp, public_keys, s_set, ct, user_id, sk) for ct in wrapped_key
    ]
    return SessionKeyResult(authorized=True, key=bits_to_bytes(bits))


# ---------- wrapped key 序列化 ----------


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _unb64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"), validate=True)


def serialize_wrapped_key(wrapped: list[Ciphertext]) -> list[dict]:
    return [
        {"xi": _b64(ct.xi), "c1": [int(x) for x in ct.c1], "c2": [int(x) for x in ct.c2],
         "c3": int(ct.c3)}
        for ct in wrapped
    ]


def deserialize_wrapped_key(data: list[dict]) -> list[Ciphertext]:
    return [
        Ciphertext(
            xi=_unb64(d["xi"]),
            c1=np.array(d["c1"], dtype=np.int64),
            c2=np.array(d["c2"], dtype=np.int64),
            c3=int(d["c3"]),
        )
        for d in data
    ]


# ---------- 广播包（header 被 AES-GCM 认证）----------


def build_package(
    params: Params,
    recipient_ids: set[int],
    wrapped_key: list[Ciphertext],
    body_nonce: bytes,
    body_ciphertext: bytes,
    original_filename: str,
    original_size: int,
    ks_id: str,
) -> dict:
    return {
        "version": VERSION,
        "algorithm": ALGORITHM,
        "params_id": params_id(params),
        "keyset_id": ks_id,
        "recipient_ids": sorted(recipient_ids),
        "wrapped_key": serialize_wrapped_key(wrapped_key),
        "body": {"nonce": _b64(body_nonce), "ciphertext": _b64(body_ciphertext)},
        "original_filename": original_filename,
        "original_size": original_size,
    }


def package_aad(pkg: dict) -> bytes:
    """AAD：认证**全部语义 header**。

    认证字段：version, algorithm, params_id, keyset_id, recipient_ids,
              original_filename, original_size, wrapped_key。
    规范化（sort_keys + 固定 separators + UTF-8），加密与解密逐字节一致。
    篡改任一字段都会导致 GCM 认证失败。
    """
    header = {
        "version": pkg["version"],
        "algorithm": pkg["algorithm"],
        "params_id": pkg["params_id"],
        "keyset_id": pkg["keyset_id"],
        "recipient_ids": list(pkg["recipient_ids"]),
        "original_filename": pkg["original_filename"],
        "original_size": pkg["original_size"],
        "wrapped_key": pkg["wrapped_key"],  # 已为 JSON 可序列化形式
    }
    return json.dumps(header, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def serialize_package(pkg: dict) -> bytes:
    return json.dumps(pkg).encode("utf-8")


def deserialize_package(data: bytes) -> dict:
    try:
        d = json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"非法 package：{exc}") from exc
    if not isinstance(d, dict):
        raise ValueError("package 顶层必须是对象")
    if d.get("version") != VERSION:
        raise ValueError(f"不支持的 version：{d.get('version')!r}")
    if d.get("algorithm") != ALGORITHM:
        raise ValueError(f"未知 algorithm：{d.get('algorithm')!r}")
    for key in ("params_id", "keyset_id", "recipient_ids", "wrapped_key", "body",
                "original_filename", "original_size"):
        if key not in d:
            raise ValueError(f"缺少字段：{key}")
    return d


# ---------- 文件层 ----------


def encrypt_file_for_set(
    pp: PublicParams,
    public_keys: dict[int, PublicKey],
    s_set: set[int],
    input_path: str,
    output_path: str,
    overwrite: bool = False,
) -> dict:
    """CHW25 DBE 保护 AES-256 会话密钥 + AES-GCM 加密文件内容。"""
    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output_path}")

    with open(input_path, "rb") as f:
        plaintext = f.read()

    key = os.urandom(KEY_LEN)  # secrets 级随机
    wrapped = encrypt_session_key(pp, public_keys, s_set, key)
    ks_id = keyset_id(pp, public_keys)  # canonical pp + 目录 的指纹

    pkg = build_package(
        pp.params, s_set, wrapped, b"", b"",
        os.path.basename(input_path), len(plaintext), ks_id,
    )
    # header 作为 AAD（先建包 → 取 AAD → 加密 body）
    aad = package_aad(pkg)
    nonce, body_ct = encrypt_body(key, plaintext, aad)
    pkg = build_package(
        pp.params, s_set, wrapped, nonce, body_ct,
        os.path.basename(input_path), len(plaintext), ks_id,
    )

    with open(output_path, "wb") as f:
        f.write(serialize_package(pkg))
    return pkg


def decrypt_file_for_user(
    pp: PublicParams,
    public_keys: dict[int, PublicKey],
    s_set: set[int],
    package_bytes: bytes,
    user_id: int,
    sk: SecretKey,
    output_path: str,
    overwrite: bool = False,
) -> FileResult:
    """非接收者 → FileResult(authorized=False)；keyset 不匹配 → KeysetMismatchError；

    认证失败 → DecryptionError。
    """
    pkg = deserialize_package(package_bytes)

    # keyset 校验：确保旧密文不会被新的 pp / 公钥目录错误解释
    if pkg["keyset_id"] != keyset_id(pp, public_keys):
        raise KeysetMismatchError(
            "广播包的 keyset_id 与当前 public parameters / 公钥目录不一致"
        )

    wrapped = deserialize_wrapped_key(pkg["wrapped_key"])
    result = decrypt_session_key(pp, public_keys, s_set, wrapped, user_id, sk)
    if not result.authorized:
        return FileResult(authorized=False, output_path=None)

    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output_path}")

    aad = package_aad(pkg)  # 与加密时逐字节一致；篡改 header → InvalidTag
    try:
        plaintext = decrypt_body(
            result.key, _unb64(pkg["body"]["nonce"]), _unb64(pkg["body"]["ciphertext"]), aad
        )
    except InvalidTag as exc:
        raise DecryptionError(
            "AES-GCM 认证失败（会话密钥错误，或 body/header 被篡改）"
        ) from exc
    with open(output_path, "wb") as f:
        f.write(plaintext)
    return FileResult(authorized=True, output_path=output_path)
