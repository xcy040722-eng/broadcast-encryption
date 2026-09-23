"""Stateful interaction layer for the SM2 + SM4 teaching workbench.

This module does not implement new cryptography.  It coordinates the already
validated backend primitives so a GUI can execute them one-by-one.  The key
invariant is that the content-key object generated in the session is the exact
key later used by both SM2 wrapping and SM4-GCM payload encryption.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import mimetypes
from pathlib import Path
from typing import Any

from .backend import CryptoBackend
from .gmssl_backend import GmsslBackend
from .package import build_manifest, canonical_manifest_bytes, inspect_package, write_package
from .service import (
    DEFAULT_CHUNK_SIZE,
    decrypt_media,
    force_try_wrapped_key,
    generate_encryption_material,
    generate_user_keys,
    wrap_content_key,
)
from .types import (
    DecryptResult,
    EncryptionMaterial,
    Manifest,
    TraceEvent,
    UserKeyPaths,
)


class SessionStage(str, Enum):
    EMPTY = "EMPTY"
    CONFIGURING = "CONFIGURING"
    READY_FOR_MATERIAL = "READY_FOR_MATERIAL"
    MATERIAL_READY = "MATERIAL_READY"
    WRAPPING = "WRAPPING"
    PAYLOAD_ENCRYPTED = "PAYLOAD_ENCRYPTED"
    READY_TO_ASSEMBLE = "READY_TO_ASSEMBLE"
    PACKAGE_ASSEMBLED = "PACKAGE_ASSEMBLED"


@dataclass(frozen=True)
class SessionSnapshot:
    stage: SessionStage
    users: tuple[str, ...]
    recipients: tuple[str, ...]
    input_path: str | None
    package_id: str | None
    content_key_fingerprint: str | None
    iv_hex: str | None
    wrapped_key_fingerprints: dict[str, str]
    payload_path: str | None
    payload_size: int | None
    payload_encryption_count: int
    package_path: str | None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["stage"] = self.stage.value
        return data


class InteractiveSession:
    """One real, manually controlled multi-recipient encryption session.

    A future PySide6 UI should treat this object as its state model.  Mouse and
    keyboard actions call these methods; the UI must not reproduce crypto math
    or mutate the session's internal dictionaries directly.
    """

    def __init__(
        self,
        workspace: Path,
        *,
        backend: CryptoBackend | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.backend: CryptoBackend = backend if backend is not None else GmsslBackend()
        self.chunk_size = chunk_size

        self.users: dict[str, UserKeyPaths] = {}
        self.recipients: set[str] = set()
        self.input_path: Path | None = None

        self._material: EncryptionMaterial | None = None
        self._manifest: Manifest | None = None
        self._aad: bytes | None = None
        self._wrapped_keys: dict[str, bytes] = {}
        self._payload_path: Path | None = None
        self._payload_size: int | None = None
        self._payload_encryption_count = 0
        self.package_path: Path | None = None
        self.events: list[TraceEvent] = []

    # ------------------------------------------------------------------
    # Read-only state for the UI
    # ------------------------------------------------------------------
    @property
    def stage(self) -> SessionStage:
        if self.package_path is not None:
            return SessionStage.PACKAGE_ASSEMBLED
        if self._material is not None:
            all_wrapped = bool(self.recipients) and set(self._wrapped_keys) == self.recipients
            payload_ready = self._payload_path is not None
            if all_wrapped and payload_ready:
                return SessionStage.READY_TO_ASSEMBLE
            if payload_ready:
                return SessionStage.PAYLOAD_ENCRYPTED
            if self._wrapped_keys:
                return SessionStage.WRAPPING
            return SessionStage.MATERIAL_READY
        if self.input_path is not None and self.recipients:
            return SessionStage.READY_FOR_MATERIAL
        if self.users or self.input_path is not None or self.recipients:
            return SessionStage.CONFIGURING
        return SessionStage.EMPTY

    def snapshot(self) -> SessionSnapshot:
        material = self._material
        return SessionSnapshot(
            stage=self.stage,
            users=tuple(sorted(self.users)),
            recipients=tuple(sorted(self.recipients)),
            input_path=str(self.input_path) if self.input_path else None,
            package_id=material.package_id.hex() if material else None,
            content_key_fingerprint=(
                self._fingerprint(material.content_key) if material else None
            ),
            iv_hex=material.iv.hex() if material else None,
            wrapped_key_fingerprints={
                user_id: self._fingerprint(value)
                for user_id, value in sorted(self._wrapped_keys.items())
            },
            payload_path=str(self._payload_path) if self._payload_path else None,
            payload_size=self._payload_size,
            payload_encryption_count=self._payload_encryption_count,
            package_path=str(self.package_path) if self.package_path else None,
        )

    def wrapped_key_for(self, user_id: str) -> bytes:
        """Return an already-created wrapped-key ciphertext for display/inspection."""
        try:
            return self._wrapped_keys[user_id]
        except KeyError as exc:
            raise KeyError(f"no wrapped key exists for {user_id!r}") from exc

    # ------------------------------------------------------------------
    # Configuration actions
    # ------------------------------------------------------------------
    def generate_user_key(self, user_id: str, password: str) -> UserKeyPaths:
        self._require_pre_material("generate user keys")
        if user_id in self.users:
            raise ValueError(f"user {user_id!r} already exists in this session")
        result = generate_user_keys(
            user_id,
            password,
            self.workspace / "keys",
            backend=self.backend,
        )
        self.users[user_id] = result
        self.events.append(TraceEvent("user-keygen", "ok", f"Generated SM2 key pair for {user_id}"))
        return result

    def set_media(self, input_path: Path) -> None:
        self._require_pre_material("change media")
        path = Path(input_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        self.input_path = path
        self.events.append(TraceEvent("media", "ok", f"Selected media {path.name}"))

    def select_recipient(self, user_id: str, selected: bool = True) -> None:
        self._require_pre_material("change recipient set")
        if user_id not in self.users:
            raise KeyError(f"unknown user {user_id!r}; generate/register keys first")
        if selected:
            self.recipients.add(user_id)
            status = "selected"
        else:
            self.recipients.discard(user_id)
            status = "removed"
        self.events.append(TraceEvent("recipient", "ok", f"{user_id} {status}"))

    def toggle_recipient(self, user_id: str) -> bool:
        selected = user_id not in self.recipients
        self.select_recipient(user_id, selected)
        return selected

    # ------------------------------------------------------------------
    # Real crypto actions, deliberately granular
    # ------------------------------------------------------------------
    def generate_content_material(self) -> SessionSnapshot:
        if self._material is not None:
            raise RuntimeError("content material has already been generated")
        if self.input_path is None:
            raise RuntimeError("select a media file before generating content material")
        if not self.recipients:
            raise RuntimeError("select at least one recipient first")

        material = generate_encryption_material(backend=self.backend)
        recipient_ids = sorted(self.recipients)
        mime = mimetypes.guess_type(self.input_path.name)[0] or "application/octet-stream"
        manifest = build_manifest(
            package_id=material.package_id,
            recipient_ids=recipient_ids,
            filename=self.input_path.name,
            plaintext_size=self.input_path.stat().st_size,
            mime=mime,
            iv=material.iv,
            tag_size=self.backend.sm4_gcm_tag_size,
        )

        self._material = material
        self._manifest = manifest
        self._aad = canonical_manifest_bytes(manifest)
        self.events.append(
            TraceEvent(
                "material",
                "ok",
                "Generated the session package ID, SM4 content key and GCM IV",
            )
        )
        return self.snapshot()

    def wrap_for(self, user_id: str) -> bytes:
        self._require_material()
        if user_id not in self.recipients:
            raise ValueError(f"{user_id!r} is not in the selected recipient set")
        if user_id in self._wrapped_keys:
            raise RuntimeError(f"content key is already wrapped for {user_id!r}")
        paths = self.users[user_id]
        assert self._material is not None
        wrapped = wrap_content_key(
            paths.public_key,
            package_id=self._material.package_id,
            user_id=user_id,
            content_key=self._material.content_key,
            backend=self.backend,
        )
        self._wrapped_keys[user_id] = wrapped
        self.events.append(TraceEvent("sm2-wrap", "ok", f"Wrapped session content key for {user_id}"))
        return wrapped

    def encrypt_payload(self) -> Path:
        self._require_material()
        if self._payload_path is not None:
            raise RuntimeError("payload has already been encrypted in this session")
        assert self.input_path is not None
        assert self._material is not None
        assert self._aad is not None

        staging = self.workspace / "staging"
        staging.mkdir(parents=True, exist_ok=True)
        final_path = staging / f"{self._material.package_id.hex()}.payload.bin"
        temp_path = final_path.with_suffix(final_path.suffix + ".part")
        if temp_path.exists():
            temp_path.unlink()
        if final_path.exists():
            final_path.unlink()

        try:
            with self.input_path.open("rb") as source, temp_path.open("wb") as sink:
                payload_size = self.backend.sm4_gcm_encrypt_stream(
                    self._material.content_key,
                    self._material.iv,
                    self._aad,
                    source,
                    sink,
                    chunk_size=self.chunk_size,
                )
            if temp_path.stat().st_size != payload_size:
                raise RuntimeError(
                    f"backend reported {payload_size} encrypted bytes but wrote {temp_path.stat().st_size}"
                )
            temp_path.replace(final_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        self._payload_path = final_path
        self._payload_size = int(payload_size)
        self._payload_encryption_count += 1
        self.events.append(
            TraceEvent(
                "sm4-gcm",
                "ok",
                f"Encrypted the media exactly once into {self._payload_size} payload bytes",
            )
        )
        return final_path

    def assemble_package(self, output_path: Path) -> Path:
        self._require_material()
        if self.package_path is not None:
            raise RuntimeError("a package has already been assembled in this session")
        if set(self._wrapped_keys) != self.recipients:
            missing = sorted(self.recipients - set(self._wrapped_keys))
            raise RuntimeError(f"wrap the content key for every recipient first; missing={missing}")
        if self._payload_path is None or self._payload_size is None:
            raise RuntimeError("encrypt the media payload before assembling the package")
        assert self._manifest is not None

        staged_payload = self._payload_path

        def payload_writer(sink) -> int:
            copied = 0
            with staged_payload.open("rb") as source:
                while True:
                    chunk = source.read(self.chunk_size)
                    if not chunk:
                        break
                    sink.write(chunk)
                    copied += len(chunk)
            return copied

        output_path = Path(output_path)
        written = write_package(
            output_path=output_path,
            manifest=self._manifest,
            wrapped_keys=self._wrapped_keys,
            payload_writer=payload_writer,
        )
        if written != self._payload_size:
            raise RuntimeError(
                f"package copied {written} payload bytes; expected {self._payload_size}"
            )
        # A structural re-read catches accidental assembly mismatches immediately.
        inspected = inspect_package(output_path)
        if inspected.package_id != self._manifest.package_id:
            raise RuntimeError("assembled package ID changed unexpectedly")

        self.package_path = output_path
        self.events.append(TraceEvent("package", "ok", "Assembled the staged objects into one .smre package"))
        return output_path

    # ------------------------------------------------------------------
    # Receiver / negative-path actions
    # ------------------------------------------------------------------
    def decrypt_as(
        self,
        user_id: str,
        password: str,
        output_path: Path,
    ) -> DecryptResult:
        self._require_package()
        if user_id not in self.users:
            raise KeyError(f"unknown session user {user_id!r}")
        assert self.package_path is not None
        result = decrypt_media(
            self.package_path,
            user_id,
            self.users[user_id].private_key,
            password,
            Path(output_path),
            backend=self.backend,
            chunk_size=self.chunk_size,
        )
        self.events.append(
            TraceEvent("receiver-try", result.status.value.lower(), f"{user_id}: {result.message}")
        )
        return result

    def force_try(
        self,
        *,
        attacker_user_id: str,
        password: str,
        target_recipient_id: str,
        output_path: Path,
    ) -> DecryptResult:
        self._require_package()
        if attacker_user_id not in self.users:
            raise KeyError(f"unknown attacker user {attacker_user_id!r}")
        assert self.package_path is not None
        result = force_try_wrapped_key(
            self.package_path,
            attacker_user_id=attacker_user_id,
            attacker_private_key_path=self.users[attacker_user_id].private_key,
            password=password,
            target_recipient_id=target_recipient_id,
            output_path=Path(output_path),
            backend=self.backend,
            chunk_size=self.chunk_size,
        )
        self.events.append(
            TraceEvent(
                "force-try",
                result.status.value.lower(),
                f"{attacker_user_id} -> {target_recipient_id}: {result.message}",
            )
        )
        return result

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def reset_broadcast(self, *, keep_media: bool = True) -> None:
        """Reset one broadcast while preserving generated user key pairs."""
        if self._payload_path is not None and self._payload_path.exists():
            self._payload_path.unlink()
        self.recipients.clear()
        if not keep_media:
            self.input_path = None
        self._material = None
        self._manifest = None
        self._aad = None
        self._wrapped_keys.clear()
        self._payload_path = None
        self._payload_size = None
        self._payload_encryption_count = 0
        self.package_path = None
        self.events.append(TraceEvent("reset", "ok", "Reset broadcast state; user keys preserved"))

    # ------------------------------------------------------------------
    # Internal guards/helpers
    # ------------------------------------------------------------------
    def _fingerprint(self, data: bytes) -> str:
        return self.backend.sm3(data).hex()[:16]

    def _require_pre_material(self, action: str) -> None:
        if self._material is not None:
            raise RuntimeError(
                f"cannot {action} after content material is generated; reset the broadcast first"
            )

    def _require_material(self) -> None:
        if self._material is None:
            raise RuntimeError("generate content material first")

    def _require_package(self) -> None:
        if self.package_path is None:
            raise RuntimeError("assemble the broadcast package first")
