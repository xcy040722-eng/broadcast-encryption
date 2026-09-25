from __future__ import annotations

from src.sm2_sm4_mre.interactive_session import SessionSnapshot, SessionStage
from src.sm2_sm4_workbench.defense_guide import guide_for
from src.sm2_sm4_workbench.receiver_canvas import ReceiverCanvasState


def _snap(
    stage: SessionStage,
    *,
    users=("u1", "u2", "u3", "u4"),
    recipients=("u2", "u4"),
    wrapped=(),
    payload=False,
    package=False,
) -> SessionSnapshot:
    return SessionSnapshot(
        stage=stage,
        users=tuple(users),
        recipients=tuple(recipients),
        input_path="/tmp/media.bin" if stage != SessionStage.EMPTY else None,
        package_id="11" * 16 if stage not in {SessionStage.EMPTY, SessionStage.CONFIGURING, SessionStage.READY_FOR_MATERIAL} else None,
        content_key_fingerprint="abc123" if stage not in {SessionStage.EMPTY, SessionStage.CONFIGURING, SessionStage.READY_FOR_MATERIAL} else None,
        iv_hex="22" * 12 if stage not in {SessionStage.EMPTY, SessionStage.CONFIGURING, SessionStage.READY_FOR_MATERIAL} else None,
        wrapped_key_fingerprints={uid: f"fp-{uid}" for uid in wrapped},
        payload_path="/tmp/payload.bin" if payload else None,
        payload_size=128 if payload else None,
        payload_encryption_count=1 if payload else 0,
        package_path="/tmp/demo.smre" if package else None,
    )


def test_ready_for_material_tells_presenter_to_generate_one_k():
    guide = guide_for(_snap(SessionStage.READY_FOR_MATERIAL), ReceiverCanvasState())
    assert "生成内容密钥" in guide.instruction
    assert "一个 SM4 内容密钥 K" in guide.emphasis


def test_material_stage_guides_real_drag_actions_without_auto_advance():
    guide = guide_for(_snap(SessionStage.MATERIAL_READY), ReceiverCanvasState())
    assert "u2" in guide.instruction and "u4" in guide.instruction
    assert "SM4-GCM" in guide.instruction
    assert "真实 SM2 封装" in guide.emphasis


def test_ready_to_assemble_guides_single_package_action():
    guide = guide_for(
        _snap(
            SessionStage.READY_TO_ASSEMBLE,
            wrapped=("u2", "u4"),
            payload=True,
        ),
        ReceiverCanvasState(),
    )
    assert "组装 .smre 广播包" in guide.instruction
    assert "唯一一份媒体密文" in guide.emphasis


def test_receiver_demo_progresses_success_then_non_recipient_then_force_try():
    snap = _snap(
        SessionStage.PACKAGE_ASSEMBLED,
        wrapped=("u2", "u4"),
        payload=True,
        package=True,
    )

    start = guide_for(snap, ReceiverCanvasState(package_ready=True))
    assert "u2" in start.instruction and "u1" in start.instruction
    assert "SUCCESS" in start.emphasis

    after_success = guide_for(
        snap,
        ReceiverCanvasState(package_ready=True, status="SUCCESS", user_id="u2"),
    )
    assert "u1 正常解密" in after_success.instruction

    after_denied = guide_for(
        snap,
        ReceiverCanvasState(package_ready=True, status="NOT_RECIPIENT", user_id="u1"),
    )
    assert "u1 → u2" in after_denied.instruction
    assert "native SM2" in after_denied.emphasis

    after_force = guide_for(
        snap,
        ReceiverCanvasState(package_ready=True, status="SM2_UNWRAP_FAILED", user_id="u1", target_recipient_id="u2"),
    )
    assert "核心演示完成" in after_force.title
    assert "K 指纹" in after_force.emphasis


def test_english_guide_contains_no_cjk_or_fullwidth_colon():
    guide = guide_for(
        _snap(SessionStage.PACKAGE_ASSEMBLED, wrapped=("u2", "u4"), payload=True, package=True),
        ReceiverCanvasState(package_ready=True, status="SM2_UNWRAP_FAILED"),
        language="en_US",
    )
    text = guide.text
    assert "Core demo complete" in text
    assert "sender K fingerprint" in text
    assert "：" not in text
    assert not any("\u4e00" <= ch <= "\u9fff" for ch in text)
