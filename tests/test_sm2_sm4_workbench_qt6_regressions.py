from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit

from src.sm2_sm4_mre.interactive_session import InteractiveSession
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
