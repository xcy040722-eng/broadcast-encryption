"""Application service layer for SM2 + SM4 multi-recipient hybrid encryption.

The functions in this module are deliberately granular: a future interactive UI
can call real cryptographic operations one-by-one (generate material, wrap one
recipient, encrypt payload, unwrap one recipient) instead of replaying a fake
animation. `encrypt_media` and `decrypt_media` are convenience orchestrators
built from the same primitives.
"""

from __future__ import annotations

import mimetypes
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Mapping

from .backend import CryptoBackend
from .envelope import decode_envelope, encode_envelope
from .errors import CryptoOperationError, InvalidEnvelopeError, InvalidPackageError
from .gmssl_backend import GmsslBackend
from .package import (
    build_manifest,
    canonical_manifest_bytes,
    inspect_package,
    write_package,
)
from .types import (
    CONTENT_KEY_SIZE,
    MAX_USER_ID_BYTES,
    PACKAGE_ID_SIZE,
    DecryptResult,
    DecryptStatus,
    DecryptTrace,
    EncryptResult,
    EncryptTrace,
    EncryptionMaterial,
    KeyEnvelope,
    Manifest,
    TraceEvent,
    UserKeyPaths,
)


DEFAULT_CHUNK_SIZE = 1024 * 1024


def _backend_or_default(backend: CryptoBackend | None) -> CryptoBackend:
    return backend if backend is not None else GmsslBackend()


def _validate_user_id(user_id: str) -> None:
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("user_id must be a non-empty string")
    encoded = user_id.encode("utf-8")
    if len(encoded) > MAX_USER_ID_BYTES:
        raise ValueError(f"user_id must be at most {MAX_USER_ID_BYTES} UTF-8 bytes")
    if user_id in {".", ".."} or any(ch in user_id for ch in ("/", "\\", "\x00")):
        raise ValueError("user_id contains path-unsafe characters")


def _fp(backend: CryptoBackend, data: bytes) -> str:
    return backend.sm3(data).hex()[:16]


def generate_user_keys(
    user_id: str,
    password: str,
    key_root: Path,
    *,
    backend: CryptoBackend | None = None,
) -> UserKeyPaths:
    """Generate one SM2 key pair and store it under key_root/user_id/."""

    _validate_user_id(user_id)
    if not password:
        raise ValueError("private-key password cannot be empty")
    b = _backend_or_default(backend)
    user_dir = Path(key_root) / user_id
    private_path = user_dir / "sm2_private.pem"
    public_path = user_dir / "sm2_public.pem"
    if private_path.exists() or public_path.exists():
        raise FileExistsError(f"key files already exist for {user_id!r}")
    user_dir.mkdir(parents=True, exist_ok=True)
    try:
        b.generate_sm2_keypair(private_path, public_path, password)
    except Exception:
        for path in (private_path, public_path):
            if path.exists():
                path.unlink()
        raise
    return UserKeyPaths(user_id=user_id, public_key=public_path, private_key=private_path)


def generate_encryption_material(
    *, backend: CryptoBackend | None = None
) -> EncryptionMaterial:
    """Create fresh package ID, SM4 content key and GCM IV for one broadcast."""

    b = _backend_or_default(backend)
    if b.sm4_key_size != CONTENT_KEY_SIZE:
        raise CryptoOperationError(
            f"backend SM4 key size is {b.sm4_key_size}, expected {CONTENT_KEY_SIZE}"
        )
    return EncryptionMaterial(
        package_id=b.random_bytes(PACKAGE_ID_SIZE),
        content_key=b.random_bytes(CONTENT_KEY_SIZE),
        iv=b.random_bytes(b.sm4_gcm_iv_size),
    )


def wrap_content_key(
    public_key_path: Path,
    *,
    package_id: bytes,
    user_id: str,
    content_key: bytes,
    backend: CryptoBackend | None = None,
) -> bytes:
    """SM2-encrypt a compact KeyEnvelope for exactly one recipient."""

    _validate_user_id(user_id)
    if len(package_id) != PACKAGE_ID_SIZE:
        raise ValueError(f"package_id must be {PACKAGE_ID_SIZE} bytes")
    if len(content_key) != CONTENT_KEY_SIZE:
        raise ValueError(f"content_key must be {CONTENT_KEY_SIZE} bytes")
    b = _backend_or_default(backend)
    public_key = b.load_sm2_public_key(Path(public_key_path))
    envelope = encode_envelope(
        KeyEnvelope(package_id=package_id, user_id=user_id, content_key=content_key)
    )
    return b.sm2_encrypt(public_key, envelope)


