from __future__ import annotations

import re

import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QApplication

from src.complete_subtree_mre.interactive_session import CompleteSubtreeSession, CsSessionStage
from src.complete_subtree_mre.types import CsRecoverStatus
from src.complete_subtree_workbench.i18n import Translator
from src.complete_subtree_workbench.tree_canvas import CompleteSubtreeCanvas
from src.complete_subtree_workbench.widgets import CS_K_MIME
from src.complete_subtree_workbench.window import CompleteSubtreeWorkbenchWindow
from tests.test_sm2_sm4_mre_core import FakeBackend


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _window(language: str = "zh_CN") -> CompleteSubtreeWorkbenchWindow:
    session = CompleteSubtreeSession(8, backend=FakeBackend())
    return CompleteSubtreeWorkbenchWindow(session=session, language=language)


def _prepare_header(window: CompleteSubtreeWorkbenchWindow) -> None:
    window.session.set_revoked(3, True)
    window.compute_cover()
    window.generate_material()
    for node in (3, 4, 11):
        window.wrap_for_node(node)


def test_window_smoke_and_initial_projection(qapp):
    window = _window()
    window.show()
    snap = window.session.snapshot()
    assert snap.stage == CsSessionStage.CONFIGURING
    assert len(window._revoked_checks) == 8
    assert window.canvas.tree.n == 8
    assert "Complete Subtree" in window.windowTitle()
    window.close()


def test_direct_manipulation_signal_and_real_session_action(qapp):
    window = _window()
    window.session.set_revoked(3, True)
    window.compute_cover()
    window.generate_material()
    snap = window.session.snapshot()
    assert snap.cover_roots == (3, 4, 11)

    calls: list[int] = []
    window.canvas.wrapRequested.connect(calls.append)
    assert window.canvas.request_wrap_for_node(3) is True
    QApplication.processEvents()

    assert calls == [3]
    assert window.session.snapshot().wrapped_nodes == (3,)
    assert window.canvas.request_wrap_for_node(3) is False
    assert window.canvas.request_wrap_for_node(5) is False
    window.close()


def test_true_qdrop_event_wraps_cover_node(qapp):
    window = _window()
    window.resize(1200, 760)
    window.show()
    QApplication.processEvents()
    window.session.set_revoked(3, True)
    window.compute_cover()
    window.generate_material()
    window.canvas.resize(700, 460)
    window.canvas.set_snapshot(window.session.snapshot())
    centers = window.canvas._layout()
    target = centers[4]

    mime = QMimeData()
    mime.setData(CS_K_MIME, b"K")
    event = QDropEvent(
        QPointF(target.x(), target.y()),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    window.canvas.dropEvent(event)
    QApplication.processEvents()

    assert event.isAccepted()
    assert 4 in window.session.snapshot().wrapped_nodes
    window.close()


def test_receiver_success_revoked_force_and_english_fallback(qapp):
    window = _window()
    _prepare_header(window)
    assert window.session.snapshot().stage == CsSessionStage.HEADER_READY

    window.receiver_user.setCurrentText("u4")
    ok = window.recover_selected()
    assert ok.status == CsRecoverStatus.SUCCESS
    assert ok.trace.matched_node_id == 11
    assert ok.trace.content_key_fingerprint == window.session.snapshot().content_key_fingerprint

    window.receiver_user.setCurrentText("u3")
    denied = window.recover_selected()
    assert denied.status == CsRecoverStatus.REVOKED
    assert denied.trace.matched_node_id is None

    idx = window.force_target.findData(3)
    window.force_target.setCurrentIndex(idx)
    forced = window.force_try_selected()
    assert forced.status == CsRecoverStatus.HEADER_UNWRAP_FAILED
    assert forced.trace.content_key_fingerprint is None
    window.close()

    en = _window("en_US")
    en.show()
    QApplication.processEvents()
    text = " ".join(
        [
            en.windowTitle(),
            en.i18n("panel_revocation"),
            en.i18n("guide_initial"),
            en.i18n("receiver"),
            en.i18n("drag_hint"),
        ]
    )
    assert not re.search(r"[\u3400-\u9fff\uff00-\uffef]", text)
    en.close()


def test_window_localizes_receiver_result_and_guide(qapp):
    zh = _window("zh_CN")
    _prepare_header(zh)
    assert "接收端三步验证" in zh.guide.text()

    zh.receiver_user.setCurrentText("u4")
    ok = zh.recover_selected()
    assert ok.status == CsRecoverStatus.SUCCESS
    assert zh.receiver_result.text().startswith("SUCCESS\n授权验证通过")
    assert "u4：SUCCESS" in zh.status.text()
    assert "接下来选择 u3" in zh.guide.text()

    zh.receiver_user.setCurrentText("u3")
    denied = zh.recover_selected()
    assert denied.status == CsRecoverStatus.REVOKED
    assert "撤销生效" in zh.receiver_result.text()
    assert "u3 → v3" in zh.guide.text()

    idx = zh.force_target.findData(3)
    zh.force_target.setCurrentIndex(idx)
    forced = zh.force_try_selected()
    assert forced.status == CsRecoverStatus.HEADER_UNWRAP_FAILED
    assert "错误路径密钥" in zh.receiver_result.text()
    assert "L[10]" in zh.receiver_result.text()
    assert "核心演示完成" in zh.guide.text()
    zh.close()

    en = _window("en_US")
    _prepare_header(en)
    en.receiver_user.setCurrentText("u4")
    en.recover_selected()
    combined = en.receiver_result.text() + "\n" + en.status.text() + "\n" + en.guide.text()
    assert "Authorized receiver verified" in combined
    assert "：" not in combined
    assert not re.search(r"[\u3400-\u9fff\uff00-\uffef]", combined)
    en.close()
