from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from src.sm2_sm4_mre.interactive_session import InteractiveSession
from src.sm2_sm4_mre.types import DecryptResult, DecryptStatus, DecryptTrace
from src.sm2_sm4_workbench.receiver_canvas import ReceiverFlowCanvas
from src.sm2_sm4_workbench.receiver_workbench import ReceiverVisualWorkbenchWindow
from tests.test_sm2_sm4_mre_core import FakeBackend


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_receiver_canvas_success_uses_only_trace_fingerprints(qapp, tmp_path: Path):
    canvas = ReceiverFlowCanvas()
    trace = DecryptTrace(
        user_id="u2",
        target_recipient_id="u2",
        wrapped_key_fingerprint="wrapped-fp",
        content_key_fingerprint="content-fp",
        gcm_authenticated=True,
    )
    result = DecryptResult(
        DecryptStatus.SUCCESS,
        "ok",
        tmp_path / "plain.bin",
        trace,
    )
    canvas.show_result(result, mode="normal", user_id="u2", target_recipient_id="u2")

    assert canvas.state.status == "SUCCESS"
    assert canvas.state.wrapped_key_fingerprint == "wrapped-fp"
    assert canvas.state.content_key_fingerprint == "content-fp"
    assert canvas.state.gcm_authenticated is True
    assert not hasattr(canvas.state, "content_key")
    canvas.close()


def test_receiver_canvas_non_recipient_and_force_failure_states(qapp):
    canvas = ReceiverFlowCanvas()

    denied = DecryptResult(
        DecryptStatus.NOT_RECIPIENT,
        "no wrapped key",
        None,
        DecryptTrace(user_id="u1", target_recipient_id="u1"),
    )
    canvas.show_result(denied, mode="normal", user_id="u1", target_recipient_id="u1")
    assert canvas.state.status == "NOT_RECIPIENT"
    assert canvas.state.wrapped_key_fingerprint is None
    assert canvas.state.content_key_fingerprint is None

    forced = DecryptResult(
        DecryptStatus.SM2_UNWRAP_FAILED,
        "wrong key",
        None,
        DecryptTrace(
            user_id="u1",
            target_recipient_id="u2",
            wrapped_key_fingerprint="e2-fp",
        ),
    )
    canvas.show_result(forced, mode="force", user_id="u1", target_recipient_id="u2")
    assert canvas.state.mode == "force"
    assert canvas.state.target_recipient_id == "u2"
    assert canvas.state.status == "SM2_UNWRAP_FAILED"
    assert canvas.state.wrapped_key_fingerprint == "e2-fp"
    assert canvas.state.content_key_fingerprint is None
    canvas.close()


def test_receiver_visual_workbench_tracks_real_fakebackend_results(qapp, tmp_path: Path):
    session = InteractiveSession(tmp_path / "workspace", backend=FakeBackend(), chunk_size=128)
    window = ReceiverVisualWorkbenchWindow(session=session)

    for user_id in ("u1", "u2"):
        window.generate_user(user_id, f"pw-{user_id}")

    source = tmp_path / "media.bin"
    source.write_bytes(b"receiver-visualization" * 100)
    window.set_media_path(source)
    window.set_recipient("u2", True)
    window.generate_material()
    window.wrap_for_user("u2")
    window.encrypt_payload()
    package = tmp_path / "demo.smre"
    window.assemble_to(package)

    recovered = tmp_path / "recovered-u2.bin"
    ok = window.decrypt_user("u2", "pw-u2", recovered)
    assert ok.status == DecryptStatus.SUCCESS
    assert recovered.read_bytes() == source.read_bytes()
    assert window.receiver_flow.state.status == "SUCCESS"
    assert window.receiver_flow.state.content_key_fingerprint is not None
    assert window.workspace_tabs.currentWidget() is window.receiver_tab

    denied = window.decrypt_user("u1", "pw-u1", tmp_path / "denied.bin")
    assert denied.status == DecryptStatus.NOT_RECIPIENT
    assert window.receiver_flow.state.status == "NOT_RECIPIENT"

    forced = window.force_try_user(
        "u1",
        "pw-u1",
        "u2",
        tmp_path / "forced.bin",
    )
    assert forced.status == DecryptStatus.SM2_UNWRAP_FAILED
    assert window.receiver_flow.state.mode == "force"
    assert window.receiver_flow.state.target_recipient_id == "u2"
    assert window.receiver_flow.state.content_key_fingerprint is None

    window.reset_broadcast(keep_media=True)
    assert window.receiver_flow.state.package_ready is False
    assert window.receiver_flow.state.status is None
    assert window.workspace_tabs.currentIndex() == 0
    window.close()
