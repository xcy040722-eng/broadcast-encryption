from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from src.sm2_sm4_mre.interactive_session import InteractiveSession, SessionStage
from src.sm2_sm4_mre.types import DecryptStatus
from src.sm2_sm4_workbench.window import WorkbenchWindow
from tests.test_sm2_sm4_mre_core import FakeBackend


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_window(tmp_path: Path) -> tuple[WorkbenchWindow, InteractiveSession]:
    backend = FakeBackend()
    session = InteractiveSession(tmp_path / "workspace", backend=backend, chunk_size=257)
    window = WorkbenchWindow(session=session)
    return window, session


def _prepare_users(window: WorkbenchWindow) -> None:
    for user_id in ("u1", "u2", "u3", "u4"):
        window.generate_user(user_id, f"pw-{user_id}")


def test_workbench_real_action_path_with_fake_backend(qapp, tmp_path: Path):
    window, session = _make_window(tmp_path)
    _prepare_users(window)

    source = tmp_path / "picture.bin"
    source.write_bytes(bytes(range(256)) * 30 + b"ui-functional-prototype")
    window.set_media_path(source)
    window.set_recipient("u2", True)
    window.set_recipient("u4", True)
    assert session.stage == SessionStage.READY_FOR_MATERIAL

    window.generate_material()
    snap = session.snapshot()
    assert snap.stage == SessionStage.MATERIAL_READY
    assert snap.content_key_fingerprint
    assert snap.content_key_fingerprint in window.content_key.fingerprint.text()

    # Direct-manipulation drop targets invoke these exact public methods.
    window.wrap_for_user("u2")
    window.wrap_for_user("u4")
    assert set(session.snapshot().wrapped_key_fingerprints) == {"u2", "u4"}

    window.encrypt_payload()
    assert session.snapshot().payload_encryption_count == 1
    package = tmp_path / "broadcast.smre"
    window.assemble_to(package)
    assert package.exists()
    assert session.snapshot().payload_encryption_count == 1
    assert session.stage == SessionStage.PACKAGE_ASSEMBLED

    out_u2 = tmp_path / "u2.bin"
    result_u2 = window.decrypt_user("u2", "pw-u2", out_u2)
    assert result_u2.status == DecryptStatus.SUCCESS
    assert out_u2.read_bytes() == source.read_bytes()

    out_u4 = tmp_path / "u4.bin"
    result_u4 = window.decrypt_user("u4", "pw-u4", out_u4)
    assert result_u4.status == DecryptStatus.SUCCESS
    assert out_u4.read_bytes() == source.read_bytes()

    denied = tmp_path / "u1-denied.bin"
    result_u1 = window.decrypt_user("u1", "pw-u1", denied)
    assert result_u1.status == DecryptStatus.NOT_RECIPIENT
    assert not denied.exists()

    forced = tmp_path / "u1-force-u2.bin"
    force = window.force_try_user("u1", "pw-u1", "u2", forced)
    assert force.status in {
        DecryptStatus.SM2_UNWRAP_FAILED,
        DecryptStatus.ENVELOPE_MISMATCH,
        DecryptStatus.GCM_AUTH_FAILED,
    }
    assert not forced.exists()

    window.close()


def test_workbench_view_never_renders_raw_content_key(qapp, tmp_path: Path):
    window, session = _make_window(tmp_path)
    _prepare_users(window)
    source = tmp_path / "sample.bin"
    source.write_bytes(b"sample" * 100)
    window.set_media_path(source)
    window.set_recipient("u2", True)
    window.generate_material()

    # Test may inspect private session state; the widget must only receive the fingerprint.
    assert session._material is not None
    raw_hex = session._material.content_key.hex()
    visible = "\n".join(
        [
            window.content_key.title.text(),
            window.content_key.fingerprint.text(),
            window.content_key.hint.text(),
            window.status_label.text(),
            window.event_log.toPlainText(),
        ]
    )
    assert raw_hex not in visible.lower()
    assert session.snapshot().content_key_fingerprint in visible
    window.close()


def test_reset_updates_visible_state_but_preserves_user_keys(qapp, tmp_path: Path):
    window, session = _make_window(tmp_path)
    _prepare_users(window)
    source = tmp_path / "keep.bin"
    source.write_bytes(b"keep-media")
    window.set_media_path(source)
    window.set_recipient("u2", True)
    window.generate_material()
    window.wrap_for_user("u2")
    window.encrypt_payload()

    window.reset_broadcast(keep_media=True)
    snap = session.snapshot()
    assert snap.users == ("u1", "u2", "u3", "u4")
    assert snap.input_path == str(source)
    assert snap.recipients == ()
    assert snap.content_key_fingerprint is None
    assert snap.wrapped_key_fingerprints == {}
    assert snap.payload_path is None
    assert window.content_key.fingerprint.text() == "not generated"
    assert all(card.key_status.text() == "SM2 key: ready" for card in window.user_cards.values())
    window.close()
