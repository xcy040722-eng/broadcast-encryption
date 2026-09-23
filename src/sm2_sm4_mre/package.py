"""Canonical manifest and .smre package helpers."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import Mapping

from .errors import InvalidPackageError
from .types import (
    MANIFEST_ENTRY,
    PACKAGE_FORMAT,
    PACKAGE_ID_SIZE,
    PACKAGE_VERSION,
    PAYLOAD_ENTRY,
    Manifest,
    RecipientRecord,
)


_WRAPPED_ENTRY_RE = re.compile(r"^wrapped_keys/[0-9]{6}\.bin$")


def canonical_manifest_bytes(manifest: Manifest) -> bytes:
    return json.dumps(
        manifest.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def build_manifest(
    *,
    package_id: bytes,
    recipient_ids: list[str],
    filename: str,
    plaintext_size: int,
    mime: str,
    iv: bytes,
    tag_size: int,
) -> Manifest:
    if len(package_id) != PACKAGE_ID_SIZE:
        raise ValueError(f"package_id must be {PACKAGE_ID_SIZE} bytes")
    if plaintext_size < 0:
        raise ValueError("plaintext_size cannot be negative")
    ordered = sorted(recipient_ids)
    if not ordered:
        raise ValueError("at least one recipient is required")
    if len(set(ordered)) != len(ordered):
        raise ValueError("recipient IDs must be unique")
    recipients = tuple(
        RecipientRecord(
            user_id=user_id,
            wrapped_key_entry=f"wrapped_keys/{index:06d}.bin",
        )
        for index, user_id in enumerate(ordered)
    )
    return Manifest(
        format=PACKAGE_FORMAT,
        version=PACKAGE_VERSION,
        package_id=package_id.hex(),
        recipients=recipients,
        payload_entry=PAYLOAD_ENTRY,
        filename=filename,
        plaintext_size=plaintext_size,
        mime=mime,
        iv=iv.hex(),
        tag_size=tag_size,
    )


def parse_manifest_bytes(data: bytes) -> Manifest:
    try:
        raw = json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise InvalidPackageError("manifest.json is not valid UTF-8 JSON") from exc

    try:
        if raw["format"] != PACKAGE_FORMAT:
            raise InvalidPackageError(f"unsupported format: {raw['format']!r}")
        if int(raw["version"]) != PACKAGE_VERSION:
            raise InvalidPackageError(f"unsupported version: {raw['version']!r}")
        package_id_hex = str(raw["package_id"])
        package_id = bytes.fromhex(package_id_hex)
        if len(package_id) != PACKAGE_ID_SIZE:
            raise InvalidPackageError("package_id has invalid length")

        payload = raw["payload"]
        payload_entry = str(payload["entry"])
        if payload_entry != PAYLOAD_ENTRY:
            raise InvalidPackageError("unexpected payload entry")
        filename = str(payload["filename"])
        if not filename:
            raise InvalidPackageError("filename cannot be empty")
        plaintext_size = int(payload["plaintext_size"])
        if plaintext_size < 0:
            raise InvalidPackageError("plaintext_size cannot be negative")
        mime = str(payload["mime"])
        iv_hex = str(payload["iv"])
        _ = bytes.fromhex(iv_hex)
        tag_size = int(payload["tag_size"])
        if not 8 <= tag_size <= 16:
            raise InvalidPackageError("tag_size must be in 8..16")

        recipients_raw = raw["recipients"]
        if not isinstance(recipients_raw, list) or not recipients_raw:
            raise InvalidPackageError("recipients must be a non-empty list")
        recipients: list[RecipientRecord] = []
        seen_users: set[str] = set()
        seen_entries: set[str] = set()
        for item in recipients_raw:
            user_id = str(item["user_id"])
            entry = str(item["wrapped_key_entry"])
            if not user_id:
                raise InvalidPackageError("recipient user_id cannot be empty")
            if user_id in seen_users:
                raise InvalidPackageError("duplicate recipient user_id")
            if entry in seen_entries:
                raise InvalidPackageError("duplicate wrapped key entry")
            if not _WRAPPED_ENTRY_RE.fullmatch(entry):
                raise InvalidPackageError("invalid wrapped key entry path")
            seen_users.add(user_id)
            seen_entries.add(entry)
            recipients.append(RecipientRecord(user_id=user_id, wrapped_key_entry=entry))

        return Manifest(
            format=PACKAGE_FORMAT,
            version=PACKAGE_VERSION,
            package_id=package_id_hex,
            recipients=tuple(recipients),
            payload_entry=payload_entry,
            filename=filename,
            plaintext_size=plaintext_size,
            mime=mime,
            iv=iv_hex,
            tag_size=tag_size,
        )
    except InvalidPackageError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidPackageError("manifest structure is invalid") from exc


def inspect_package(package_path: Path) -> Manifest:
    try:
        with zipfile.ZipFile(Path(package_path), "r") as zf:
            names = set(zf.namelist())
            if MANIFEST_ENTRY not in names:
                raise InvalidPackageError("manifest.json is missing")
            manifest = parse_manifest_bytes(zf.read(MANIFEST_ENTRY))
            required = {manifest.payload_entry}
            required.update(r.wrapped_key_entry for r in manifest.recipients)
            missing = sorted(required - names)
            if missing:
                raise InvalidPackageError(f"package entries missing: {missing}")
            return manifest
    except InvalidPackageError:
        raise
    except (OSError, zipfile.BadZipFile) as exc:
        raise InvalidPackageError(f"invalid package container: {exc}") from exc


def write_package(
    *,
    output_path: Path,
    manifest: Manifest,
    wrapped_keys: Mapping[str, bytes],
    payload_writer,
) -> int:
    """Write one atomic .smre package.

    payload_writer is called with a writable binary file-like object for
    `payload.bin` and must return the number of bytes written.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_name(output_path.name + ".tmp")
    if temp_path.exists():
        temp_path.unlink()

    recipient_map = {r.user_id: r for r in manifest.recipients}
    if set(recipient_map) != set(wrapped_keys):
        raise InvalidPackageError("wrapped key set does not match manifest recipients")

    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr(MANIFEST_ENTRY, canonical_manifest_bytes(manifest))
            for user_id in sorted(recipient_map):
                zf.writestr(
                    recipient_map[user_id].wrapped_key_entry,
                    wrapped_keys[user_id],
                )
            with zf.open(manifest.payload_entry, "w") as payload_sink:
                payload_size = int(payload_writer(payload_sink))
        temp_path.replace(output_path)
        return payload_size
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise
