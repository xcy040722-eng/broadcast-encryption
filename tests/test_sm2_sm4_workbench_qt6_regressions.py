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


def _window(tmp_path: Path) -> WorkbenchWindow:
    session = InteractiveSession(tmp_path / "workspace", backend=FakeBackend())
    return WorkbenchWindow(session=session)


def test_generate_user_dialog_uses_qlineedit_password_echo(qapp, tmp_path: Path, monkeypatch):
    window = _window(tmp_path)
    seen: dict[str, object] = {}

    def fake_get_text(parent, title, label, echo=QLineEdit.EchoMode.Normal, *args, **kwargs):
        seen["echo"] = echo
        return "pw-u1", True

    monkeypatch.setattr(QInputDialog, "getText", fake_get_text)
    window._prompt_generate_user("u1")

    assert seen["echo"] == QLineEdit.EchoMode.Password
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

    # A synthetic/programmatic drop must not bypass the same state checks that
    # dragEnterEvent normally enforces.
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
    assert any("None yet" in text for text in after)
    assert window.receiver_result.text() == "Assemble a package first"
    window.close()
