from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication, QInputDialog, QLabel, QLineEdit

from src.sm2_sm4_mre.interactive_session import InteractiveSession
from src.sm2_sm4_workbench.widgets import CONTENT_KEY_MIME, UserCard
from src.sm2_sm4_workbench.window import WorkbenchWindow
from tests.test_sm2_sm4_mre_core import FakeBackend


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _window(tmp_path: Path, *, language: str = "zh_CN") -> WorkbenchWindow:
    session = InteractiveSession(tmp_path / "workspace", backend=FakeBackend())
    return WorkbenchWindow(session=session, language=language)


def test_generate_user_dialog_uses_qlineedit_password_echo(qapp, tmp_path: Path, monkeypatch):
    window = _window(tmp_path)
    seen: dict[str, object] = {}

    def fake_get_text(parent, title, label, echo=QLineEdit.EchoMode.Normal, *args, **kwargs):
        seen["echo"] = echo
        seen["title"] = title
        seen["label"] = label
        return "pw-u1", True

    monkeypatch.setattr(QInputDialog, "getText", fake_get_text)
    window._prompt_generate_user("u1")

    assert seen["echo"] == QLineEdit.EchoMode.Password
    assert seen["title"] == window.i18n("dialog_generate_title", user_id="u1")
    assert seen["label"] == window.i18n("dialog_private_password")
    assert "u1" in window.session.snapshot().users
    window.close()


def test_password_prompt_uses_qlineedit_password_echo(qapp, tmp_path: Path, monkeypatch):
    window = _window(tmp_path)
    seen: dict[str, object] = {}

    def fake_get_text(parent, title, label, echo=QLineEdit.EchoMode.Normal, *args, **kwargs):
        seen["echo"] = echo
        return "secret", True

    monkeypatch.setattr(QInputDialog, "getText", fake_get_text)
    password = window._password_for("u9")

    assert password == "secret"
    assert seen["echo"] == QLineEdit.EchoMode.Password
    window.close()


class _SyntheticDropEvent:
    def __init__(self, mime: QMimeData):
        self._mime = mime
        self.accepted = False
        self.ignored = False

    def mimeData(self):
        return self._mime

    def acceptProposedAction(self):
        self.accepted = True

    def ignore(self):
        self.ignored = True


def test_user_card_drop_rechecks_recipient_guard(qapp):
    card = UserCard("u2")
    seen: list[str] = []
    card.wrapRequested.connect(seen.append)
    mime = QMimeData()
    mime.setData(CONTENT_KEY_MIME, b"session-content-key")

    denied = _SyntheticDropEvent(mime)
    card.dropEvent(denied)
    assert seen == []
    assert denied.ignored

    card.update_state(has_key=True, selected=True, wrapped=False, locked=True)
    allowed = _SyntheticDropEvent(mime)
    card.dropEvent(allowed)
    assert seen == ["u2"]
    assert allowed.accepted
    card.close()


def test_reset_removes_wrapped_key_widgets_immediately(qapp, tmp_path: Path):
    window = _window(tmp_path)
    for user_id in ("u1", "u2"):
        window.generate_user(user_id, f"pw-{user_id}")
    source = tmp_path / "sample.bin"
    source.write_bytes(b"state-sync" * 50)
    window.set_media_path(source)
    window.set_recipient("u2", True)
    window.generate_material()
    window.wrap_for_user("u2")

    before = [label.text() for label in window.wrapped_container.findChildren(QLabel)]
    assert any(text == "E[u2]" for text in before)

    window.reset_broadcast(keep_media=True)
    after = [label.text() for label in window.wrapped_container.findChildren(QLabel)]
    assert not any(text.startswith("E[") for text in after)
    assert window.i18n("wrapped_none") in after
    assert window.receiver_result.text() == window.i18n("receiver_wait")
    window.close()


def test_chinese_is_default_and_english_remains_available(qapp, tmp_path: Path):
    zh = _window(tmp_path / "zh")
    assert zh.windowTitle() == "SM2 + SM4 多接收者交互工作台"
    assert zh.i18n.language == "zh_CN"
    assert "阶段" in zh.stage_label.text()
    zh.close()

    en = _window(tmp_path / "en", language="en_US")
    assert en.windowTitle() == "SM2 + SM4 Multi-Recipient Workbench"
    assert en.i18n.language == "en_US"
    assert en.stage_label.text().startswith("Stage:")
    en.close()


def test_flow_strip_tracks_session_stage(qapp, tmp_path: Path):
    window = _window(tmp_path)
    active = [label.property("active") for label in window.flow_strip._labels]
    assert active == [True, False, False, False, False, False]

    window.generate_user("u2", "pw-u2")
    source = tmp_path / "flow.bin"
    source.write_bytes(b"flow")
    window.set_media_path(source)
    window.set_recipient("u2", True)
    window.generate_material()

    active = [label.property("active") for label in window.flow_strip._labels]
    assert active == [False, True, False, False, False, False]
    window.close()