def unwrap_content_key(
    private_key_path: Path,
    password: str,
    wrapped_key: bytes,
    *,
    expected_package_id: bytes,
    expected_user_id: str,
    backend: CryptoBackend | None = None,
) -> bytes:
    """SM2-decrypt and bind one envelope to a package and user identity."""

    _validate_user_id(expected_user_id)
    b = _backend_or_default(backend)
    private_key = b.load_sm2_private_key(Path(private_key_path), password)
    plaintext = b.sm2_decrypt(private_key, wrapped_key)
    envelope = decode_envelope(plaintext)
    if envelope.package_id != expected_package_id:
        raise InvalidEnvelopeError("envelope package_id does not match package")
    if envelope.user_id != expected_user_id:
        raise InvalidEnvelopeError(
            f"envelope belongs to {envelope.user_id!r}, not {expected_user_id!r}"
        )
    if len(envelope.content_key) != CONTENT_KEY_SIZE:
        raise InvalidEnvelopeError("invalid SM4 content key length")
    return envelope.content_key


def _manifest_for_file(
    input_path: Path,
    recipient_ids: list[str],
    material: EncryptionMaterial,
    b: CryptoBackend,
) -> Manifest:
    mime = mimetypes.guess_type(input_path.name)[0] or "application/octet-stream"
    return build_manifest(
        package_id=material.package_id,
        recipient_ids=recipient_ids,
        filename=input_path.name,
        plaintext_size=input_path.stat().st_size,
        mime=mime,
        iv=material.iv,
        tag_size=b.sm4_gcm_tag_size,
    )


