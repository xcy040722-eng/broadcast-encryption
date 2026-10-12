"""Typed state and result objects for the unified Complete Subtree backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


CS_KEY_SIZE = 16
CS_PACKAGE_ID_SIZE = 16
CS_HEADER_MAGIC = b"CSK1"
CS_HEADER_VERSION = 1


class CsRecoverStatus(str, Enum):
    SUCCESS = "SUCCESS"
    REVOKED = "REVOKED"
    INVALID_HEADER = "INVALID_HEADER"
    HEADER_UNWRAP_FAILED = "HEADER_UNWRAP_FAILED"
    ENVELOPE_MISMATCH = "ENVELOPE_MISMATCH"


@dataclass(frozen=True)
class CsMaterial:
    package_id: bytes
    content_key: bytes


@dataclass(frozen=True)
class CsHeaderEntry:
    node_id: int
    iv: bytes
    ciphertext: bytes


@dataclass(frozen=True)
class CsTraceEvent:
    stage: str
    status: str
    detail: str


@dataclass
class CsRecoverTrace:
    user_id: int
    user_path_nodes: tuple[int, ...] = ()
    matched_node_id: int | None = None
    attempted_key_node_id: int | None = None
    header_fingerprint: str | None = None
    content_key_fingerprint: str | None = None
    events: list[CsTraceEvent] = field(default_factory=list)


@dataclass(frozen=True)
class CsRecoverResult:
    status: CsRecoverStatus
    message: str
    trace: CsRecoverTrace
