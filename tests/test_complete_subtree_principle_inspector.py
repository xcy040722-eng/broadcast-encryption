from __future__ import annotations

import re

import pytest
from PySide6.QtWidgets import QApplication

from src.complete_subtree_mre.interactive_session import CompleteSubtreeSession
from src.complete_subtree_mre.types import CsRecoverStatus
from src.complete_subtree_workbench.principle_inspector import (
    CsReceiverState,
    CompleteSubtreePrincipleInspector,
)
from src.complete_subtree_workbench.window import CompleteSubtreeWorkbenchWindow
from tests.test_sm2_sm4_mre_core import FakeBackend


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _session_ready() -> CompleteSubtreeSession:
    session = CompleteSubtreeSession(8, backend=FakeBackend())
    session.set_revoked(3, True)
    session.compute_cover()
    session.generate_content_material()
    session.wrap_all()
    return session


def test_principle_inspector_sender_topics_use_safe_live_state(qapp):
    session = _session_ready()
    inspector = CompleteSubtreePrincipleInspector(
        __import__(
            "src.complete_subtree_workbench.i18n",
            fromlist=["Translator"],
        ).Translator("zh_CN")
    )
    snap = session.snapshot()

    for topic in ("revocation", "steiner", "cover", "key", "nodekey:6", "header:3"):
        inspector.show_topic(topic, snapshot=snap)
        text = inspector.browser.toPlainText()
        assert "作用：" in text
        assert "核心关系 / 运算：" in text
        assert "本次真实状态：" in text

    inspector.show_topic("cover", snapshot=snap)
    assert "v3" in inspector.browser.toPlainText()
    assert "v4" in inspector.browser.toPlainText()
    assert "v11" in inspector.browser.toPlainText()

    inspector.show_topic("header:3", snapshot=snap)
    assert snap.header_fingerprints[3] in inspector.browser.toPlainText()

    raw_k_hex = session._material.content_key.hex()  # test-only inspection
    assert raw_k_hex not in inspector.browser.toPlainText()
    for raw_node_key in session._node_keys.values():  # test-only inspection
        assert raw_node_key.hex() not in inspector.browser.toPlainText()


def test_tree_click_maps_to_principle_topics_and_switches_tab(qapp):
    session = CompleteSubtreeSession(8, backend=FakeBackend())
    window = CompleteSubtreeWorkbenchWindow(session=session, language="zh_CN")
    window.show()

    session.set_revoked(3, True)
    window.compute_cover()

    window._node_selected(3)
    assert window.principle_inspector.topic == "cover:3"
    assert window.workspace_tabs.currentWidget() is window.principle_inspector

    window._node_selected(2)
    assert window.principle_inspector.topic == "steiner:2"

    window._node_selected(6)
    assert window.principle_inspector.topic == "nodekey:6"

    window.generate_material()
    window.wrap_for_node(3)
    window._node_selected(3)
    assert window.principle_inspector.topic == "header:3"
    assert "E[L3](K)" in window.principle_inspector.browser.toPlainText()
    window.close()


def test_receiver_principle_tracks_success_revoked_and_force(qapp):
    session = _session_ready()
    window = CompleteSubtreeWorkbenchWindow(session=session, language="zh_CN")
    window.show()
    window.refresh()

    window.receiver_user.setCurrentText("u4")
    ok = window.recover_selected()
    assert ok.status == CsRecoverStatus.SUCCESS
    window.principle_inspector.show_topic(
        "receiver",
        snapshot=session.snapshot(),
        receiver=window._receiver_state,
    )
    text = window.principle_inspector.browser.toPlainText()
    assert "SUCCESS" in text
    assert "v11" in text
    assert session.snapshot().content_key_fingerprint in text

    window.receiver_user.setCurrentText("u3")
    denied = window.recover_selected()
    assert denied.status == CsRecoverStatus.REVOKED
    window.principle_inspector.show_topic(
        "receiver",
        snapshot=session.snapshot(),
        receiver=window._receiver_state,
    )
    text = window.principle_inspector.browser.toPlainText()
    assert "REVOKED" in text
    assert "恢复 K 指纹=-" in text

    idx = window.force_target.findData(3)
    window.force_target.setCurrentIndex(idx)
    forced = window.force_try_selected()
    assert forced.status == CsRecoverStatus.HEADER_UNWRAP_FAILED
    window.principle_inspector.show_topic(
        "receiver",
        snapshot=session.snapshot(),
        receiver=window._receiver_state,
    )
    text = window.principle_inspector.browser.toPlainText()
    assert "HEADER_UNWRAP_FAILED" in text
    assert "v10" in text
    assert "恢复 K 指纹=-" in text
    window.close()


def test_english_principle_inspector_has_no_cjk_or_fullwidth_colon(qapp):
    session = _session_ready()
    from src.complete_subtree_workbench.i18n import Translator

    inspector = CompleteSubtreePrincipleInspector(Translator("en_US"))
    receiver = CsReceiverState.from_result(session.recover_as(4), mode="recover")
    snap = session.snapshot()

    texts: list[str] = []
    for topic in (
        "revocation",
        "steiner",
        "cover",
        "nodekey:6",
        "key",
        "header:3",
        "receiver",
    ):
        inspector.show_topic(topic, snapshot=snap, receiver=receiver)
        texts.append(inspector.browser.toPlainText())

    combined = "\n".join(texts)
    assert "：" not in combined
    assert not re.search(r"[\u3400-\u9fff\uff00-\uffef]", combined)
    for label in (
        "Role:",
        "Inputs:",
        "Core relation / operation:",
        "Outputs:",
        "Live state:",
        "Security boundary:",
    ):
        assert label in combined
