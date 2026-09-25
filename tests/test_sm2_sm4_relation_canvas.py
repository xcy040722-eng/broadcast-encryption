from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication

from src.sm2_sm4_mre.interactive_session import InteractiveSession, SessionStage
from src.sm2_sm4_workbench.relation_canvas import CryptoRelationCanvas
from src.sm2_sm4_workbench.widgets import CONTENT_KEY_MIME
from src.sm2_sm4_workbench.window import WorkbenchWindow
from tests.test_sm2_sm4_mre_core import FakeBackend


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class _SyntheticDropEvent:
    def __init__(self, mime: QMimeData, point):
        self._mime = mime
        self._point = point
        self.accepted = False
        self.ignored = False

    def mimeData(self):
        return self._mime

    def position(self):
        return self._point

    def acceptProposedAction(self):
        self.accepted = True

    def ignore(self):
        self.ignored = True


def _content_key_mime() -> QMimeData:
    mime = QMimeData()
    mime.setData(CONTENT_KEY_MIME, b"session-content-key")
    return mime


def test_relation_canvas_direct_drop_targets_emit_real_action_signals(qapp):
    canvas = CryptoRelationCanvas()
    canvas.resize(820, 300)
    canvas.update_state(
        recipients=("u2", "u4"),
        wrapped=(),
        content_key_fingerprint="abc123",
        media_name="demo.bin",
        payload_ready=False,
        package_ready=False,
        package_assembled=False,
    )

    wrapped: list[str] = []
    encrypted: list[bool] = []
    canvas.wrapRequested.connect(wrapped.append)
    canvas.encryptRequested.connect(lambda: encrypted.append(True))

    regions = canvas._layout_regions()
    drop_u2 = _SyntheticDropEvent(_content_key_mime(), regions["recipient:u2"].center())
    canvas.dropEvent(drop_u2)
    assert wrapped == ["u2"]
    assert drop_u2.accepted

    drop_engine = _SyntheticDropEvent(_content_key_mime(), regions["engine"].center())
    canvas.dropEvent(drop_engine)
    assert encrypted == [True]
    assert drop_engine.accepted
    canvas.close()


def test_relation_canvas_rechecks_state_guards_on_programmatic_drop(qapp):
    canvas = CryptoRelationCanvas()
    canvas.resize(820, 300)
    seen: list[str] = []
    canvas.wrapRequested.connect(seen.append)

    canvas.update_state(
        recipients=("u2",),
        wrapped=("u2",),
        content_key_fingerprint="abc123",
        media_name="demo.bin",
        payload_ready=True,
        package_ready=True,
        package_assembled=False,
    )
    regions = canvas._layout_regions()

    denied_wrapped = _SyntheticDropEvent(
        _content_key_mime(), regions["recipient:u2"].center()
    )
    canvas.dropEvent(denied_wrapped)
    assert seen == []
    assert denied_wrapped.ignored

    denied_engine = _SyntheticDropEvent(_content_key_mime(), regions["engine"].center())
    canvas.dropEvent(denied_engine)
    assert denied_engine.ignored
    canvas.close()


def test_workbench_relation_canvas_tracks_interactive_session(qapp, tmp_path: Path):
    backend = FakeBackend()
    session = InteractiveSession(tmp_path / "workspace", backend=backend, chunk_size=257)
    window = WorkbenchWindow(session=session)

    for user_id in ("u1", "u2", "u3", "u4"):
        window.generate_user(user_id, f"pw-{user_id}")

    source = tmp_path / "visual.bin"
    source.write_bytes(b"interactive-object-graph" * 100)
    window.set_media_path(source)
    window.set_recipient("u2", True)
    window.set_recipient("u4", True)

    state = window.relation_canvas.state
    assert state.recipients == ("u2", "u4")
    assert state.media_name == source.name
    assert state.content_key_fingerprint is None

    window.generate_material()
    snap = session.snapshot()
    state = window.relation_canvas.state
    assert state.content_key_fingerprint == snap.content_key_fingerprint

    # The canvas receives only the fingerprint, never the raw 16-byte K.
    assert session._material is not None
    raw_hex = session._material.content_key.hex()
    assert raw_hex not in repr(state).lower()

    window.wrap_for_user("u2")
    assert window.relation_canvas.state.wrapped == ("u2",)

    window.encrypt_payload()
    assert window.relation_canvas.state.payload_ready
    assert session.snapshot().payload_encryption_count == 1

    window.wrap_for_user("u4")
    assert session.stage == SessionStage.READY_TO_ASSEMBLE
    assert window.relation_canvas.state.package_ready

    package = tmp_path / "visual.smre"
    window.assemble_to(package)
    assert window.relation_canvas.state.package_assembled
    assert session.snapshot().payload_encryption_count == 1
    window.close()