def encrypt_media(
    input_path: Path,
    recipient_public_keys: Mapping[str, Path],
    output_package: Path,
    *,
    backend: CryptoBackend | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> EncryptResult:
    """Encrypt a file once with SM4-GCM and wrap its key for each recipient with SM2."""

    b = _backend_or_default(backend)
    input_path = Path(input_path)
    output_package = Path(output_package)
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not recipient_public_keys:
        raise ValueError("at least one recipient is required")

    recipient_ids = sorted(recipient_public_keys)
    for user_id in recipient_ids:
        _validate_user_id(user_id)

    material = generate_encryption_material(backend=b)
    manifest = _manifest_for_file(input_path, recipient_ids, material, b)
    aad = canonical_manifest_bytes(manifest)
    trace = EncryptTrace(
        package_id=material.package_id.hex(),
        recipients=recipient_ids,
        filename=input_path.name,
        input_size=input_path.stat().st_size,
        mime=manifest.mime,
        content_key_fingerprint=_fp(b, material.content_key),
        iv_hex=material.iv.hex(),
        aad_fingerprint=_fp(b, aad),
    )
    trace.events.append(TraceEvent("material", "ok", "Generated fresh package ID, SM4 key and IV"))

    wrapped_keys: dict[str, bytes] = {}
    for user_id in recipient_ids:
        wrapped = wrap_content_key(
            recipient_public_keys[user_id],
            package_id=material.package_id,
            user_id=user_id,
            content_key=material.content_key,
            backend=b,
        )
        wrapped_keys[user_id] = wrapped
        trace.wrapped_key_fingerprints[user_id] = _fp(b, wrapped)
        trace.events.append(
            TraceEvent("sm2-wrap", "ok", f"Wrapped content key for {user_id}")
        )

    def payload_writer(sink) -> int:
        with input_path.open("rb") as source:
            return b.sm4_gcm_encrypt_stream(
                material.content_key,
                material.iv,
                aad,
                source,
                sink,
                chunk_size=chunk_size,
            )

    payload_size = write_package(
        output_path=output_package,
        manifest=manifest,
        wrapped_keys=wrapped_keys,
        payload_writer=payload_writer,
    )
    trace.payload_size = payload_size
    trace.events.append(
        TraceEvent(
            "sm4-gcm",
            "ok",
            f"Encrypted media once ({trace.input_size} -> {payload_size} bytes including GCM tag)",
        )
    )
    trace.events.append(TraceEvent("package", "ok", "Assembled one .smre broadcast package"))
    return EncryptResult(package_path=output_package, trace=trace)


def _recipient_record(manifest: Manifest, user_id: str):
    for record in manifest.recipients:
        if record.user_id == user_id:
            return record
    return None


def decrypt_media(
    package_path: Path,
    user_id: str,
    private_key_path: Path,
    password: str,
    output_path: Path,
    *,
    backend: CryptoBackend | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> DecryptResult:
    """Decrypt as one named recipient.

    The plaintext is written to a temporary file first and is atomically moved
    to output_path only after SM4-GCM authentication succeeds.
    """

    _validate_user_id(user_id)
    b = _backend_or_default(backend)
    trace = DecryptTrace(user_id=user_id, target_recipient_id=user_id)
    package_path = Path(package_path)
    output_path = Path(output_path)

    try:
        manifest = inspect_package(package_path)
        trace.package_id = manifest.package_id
        trace.events.append(TraceEvent("package", "ok", "Validated package structure"))
    except InvalidPackageError as exc:
        trace.events.append(TraceEvent("package", "error", str(exc)))
        return DecryptResult(DecryptStatus.INVALID_PACKAGE, str(exc), None, trace)

    record = _recipient_record(manifest, user_id)
    if record is None:
        trace.events.append(TraceEvent("recipient", "denied", f"{user_id} is not in the recipient set"))
        return DecryptResult(
            DecryptStatus.NOT_RECIPIENT,
            f"{user_id!r} has no SM2-wrapped content key in this package",
            None,
            trace,
        )

    try:
        with zipfile.ZipFile(package_path, "r") as zf:
            wrapped_key = zf.read(record.wrapped_key_entry)
        trace.wrapped_key_fingerprint = _fp(b, wrapped_key)
    except Exception as exc:
        trace.events.append(TraceEvent("package", "error", f"Cannot read wrapped key: {exc}"))
        return DecryptResult(DecryptStatus.INVALID_PACKAGE, str(exc), None, trace)

    try:
        private_key = b.load_sm2_private_key(Path(private_key_path), password)
    except Exception as exc:
        trace.events.append(TraceEvent("private-key", "error", str(exc)))
        return DecryptResult(
            DecryptStatus.PRIVATE_KEY_LOAD_FAILED,
            f"Unable to load SM2 private key: {exc}",
            None,
            trace,
        )

    try:
        envelope_plain = b.sm2_decrypt(private_key, wrapped_key)
    except Exception as exc:
        trace.events.append(TraceEvent("sm2-unwrap", "error", str(exc)))
        return DecryptResult(
            DecryptStatus.SM2_UNWRAP_FAILED,
            f"SM2 unwrap failed: {exc}",
            None,
            trace,
        )

    try:
        envelope = decode_envelope(envelope_plain)
        if envelope.package_id.hex() != manifest.package_id:
            raise InvalidEnvelopeError("envelope package_id mismatch")
        if envelope.user_id != user_id:
            raise InvalidEnvelopeError(
                f"envelope belongs to {envelope.user_id!r}, not {user_id!r}"
            )
        content_key = envelope.content_key
        trace.content_key_fingerprint = _fp(b, content_key)
        trace.events.append(TraceEvent("sm2-unwrap", "ok", "Recovered and validated SM4 content key"))
    except InvalidEnvelopeError as exc:
        trace.events.append(TraceEvent("envelope", "error", str(exc)))
        return DecryptResult(DecryptStatus.ENVELOPE_MISMATCH, str(exc), None, trace)

    aad = canonical_manifest_bytes(manifest)
    iv = bytes.fromhex(manifest.iv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=output_path.name + ".",
        suffix=".part",
        dir=str(output_path.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(package_path, "r") as zf:
            with zf.open(manifest.payload_entry, "r") as source, temp_path.open("wb") as sink:
                b.sm4_gcm_decrypt_stream(
                    content_key,
                    iv,
                    aad,
                    source,
                    sink,
                    chunk_size=chunk_size,
                )
        if temp_path.stat().st_size != manifest.plaintext_size:
            raise CryptoOperationError(
                f"plaintext size mismatch: expected {manifest.plaintext_size}, got {temp_path.stat().st_size}"
            )
        temp_path.replace(output_path)
        trace.gcm_authenticated = True
        trace.events.append(TraceEvent("sm4-gcm", "ok", "Authentication passed; plaintext released"))
        return DecryptResult(
            DecryptStatus.SUCCESS,
            "Decryption and SM4-GCM authentication succeeded",
            output_path,
            trace,
        )
    except CryptoOperationError as exc:
        trace.gcm_authenticated = False
        trace.events.append(TraceEvent("sm4-gcm", "error", str(exc)))
        if temp_path.exists():
            temp_path.unlink()
        return DecryptResult(
            DecryptStatus.GCM_AUTH_FAILED,
            f"SM4-GCM decryption/authentication failed: {exc}",
            None,
            trace,
        )
    except Exception as exc:
        trace.events.append(TraceEvent("io", "error", str(exc)))
        if temp_path.exists():
            temp_path.unlink()
        return DecryptResult(DecryptStatus.IO_ERROR, str(exc), None, trace)


def force_try_wrapped_key(
    package_path: Path,
    *,
    attacker_user_id: str,
    attacker_private_key_path: Path,
    password: str,
    target_recipient_id: str,
    output_path: Path,
    backend: CryptoBackend | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> DecryptResult:
    """Educational negative-path helper using the real crypto backend."""

    _validate_user_id(attacker_user_id)
    _validate_user_id(target_recipient_id)
    b = _backend_or_default(backend)
    trace = DecryptTrace(
        user_id=attacker_user_id,
        target_recipient_id=target_recipient_id,
    )
    try:
        manifest = inspect_package(Path(package_path))
        trace.package_id = manifest.package_id
    except InvalidPackageError as exc:
        return DecryptResult(DecryptStatus.INVALID_PACKAGE, str(exc), None, trace)

    target = _recipient_record(manifest, target_recipient_id)
    if target is None:
        return DecryptResult(
            DecryptStatus.INVALID_PACKAGE,
            f"target recipient {target_recipient_id!r} is not present",
            None,
            trace,
        )

    try:
        with zipfile.ZipFile(Path(package_path), "r") as zf:
            wrapped_key = zf.read(target.wrapped_key_entry)
        trace.wrapped_key_fingerprint = _fp(b, wrapped_key)
        private_key = b.load_sm2_private_key(Path(attacker_private_key_path), password)
        envelope_plain = b.sm2_decrypt(private_key, wrapped_key)
    except Exception as exc:
        trace.events.append(TraceEvent("forced-sm2-unwrap", "error", str(exc)))
        return DecryptResult(
            DecryptStatus.SM2_UNWRAP_FAILED,
            f"Forced SM2 unwrap failed as expected: {exc}",
            None,
            trace,
        )

    try:
        envelope = decode_envelope(envelope_plain)
        if envelope.package_id.hex() != manifest.package_id:
            raise InvalidEnvelopeError("envelope package_id mismatch")
        if envelope.user_id != attacker_user_id:
            raise InvalidEnvelopeError(
                f"wrapped key is bound to {envelope.user_id!r}, not attacker {attacker_user_id!r}"
            )
        content_key = envelope.content_key
        trace.content_key_fingerprint = _fp(b, content_key)
    except InvalidEnvelopeError as exc:
        trace.events.append(TraceEvent("forced-envelope", "error", str(exc)))
        return DecryptResult(DecryptStatus.ENVELOPE_MISMATCH, str(exc), None, trace)

    aad = canonical_manifest_bytes(manifest)
    iv = bytes.fromhex(manifest.iv)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=output_path.name + ".",
        suffix=".part",
        dir=str(output_path.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(Path(package_path), "r") as zf:
            with zf.open(manifest.payload_entry, "r") as source, temp_path.open("wb") as sink:
                b.sm4_gcm_decrypt_stream(
                    content_key,
                    iv,
                    aad,
                    source,
                    sink,
                    chunk_size=chunk_size,
                )
        temp_path.replace(output_path)
        trace.gcm_authenticated = True
        return DecryptResult(
            DecryptStatus.SUCCESS,
            "Forced try unexpectedly produced a valid authenticated plaintext",
            output_path,
            trace,
        )
    except Exception as exc:
        trace.gcm_authenticated = False
        if temp_path.exists():
            temp_path.unlink()
        trace.events.append(TraceEvent("forced-sm4-gcm", "error", str(exc)))
        return DecryptResult(
            DecryptStatus.GCM_AUTH_FAILED,
            f"Forced try rejected by SM4-GCM authentication: {exc}",
            None,
            trace,
        )
