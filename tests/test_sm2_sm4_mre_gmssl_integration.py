"""Integration tests against the real GmSSL shared library.

Skipped automatically only when GmSSL-Python/native libgmssl cannot be imported.
An ABI layout mismatch is a hard failure (not a skip) because an undersized
ctypes structure can otherwise corrupt memory and cause delayed segfaults.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.sm2_sm4_mre.gmssl_backend import GmsslBackend
from src.sm2_sm4_mre.interactive_session import InteractiveSession, SessionStage
from src.sm2_sm4_mre.service import decrypt_media, encrypt_media, generate_user_keys
from src.sm2_sm4_mre.types import DecryptStatus


pytestmark = pytest.mark.skipif(
    not GmsslBackend.is_available(),
    reason="GmSSL-Python/native libgmssl is not installed",
)


def _assert_safe_abi() -> None:
    issues = GmsslBackend.abi_issues()
    assert not issues, (
        "Unsafe GmSSL ctypes ABI layout: "
        + "; ".join(issues)
        + ". Run `python tools/patch_gmssl_python_abi.py` before native tests."
    )


def test_real_gmssl_sm2_sm4_roundtrip(tmp_path: Path):
    _assert_safe_abi()

    backend = GmsslBackend()
    u2 = generate_user_keys("u2", "test-password", tmp_path / "keys", backend=backend)
    src = tmp_path / "sample.bin"
    src.write_bytes((b"real gmssl integration\n" * 1024) + bytes(range(64)))
    package = tmp_path / "sample.smre"
    encrypt_media(src, {"u2": u2.public_key}, package, backend=backend, chunk_size=1024)

    out = tmp_path / "out.bin"
    dec = decrypt_media(
        package,
        "u2",
        u2.private_key,
        "test-password",
        out,
        backend=backend,
        chunk_size=777,
    )
    assert dec.status == DecryptStatus.SUCCESS
    assert out.read_bytes() == src.read_bytes()


def test_real_gmssl_interactive_session_roundtrip(tmp_path: Path):
    """The GUI-facing session must execute the same real native primitives."""

    _assert_safe_abi()
    backend = GmsslBackend()
    session = InteractiveSession(tmp_path / "interactive", backend=backend, chunk_size=913)
    for user_id in ("u1", "u2", "u4"):
        session.generate_user_key(user_id, f"pw-{user_id}")

    src = tmp_path / "interactive.bin"
    src.write_bytes((b"interactive real gmssl\n" * 512) + bytes(range(128)))
    session.set_media(src)
    session.select_recipient("u2")
    session.select_recipient("u4")

    material_view = session.generate_content_material()
    session.wrap_for("u2")
    session.wrap_for("u4")
    session.encrypt_payload()
    assert session.stage == SessionStage.READY_TO_ASSEMBLE
    assert session.snapshot().payload_encryption_count == 1

    package = session.assemble_package(tmp_path / "interactive.smre")
    assert package.is_file()
    assert session.snapshot().payload_encryption_count == 1

    out = tmp_path / "interactive-u2.bin"
    dec = session.decrypt_as("u2", "pw-u2", out)
    assert dec.status == DecryptStatus.SUCCESS
    assert out.read_bytes() == src.read_bytes()
    assert dec.trace.content_key_fingerprint == material_view.content_key_fingerprint

    denied = session.decrypt_as("u1", "pw-u1", tmp_path / "interactive-u1.bin")
    assert denied.status == DecryptStatus.NOT_RECIPIENT

    forced = session.force_try(
        attacker_user_id="u1",
        password="pw-u1",
        target_recipient_id="u2",
        output_path=tmp_path / "interactive-force.bin",
    )
    assert forced.status in {
        DecryptStatus.SM2_UNWRAP_FAILED,
        DecryptStatus.ENVELOPE_MISMATCH,
        DecryptStatus.GCM_AUTH_FAILED,
    }
