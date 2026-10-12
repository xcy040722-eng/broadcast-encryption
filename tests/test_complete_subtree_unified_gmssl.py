from __future__ import annotations

from src.complete_subtree_mre.interactive_session import CompleteSubtreeSession
from src.complete_subtree_mre.types import CsRecoverStatus
from src.sm2_sm4_mre.gmssl_backend import GmsslBackend


def test_real_gmssl_complete_subtree_header_roundtrip():
    backend = GmsslBackend()
    session = CompleteSubtreeSession(8, backend=backend)
    session.set_revoked(3, True)
    snap = session.compute_cover()
    assert snap.cover_roots == (3, 4, 11)
    session.generate_content_material()
    ready = session.wrap_all()

    ok = session.recover_as(4)
    assert ok.status == CsRecoverStatus.SUCCESS
    assert ok.trace.content_key_fingerprint == ready.content_key_fingerprint

    denied = session.recover_as(3)
    assert denied.status == CsRecoverStatus.REVOKED

    forced = session.force_try(3, 3)
    assert forced.status == CsRecoverStatus.HEADER_UNWRAP_FAILED
