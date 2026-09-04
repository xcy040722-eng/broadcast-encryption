"""文件容器格式：版本化、序列化/反序列化、AAD 规范化。"""

from __future__ import annotations

import base64
import json

from .crypto import BODY_NONCE_LEN

VERSION = 1
ALGORITHM = "NNL01-CS-AES256GCM"


class InvalidPackageError(ValueError):
    """文件格式损坏 / 字段缺失 / 类型错误 / 版本不支持。"""


class DecryptionError(Exception):
    """无法解密：用户被撤销，或 header/body/AAD 被篡改导致认证失败。"""


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _unb64(s: str) -> bytes:
    try:
        return base64.b64decode(s.encode("ascii"), validate=True)
    except Exception as exc:
        raise InvalidPackageError(f"非法 base64：{exc}") from exc


def build_aad(
    version: int,
    algorithm: str,
    original_filename: str,
    original_size: int,
    cs_header: dict,
) -> bytes:
    """规范化 AAD：认证版本/算法/元数据/CS header（不含 body）。

    用 sort_keys=True + 固定 separators + UTF-8，保证加密与解密时逐字节一致。
    """
    aad_dict = {
        "version": version,
        "algorithm": algorithm,
        "original_filename": original_filename,
        "original_size": original_size,
        "cs_header": {
            "indices": list(cs_header["indices"]),
            "encrypted": [_b64(b) for b in cs_header["encrypted"]],
        },
    }
    return json.dumps(
        aad_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def build_package(
    original_filename: str,
    original_size: int,
    cs_header: dict,
    body_nonce: bytes,
    body_ciphertext: bytes,
) -> dict:
    return {
        "version": VERSION,
        "algorithm": ALGORITHM,
        "original_filename": original_filename,
        "original_size": original_size,
        "cs_header": cs_header,
        "body": {"nonce": body_nonce, "ciphertext": body_ciphertext},
    }


def serialize_package(pkg: dict) -> bytes:
    d = {
        "version": pkg["version"],
        "algorithm": pkg["algorithm"],
        "original_filename": pkg["original_filename"],
        "original_size": pkg["original_size"],
        "cs_header": {
            "indices": list(pkg["cs_header"]["indices"]),
            "encrypted": [_b64(b) for b in pkg["cs_header"]["encrypted"]],
        },
        "body": {
            "nonce": _b64(pkg["body"]["nonce"]),
            "ciphertext": _b64(pkg["body"]["ciphertext"]),
        },
    }
    return json.dumps(d).encode("utf-8")


def deserialize_package(data: bytes) -> dict:
    """解析并校验 package；任何结构问题抛 InvalidPackageError。"""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidPackageError("非法 UTF-8 编码") from exc
    try:
        d = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidPackageError("非法 JSON") from exc

    if not isinstance(d, dict):
        raise InvalidPackageError("package 顶层必须是对象")

    version = d.get("version")
    if version != VERSION:
        raise InvalidPackageError(f"不支持的 version：{version!r}")
    if d.get("algorithm") != ALGORITHM:
        raise InvalidPackageError(f"未知 algorithm：{d.get('algorithm')!r}")

    original_filename = d.get("original_filename")
    original_size = d.get("original_size")
    if not isinstance(original_filename, str):
        raise InvalidPackageError("original_filename 缺失或类型错误")
    if not isinstance(original_size, int) or original_size < 0:
        raise InvalidPackageError("original_size 缺失或类型错误")

    cs_header_raw = d.get("cs_header")
    if not isinstance(cs_header_raw, dict):
        raise InvalidPackageError("cs_header 缺失或类型错误")
    indices = cs_header_raw.get("indices")
    encrypted_raw = cs_header_raw.get("encrypted")
    if not isinstance(indices, list) or not isinstance(encrypted_raw, list):
        raise InvalidPackageError("cs_header.indices/encrypted 类型错误")
    if not all(isinstance(i, int) for i in indices):
        raise InvalidPackageError("cs_header.indices 含非整数")
    if len(indices) != len(encrypted_raw):
        raise InvalidPackageError("cs_header.indices 与 encrypted 长度不一致")
    encrypted = [_unb64(s) for s in encrypted_raw]

    body_raw = d.get("body")
    if not isinstance(body_raw, dict):
        raise InvalidPackageError("body 缺失或类型错误")
    nonce_raw = body_raw.get("nonce")
    ciphertext_raw = body_raw.get("ciphertext")
    if not isinstance(nonce_raw, str) or not isinstance(ciphertext_raw, str):
        raise InvalidPackageError("body.nonce/ciphertext 类型错误")
    nonce = _unb64(nonce_raw)
    ciphertext = _unb64(ciphertext_raw)
    if len(nonce) != BODY_NONCE_LEN:
        raise InvalidPackageError(f"body nonce 长度错误：{len(nonce)}")

    return {
        "version": version,
        "algorithm": ALGORITHM,
        "original_filename": original_filename,
        "original_size": original_size,
        "cs_header": {"indices": indices, "encrypted": encrypted},
        "body": {"nonce": nonce, "ciphertext": ciphertext},
    }
