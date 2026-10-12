from __future__ import annotations

import pytest

from src.complete_subtree_mre.interactive_session import (
    CompleteSubtreeSession,
    CsSessionStage,
)
from src.complete_subtree_mre.types import CsRecoverStatus
from tests.test_sm2_sm4_mre_core import FakeBackend


def test_state_progression_and_receiver_paths():
    session = CompleteSubtreeSession(8, backend=FakeBackend())
    assert session.snapshot().stage == CsSessionStage.CONFIGURING

    session.set_revoked(3, True)
    snap = session.compute_cover()
    assert snap.stage == CsSessionStage.COVER_READY
    assert snap.steiner_nodes == (1, 2, 5, 10)
    assert snap.cover_roots == (3, 4, 11)
    assert snap.covered_users == (1, 2, 4, 5, 6, 7, 8)

    snap = session.generate_content_material()
    assert snap.stage == CsSessionStage.MATERIAL_READY
    assert snap.content_key_fingerprint
    assert not hasattr(snap, "content_key")

    session.wrap_for_node(3)
    assert session.snapshot().stage == CsSessionStage.WRAPPING
    session.wrap_for_node(4)
    session.wrap_for_node(11)
    snap = session.snapshot()
    assert snap.stage == CsSessionStage.HEADER_READY
    assert snap.wrapped_nodes == (3, 4, 11)

    ok = session.recover_as(4)
    assert ok.status == CsRecoverStatus.SUCCESS
    assert ok.trace.matched_node_id == 11
    assert ok.trace.content_key_fingerprint == snap.content_key_fingerprint

    denied = session.recover_as(3)
    assert denied.status == CsRecoverStatus.REVOKED
    assert denied.trace.content_key_fingerprint is None

    forced = session.force_try(3, 3)
    assert forced.status == CsRecoverStatus.HEADER_UNWRAP_FAILED


def test_reset_preserves_long_lived_tree_but_clears_broadcast_state():
    session = CompleteSubtreeSession(8, backend=FakeBackend())
    first = session.snapshot()
    assert first.setup_key_count == 15
    assert first.per_user_key_count == 4

    session.set_revoked(3, True)
    session.compute_cover()
    session.generate_content_material()
    session.wrap_all()
    assert session.snapshot().stage == CsSessionStage.HEADER_READY

    reset = session.reset_broadcast()
    assert reset.stage == CsSessionStage.CONFIGURING
    assert reset.revoked_users == ()
    assert reset.cover_roots == ()
    assert reset.package_id is None
    assert reset.content_key_fingerprint is None
    assert reset.wrapped_nodes == ()
    assert reset.setup_key_count == 15
    assert reset.per_user_key_count == 4


def test_revocation_set_cannot_change_after_content_material_exists():
    session = CompleteSubtreeSession(8, backend=FakeBackend())
    session.set_revoked(3, True)
    session.compute_cover()
    session.generate_content_material()
    with pytest.raises(RuntimeError):
        session.set_revoked(5, True)
