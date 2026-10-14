from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton

import src.broadcast_encryption_workbench.launcher as launcher_module
from src.broadcast_encryption_workbench.launcher import BroadcastEncryptionLauncher


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _visible_text(window: QMainWindow) -> str:
    parts: list[str] = [window.windowTitle()]
    parts.extend(label.text() for label in window.findChildren(QLabel))
    parts.extend(button.text() for button in window.findChildren(QPushButton))
    return "\n".join(parts)


def test_launcher_smoke_has_two_modules_and_no_crypto_child_at_start(qapp, tmp_path):
    launcher = BroadcastEncryptionLauncher(
        language="zh_CN",
        workspace=tmp_path / "sm2",
        cs_users=8,
    )
    launcher.show()
    QApplication.processEvents()

    text = _visible_text(launcher)
    assert "Complete Subtree" in text
    assert "SM2 + SM4" in text
    assert "经典广播撤销" in text
    assert "多接收者混合加密" in text
    assert launcher._children == []
    launcher.close()


def test_launcher_english_has_no_cjk_or_fullwidth_colon(qapp, tmp_path):
    launcher = BroadcastEncryptionLauncher(
        language="en_US",
        workspace=tmp_path / "sm2",
        cs_users=8,
    )
    text = _visible_text(launcher)
    assert "Complete Subtree" in text
    assert "SM2 + SM4" in text
    assert "：" not in text
    assert not re.search(r"[\u3400-\u9fff\uff00-\uffef]", text)
    launcher.close()


def test_launcher_opens_complete_subtree_with_shared_language(qapp, monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    class DummyCsWindow(QMainWindow):
        def __init__(self, *, n: int, language: str):
            super().__init__()
            captured["n"] = n
            captured["language"] = language

    monkeypatch.setattr(
        launcher_module,
        "CompleteSubtreeWorkbenchWindow",
        DummyCsWindow,
    )

    launcher = BroadcastEncryptionLauncher(
        language="en_US",
        workspace=tmp_path / "sm2",
        cs_users=16,
    )
    child = launcher.open_complete_subtree()
    QApplication.processEvents()

    assert captured == {"n": 16, "language": "en_US"}
    assert child in launcher._children
    assert child.isVisible()

    child.close()
    QApplication.processEvents()
    launcher.close()


def test_launcher_opens_sm2_sm4_with_shared_language_and_workspace(
    qapp,
    monkeypatch,
    tmp_path,
):
    captured: dict[str, object] = {}

    class DummySmWindow(QMainWindow):
        def __init__(self, *, workspace: Path, language: str):
            super().__init__()
            captured["workspace"] = Path(workspace)
            captured["language"] = language

    monkeypatch.setattr(
        launcher_module,
        "DefenseWorkbenchWindow",
        DummySmWindow,
    )

    workspace = tmp_path / "nested" / "sm2"
    launcher = BroadcastEncryptionLauncher(
        language="zh_CN",
        workspace=workspace,
        cs_users=8,
    )
    child = launcher.open_sm2_sm4()
    QApplication.processEvents()

    assert workspace.is_dir()
    assert captured == {"workspace": workspace, "language": "zh_CN"}
    assert child in launcher._children
    assert child.isVisible()

    child.close()
    QApplication.processEvents()
    launcher.close()


def test_launcher_rejects_non_power_of_two_complete_subtree_size(qapp):
    with pytest.raises(ValueError):
        BroadcastEncryptionLauncher(cs_users=6)
