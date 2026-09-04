"""header 基础序列化（JSON + base64）。"""

from __future__ import annotations

import base64
import json


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _unb64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def serialize_header(header: dict) -> bytes:
    d = {
        "indices": header["indices"],
        "encrypted": [_b64(b) for b in header["encrypted"]],
    }
    return json.dumps(d).encode("utf-8")


def deserialize_header(data: bytes) -> dict:
    d = json.loads(data.decode("utf-8"))
    return {
        "indices": d["indices"],
        "encrypted": [_unb64(s) for s in d["encrypted"]],
    }
