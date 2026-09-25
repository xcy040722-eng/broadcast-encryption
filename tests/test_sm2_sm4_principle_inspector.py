from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from src.sm2_sm4_mre.interactive_session import InteractiveSession
from src.sm2_sm4_mre.types import DecryptStatus
from src.sm2_sm4_workbench.defense_workbench import DefenseWorkbenchWindow
from tests.test_sm2_sm4_mre_core import FakeBackend


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _prepared_window(
    tmp_path: Path,
    *,
    language: str = "zh_CN",
) -> tuple[DefenseWorkbenchWindow, Path]:
    session = InteractiveSession(tmp_path / "workspace", backend=FakeBackend(), chunk_size=128)
    window = DefenseWorkbenchWindow(session=session, language=language)
    for user_id in ("u1", "u2"):
        window.generate_user(user_id, f"pw-{user_id}")
    source = tmp_path / "media.bin"
    source.write_bytes(b"principle-inspector" * 200)
    window.set_media_path(source)
    window.set_recipient("u2", True)
    window.generate_material()
    return window, source


def _receiver_node_center(width_px: int, index: int) -> QPointF:
    margin = 18.0
    width = max(680.0, float(width_px) - margin * 2)
    node_w = min(180.0, (width - 80.0) / 5.0)
    gap = (width - node_w * 5.0) / 4.0
    x = margin + index * (node_w + gap) + node_w / 2.0
    return QPointF(x, 106.0)


def test_sender_object_inspector_uses_safe_snapshot_only(qapp, tmp_path: Path):
    window, _ = _prepared_window(tmp_path)
    window.relation_canvas.resize(780, 300)
    regions = window.relation_canvas._layout_regions()
    assert window._relation_topic_at(regions["key"].center()) == "key"

    window._show_principle("key")
    text = window.principle_inspector.browser.toPlainText()
    snap = window.session.snapshot()
    assert "128" in text
    assert snap.content_key_fingerprint in text

    # Test-only access proves the explanatory layer does not reveal raw K.
    raw_key_hex = window.session._material.content_key.hex()  # noqa: SLF001
    assert raw_key_hex not in text
    assert window.workspace_tabs.currentWidget() is window.principle_tab
    window.close()


def test_recipient_inspector_tracks_real_wrapped_key_state(qapp, tmp_path: Path):
    window, _ = _prepared_window(tmp_path)
    window.wrap_for_user("u2")
    window._show_principle("recipient:u2")
    text = window.principle_inspector.browser.toPlainText()
    fp = window.session.snapshot().wrapped_key_fingerprints["u2"]
    assert "E[u2]" in text
    assert fp in text
    assert "SM2.Enc" in text
    window.close()


def test_receiver_inspector_projects_real_result_trace_without_secrets(qapp, tmp_path: Path):
    window, source = _prepared_window(tmp_path)
    window.wrap_for_user("u2")
    window.encrypt_payload()
    package = tmp_path / "demo.smre"
    window.assemble_to(package)

    recovered = tmp_path / "recovered-u2.bin"
    result = window.decrypt_user("u2", "pw-u2", recovered)
    assert result.status == DecryptStatus.SUCCESS
    assert recovered.read_bytes() == source.read_bytes()

    window.receiver_flow.resize(780, 280)
    assert window._receiver_topic_at(_receiver_node_center(780, 4)) == "receiver:gcm"

    window._show_principle("receiver:gcm")
    text = window.principle_inspector.browser.toPlainText()
    assert "GCM" in text
    assert "认证=是" in text or "authenticated=yes" in text
    assert recovered.name in text

    private_pem = window.session.users["u2"].private_key.read_text(encoding="utf-8")
    assert private_pem not in text
    raw_key_hex = window.session._material.content_key.hex()  # noqa: SLF001
    assert raw_key_hex not in text

    window.reset_broadcast(keep_media=True)
    assert window.principle_inspector.topic is None
    window.close()


def test_english_inspector_uses_ascii_colons_only(qapp, tmp_path: Path):
    window, _ = _prepared_window(tmp_path, language="en_US")
    window._show_principle("key")
    text = window.principle_inspector.browser.toPlainText()

    assert "：" not in text
    for label in (
        "Role:",
        "Inputs:",
        "Core relation / operation:",
        "Outputs:",
        "Live state:",
        "Security boundary:",
    ):
        assert label in text

    window.close()
