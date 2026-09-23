"""Typed data structures shared by the SM2 + SM4 multi-recipient backend."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


PACKAGE_FORMAT = "SM2-SM4-MRE"
PACKAGE_VERSION = 1
PACKAGE_ID_SIZE = 16
CONTENT_KEY_SIZE = 16
MAX_USER_ID_BYTES = 64
PAYLOAD_ENTRY = "payload.bin"
MANIFEST_ENTRY = "manifest.json"


class DecryptStatus(str, Enum):
    SUCCESS = "SUCCESS"
    NOT_RECIPIENT = "NOT_RECIPIENT"
    INVALID_PACKAGE = "INVALID_PACKAGE"
    PRIVATE_KEY_LOAD_FAILED = "PRIVATE_KEY_LOAD_FAILED"
    SM2_UNWRAP_FAILED = "SM2_UNWRAP_FAILED"
    ENVELOPE_MISMATCH = "ENVELOPE_MISMATCH"
    GCM_AUTH_FAILED = "GCM_AUTH_FAILED"
    IO_ERROR = "IO_ERROR"


@dataclass(frozen=True)
class UserKeyPaths:
    user_id: str
    public_key: Path
    private_key: Path


@dataclass(frozen=True)
class EncryptionMaterial:
    """Ephemeral material for one broadcast package.

    This object contains the secret SM4 content key and therefore MUST NOT be
    serialized into the package or emitted by the default trace.
    """

    package_id: bytes
    content_key: bytes
    iv: bytes


@dataclass(frozen=True)
class KeyEnvelope:
    package_id: bytes
    user_id: str
    content_key: bytes


@dataclass(frozen=True)
class RecipientRecord:
    user_id: str
    wrapped_key_entry: str


@dataclass(frozen=True)
class Manifest:
    format: str
    version: int
    package_id: str
    recipients: tuple[RecipientRecord, ...]
    payload_entry: str
    filename: str
    plaintext_size: int
    mime: str
    iv: str
    tag_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "version": self.version,
            "package_id": self.package_id,
            "recipients": [
                {"user_id": r.user_id, "wrapped_key_entry": r.wrapped_key_entry}
                for r in self.recipients
            ],
            "payload": {
                "entry": self.payload_entry,
                "filename": self.filename,
                "plaintext_size": self.plaintext_size,
                "mime": self.mime,
                "iv": self.iv,
                "tag_size": self.tag_size,
            },
        }


@dataclass(frozen=True)
class TraceEvent:
    stage: str
    status: str
    detail: str


@dataclass
class EncryptTrace:
    package_id: str
    recipients: list[str]
    filename: str
    input_size: int
    mime: str
    content_key_fingerprint: str
    iv_hex: str
    aad_fingerprint: str = ""
    wrapped_key_fingerprints: dict[str, str] = field(default_factory=dict)
    payload_size: int | None = None
    events: list[TraceEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["events"] = [asdict(e) for e in self.events]
        return data


@dataclass
class DecryptTrace:
    package_id: str | None = None
    user_id: str | None = None
    target_recipient_id: str | None = None
    wrapped_key_fingerprint: str | None = None
    content_key_fingerprint: str | None = None
    gcm_authenticated: bool | None = None
    events: list[TraceEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["events"] = [asdict(e) for e in self.events]
        return data


@dataclass(frozen=True)
class EncryptResult:
    package_path: Path
    trace: EncryptTrace


@dataclass(frozen=True)
class DecryptResult:
    status: DecryptStatus
    message: str
    output_path: Path | None
    trace: DecryptTrace
