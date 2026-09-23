"""Compact binary envelope carried inside each recipient's SM2 ciphertext."""

from __future__ import annotations

from .errors import InvalidEnvelopeError
from .types import (
    CONTENT_KEY_SIZE,
    MAX_USER_ID_BYTES,
    PACKAGE_ID_SIZE,
    KeyEnvelope,
)


_MAGIC = b"MRE1"
_VERSION = 1


def encode_envelope(envelope: KeyEnvelope) -> bytes:
    user_bytes = envelope.user_id.encode("utf-8")
    if len(envelope.package_id) != PACKAGE_ID_SIZE:
        raise InvalidEnvelopeError(
            f"package_id must be {PACKAGE_ID_SIZE} bytes"
        )
    if len(envelope.content_key) != CONTENT_KEY_SIZE:
        raise InvalidEnvelopeError(
            f"content_key must be {CONTENT_KEY_SIZE} bytes"
        )
    if not user_bytes or len(user_bytes) > MAX_USER_ID_BYTES:
        raise InvalidEnvelopeError(
            f"user_id must be 1..{MAX_USER_ID_BYTES} UTF-8 bytes"
        )
    return (
        _MAGIC
        + bytes([_VERSION])
        + envelope.package_id
        + bytes([len(user_bytes)])
        + user_bytes
        + envelope.content_key
    )


def decode_envelope(data: bytes) -> KeyEnvelope:
    minimum = len(_MAGIC) + 1 + PACKAGE_ID_SIZE + 1 + CONTENT_KEY_SIZE
    if len(data) < minimum:
        raise InvalidEnvelopeError("envelope is truncated")
    if data[:4] != _MAGIC:
        raise InvalidEnvelopeError("invalid envelope magic")
    if data[4] != _VERSION:
        raise InvalidEnvelopeError(f"unsupported envelope version: {data[4]}")

    pos = 5
    package_id = data[pos : pos + PACKAGE_ID_SIZE]
    pos += PACKAGE_ID_SIZE
    user_len = data[pos]
    pos += 1
    if user_len == 0 or user_len > MAX_USER_ID_BYTES:
        raise InvalidEnvelopeError("invalid user_id length")
    expected = pos + user_len + CONTENT_KEY_SIZE
    if len(data) != expected:
        raise InvalidEnvelopeError("invalid envelope length")
    try:
        user_id = data[pos : pos + user_len].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidEnvelopeError("user_id is not valid UTF-8") from exc
    pos += user_len
    content_key = data[pos : pos + CONTENT_KEY_SIZE]
    return KeyEnvelope(
        package_id=package_id,
        user_id=user_id,
        content_key=content_key,
    )
