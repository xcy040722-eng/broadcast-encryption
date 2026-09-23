from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from src.sm2_sm4_mre.gmssl_backend import GmsslBackend
from src.sm2_sm4_mre.interactive_session import InteractiveSession
from src.sm2_sm4_mre.types import DecryptStatus
from src.sm2_sm4_workbench.window import WorkbenchWindow


pytestmark = pytest.mark.skipif(
    not GmsslBackend.is_available(),
    reason="GmSSL-Python/native libgmssl is not installed",
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_real_gmssl_through_workbench_action_methods(qapp, tmp_path: Path):
    issues = GmsslBackend.abi_issues()
    assert not issues, "Unsafe GmSSL ctypes ABI layout: " + "; ".join(issues)

    backend = GmsslBackend()
    session = InteractiveSession(tmp_path / "workspace", backend=backend, chunk_size=1024)
    window = WorkbenchWindow(session=session)

    for user_id in ("u1", "u2", "u3", "u4"):
        window.generate_user(user_id, f"pw-{user_id}")

    source = tmp_path / "real-media.bin"
    source.write_bytes((b"real PySide6 -> InteractiveSession -> GmSSL\n" * 512) + bytes(range(128)))
    window.set_media_path(source)
    window.set_recipient("u2", True)
    window.set_recipient("u4", True)
    window.generate_material()
    window.wrap_for_user("u2")
    window.wrap_for_user("u4")
    window.encrypt_payload()

    package = tmp_path / "real-workbench.smre"
    window.assemble_to(package)
    assert session.snapshot().payload_encryption_count == 1

    recovered = tmp_path / "recovered-u2.bin"
    result = window.decrypt_user("u2", "pw-u2", recovered)
    assert result.status == DecryptStatus.SUCCESS
    assert recovered.read_bytes() == source.read_bytes()

    denied = tmp_path / "denied-u1.bin"
    result = window.decrypt_user("u1", "pw-u1", denied)
    assert result.status == DecryptStatus.NOT_RECIPIENT
    assert not denied.exists()

    forced = tmp_path / "forced-u1-u2.bin"
    result = window.force_try_user("u1", "pw-u1", "u2", forced)
    assert result.status in {
        DecryptStatus.SM2_UNWRAP_FAILED,
        DecryptStatus.ENVELOPE_MISMATCH,
        DecryptStatus.GCM_AUTH_FAILED,
    }
    assert not forced.exists()
    window.close()
