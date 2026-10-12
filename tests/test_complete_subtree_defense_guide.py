from __future__ import annotations

from src.complete_subtree_mre.interactive_session import (
    CsSessionSnapshot,
    CsSessionStage,
)
from src.complete_subtree_workbench.defense_guide import guide_for
from src.complete_subtree_workbench.principle_inspector import CsReceiverState


def _snap(
    stage: CsSessionStage,
    *,
    revoked=(3,),
    steiner=(1, 2, 5, 10),
    cover=(3, 4, 11),
    wrapped=(),
    fp: str | None = None,
) -> CsSessionSnapshot:
    return CsSessionSnapshot(
        stage=stage,
        n=8,
        revoked_users=tuple(revoked),
        steiner_nodes=tuple(steiner),
        cover_roots=tuple(cover),
        covered_users=(1, 2, 4, 5, 6, 7, 8),
        package_id="11" * 16 if fp else None,
        content_key_fingerprint=fp,
        wrapped_nodes=tuple(wrapped),
        header_fingerprints={node: f"fp-{node}" for node in wrapped},
        setup_key_count=15,
        per_user_key_count=4,
    )


def test_configuring_guide_teaches_revocation_first():
    guide = guide_for(
        _snap(
            CsSessionStage.CONFIGURING,
            revoked=(),
            steiner=(),
            cover=(),
        ),
        CsReceiverState(),
    )
    assert "R={u3}" in guide.instruction
    assert "撤销集合 R" in guide.emphasis


def test_material_guide_lists_remaining_cover_roots_and_real_gmssl():
    guide = guide_for(
        _snap(
            CsSessionStage.WRAPPING,
            wrapped=(3,),
            fp="abc123",
        ),
        CsReceiverState(),
    )
    assert "v4" in guide.instruction and "v11" in guide.instruction
    assert "v3" not in guide.instruction
    assert "GmSSL SM4-GCM" in guide.emphasis
    assert "不是预设动画" in guide.emphasis


def test_header_ready_demo_progresses_success_revoked_force():
    snap = _snap(
        CsSessionStage.HEADER_READY,
        wrapped=(3, 4, 11),
        fp="abc123",
    )
    start = guide_for(snap, CsReceiverState())
    assert "u4" in start.instruction and "u3" in start.instruction
    assert "SUCCESS" in start.emphasis
    assert "REVOKED" in start.emphasis

    success = guide_for(
        snap,
        CsReceiverState(status="SUCCESS", user_id=4, matched_node_id=11),
    )
    assert "u3" in success.instruction
    assert "v11" in success.emphasis

    revoked = guide_for(
        snap,
        CsReceiverState(status="REVOKED", user_id=3),
    )
    assert "u3 → v3" in revoked.instruction
    assert "SM4-GCM" in revoked.emphasis

    forced = guide_for(
        snap,
        CsReceiverState(
            status="HEADER_UNWRAP_FAILED",
            mode="force",
            user_id=3,
            matched_node_id=3,
            attempted_key_node_id=10,
        ),
    )
    assert "核心演示完成" in forced.title
    assert "SM2+SM4" in forced.emphasis


def test_guide_function_does_not_require_or_mutate_session():
    snap = _snap(
        CsSessionStage.HEADER_READY,
        wrapped=(3, 4, 11),
        fp="abc123",
    )
    receiver = CsReceiverState(status="SUCCESS", user_id=4, matched_node_id=11)
    before = (snap, receiver)
    for _ in range(10):
        guide_for(snap, receiver)
    assert before == (snap, receiver)


def test_english_guide_has_no_cjk_or_fullwidth_colon():
    guide = guide_for(
        _snap(
            CsSessionStage.HEADER_READY,
            wrapped=(3, 4, 11),
            fp="abc123",
        ),
        CsReceiverState(
            status="HEADER_UNWRAP_FAILED",
            mode="force",
            user_id=3,
            matched_node_id=3,
            attempted_key_node_id=10,
        ),
        language="en_US",
    )
    text = guide.text
    assert "Core demo complete" in text
    assert "SM2+SM4" in text
    assert "：" not in text
    assert not any("\u4e00" <= ch <= "\u9fff" for ch in text)
