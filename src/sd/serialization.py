"""SD header 序列化/反序列化（版本化 + 长度校验）。"""

from __future__ import annotations

import base64
import json

VERSION = 1


class InvalidHeaderError(ValueError):
    """header 格式损坏 / 字段缺失 / 类型错误。"""


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _unb64(s: str) -> bytes:
    try:
        return base64.b64decode(s.encode("ascii"), validate=True)
    except Exception as exc:
        raise InvalidHeaderError(f"非法 base64：{exc}") from exc


def serialize_header(header: list[tuple[int, int | None, bytes]]) -> bytes:
    d = {
        "version": VERSION,
        "subsets": [
            {"i": i, "j": j, "encrypted": _b64(blob)} for (i, j, blob) in header
        ],
    }
    return json.dumps(d).encode("utf-8")


def deserialize_header(data: bytes) -> list[tuple[int, int | None, bytes]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidHeaderError("非法 UTF-8 编码") from exc
    try:
        d = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidHeaderError("非法 JSON") from exc

    if not isinstance(d, dict):
        raise InvalidHeaderError("header 顶层必须是对象")
    if d.get("version") != VERSION:
        raise InvalidHeaderError(f"不支持的 version：{d.get('version')!r}")

    subsets = d.get("subsets")
    if not isinstance(subsets, list):
        raise InvalidHeaderError("subsets 缺失或类型错误")

    header = []
    for s in subsets:
        if not isinstance(s, dict):
            raise InvalidHeaderError("subset 必须是对象")
        i = s.get("i")
        j = s.get("j")
        encrypted_raw = s.get("encrypted")
        if not isinstance(i, int):
            raise InvalidHeaderError("subset.i 缺失或类型错误")
        if j is not None and not isinstance(j, int):
            raise InvalidHeaderError("subset.j 类型错误")
        if not isinstance(encrypted_raw, str):
            raise InvalidHeaderError("subset.encrypted 类型错误")
        header.append((i, j, _unb64(encrypted_raw)))

    return header
