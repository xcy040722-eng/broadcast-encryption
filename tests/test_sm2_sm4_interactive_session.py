from __future__ import annotations

from pathlib import Path

import pytest

from src.sm2_sm4_mre.interactive_session import InteractiveSession, SessionStage
from src.sm2_sm4_mre.types import DecryptStatus
from tests.test_sm2_sm4_mre_core import FakeBackend


def _build_session(tmp_path: Path) -> tuple[InteractiveSession, Path]:
    backend = FakeBackend()
    session = InteractiveSession(tmp_path / "session", backend=backend, chunk_size=257)
    for user_id in ("u1", "u2", "u3", "u4"):
        session.generate_user_key(user_id, f"pw-{user_id}")

    media = tmp_path / "demo.bin"
    media.write_bytes((bytes(range(256)) * 32) + b"interactive-session-tail")
    session.set_media(media)
    session.select_recipient("u2")
    session.select_recipient("u4")
    return session, media


def test_interactive_session_real_action_chain(tmp_path: Path):
    session, media = _build_session(tmp_path)
    assert session.stage == SessionStage.READY_FOR_MATERIAL

    material_view = session.generate_content_material()
    assert material_view.stage == SessionStage.MATERIAL_READY
    assert material_view.recipients == ("u2", "u4")
    assert material_view.content_key_fingerprint is not None

    wrapped_u2 = session.wrap_for("u2")
    assert wrapped_u2
    assert session.stage == SessionStage.WRAPPING
    wrapped_u4 = session.wrap_for("u4")
    assert wrapped_u4
    assert session.stage == SessionStage.WRAPPING

    payload = session.encrypt_payload()
    assert payload.is_file()
    ready = session.snapshot()
    assert ready.stage == SessionStage.READY_TO_ASSEMBLE
    assert ready.payload_encryption_count == 1
    assert ready.payload_size == payload.stat().st_size

    package = session.assemble_package(tmp_path / "broadcast.smre")
    assert package.is_file()
    assembled = session.snapshot()
    assert assembled.stage == SessionStage.PACKAGE_ASSEMBLED
    # Assembly copies the staged ciphertext; it must not invoke SM4 encryption again.
    assert assembled.payload_encryption_count == 1

    out_u2 = tmp_path / "u2.bin"
    dec_u2 = session.decrypt_as("u2", "pw-u2", out_u2)
    assert dec_u2.status == DecryptStatus.SUCCESS
    assert out_u2.read_bytes() == media.read_bytes()
    assert dec_u2.trace.content_key_fingerprint == material_view.content_key_fingerprint

    out_u4 = tmp_path / "u4.bin"
    dec_u4 = session.decrypt_as("u4", "pw-u4", out_u4)
    assert dec_u4.status == DecryptStatus.SUCCESS
    assert out_u4.read_bytes() == media.read_bytes()
    assert dec_u4.trace.content_key_fingerprint == material_view.content_key_fingerprint

    out_u1 = tmp_path / "u1-should-not-exist.bin"
    dec_u1 = session.decrypt_as("u1", "pw-u1", out_u1)
    assert dec_u1.status == DecryptStatus.NOT_RECIPIENT
    assert not out_u1.exists()

    forced = session.force_try(
        attacker_user_id="u1",
        password="pw-u1",
        target_recipient_id="u2",
        output_path=tmp_path / "forced-should-not-exist.bin",
    )
    assert forced.status == DecryptStatus.SM2_UNWRAP_FAILED
    assert not (tmp_path / "forced-should-not-exist.bin").exists()


def test_session_guards_preserve_visual_crypto_invariants(tmp_path: Path):
    session, _ = _build_session(tmp_path)

    with pytest.raises(RuntimeError, match="assemble the broadcast package first"):
        session.decrypt_as("u2", "pw-u2", tmp_path / "too-early.bin")

    session.generate_content_material()

    # Recipient set and media are frozen after material generation so the AAD,
    # wrapped keys, and SM4 payload all refer to exactly one broadcast state.
    with pytest.raises(RuntimeError, match="change recipient set"):
        session.select_recipient("u1")
    with pytest.raises(RuntimeError, match="change media"):
        session.set_media(tmp_path / "other.bin")

    with pytest.raises(ValueError, match="not in the selected recipient set"):
        session.wrap_for("u1")

    session.wrap_for("u2")
    session.encrypt_payload()

    with pytest.raises(RuntimeError, match="already been encrypted"):
        session.encrypt_payload()

    with pytest.raises(RuntimeError, match="missing=.*u4"):
        session.assemble_package(tmp_path / "incomplete.smre")

    session.wrap_for("u4")
    session.assemble_package(tmp_path / "ok.smre")
    assert session.snapshot().payload_encryption_count == 1


def test_reset_broadcast_keeps_user_keys_but_discards_ephemeral_state(tmp_path: Path):
    session, media = _build_session(tmp_path)
    session.generate_content_material()
    session.wrap_for("u2")
    staged = session.encrypt_payload()
    assert staged.exists()

    session.reset_broadcast(keep_media=True)
    snap = session.snapshot()
    assert set(snap.users) == {"u1", "u2", "u3", "u4"}
    assert snap.recipients == ()
    assert snap.input_path == str(media)
    assert snap.package_id is None
    assert snap.content_key_fingerprint is None
    assert snap.payload_path is None
    assert snap.payload_encryption_count == 0
    assert not staged.exists()
    assert snap.stage == SessionStage.CONFIGURING

    session.select_recipient("u2")
    assert session.stage == SessionStage.READY_FOR_MATERIAL
