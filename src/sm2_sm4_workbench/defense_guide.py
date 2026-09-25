"""Manual defense/demo guidance derived from safe workbench state.

This module does not execute cryptography and does not advance the session.
It only tells the presenter what action is useful next, based on the already
validated SessionSnapshot and ReceiverCanvasState projections.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.sm2_sm4_mre.interactive_session import SessionSnapshot, SessionStage

from .receiver_canvas import ReceiverCanvasState


@dataclass(frozen=True)
class DefenseGuide:
    title: str
    instruction: str
    emphasis: str

    @property
    def text(self) -> str:
        return f"{self.title} · {self.instruction}\n{self.emphasis}"


def guide_for(
    snapshot: SessionSnapshot,
    receiver: ReceiverCanvasState,
    *,
    language: str = "zh_CN",
) -> DefenseGuide:
    """Return the next manual demonstration hint without mutating any state."""

    zh = language == "zh_CN"
    stage = snapshot.stage

    if stage in {SessionStage.EMPTY, SessionStage.CONFIGURING}:
        missing_keys = [uid for uid in ("u1", "u2", "u3", "u4") if uid not in snapshot.users]
        if missing_keys:
            who = "、".join(missing_keys) if zh else ", ".join(missing_keys)
            return DefenseGuide(
                "答辩提示" if zh else "Defense guide",
                (f"先为 {who} 生成 SM2 密钥，再选择接收者集合 S 和媒体。" if zh else f"Generate SM2 keys for {who}, then choose recipient set S and a media file."),
                ("这里生成的都是真实 GmSSL SM2 密钥。" if zh else "These are real GmSSL SM2 keys."),
            )
        return DefenseGuide(
            "答辩提示" if zh else "Defense guide",
            ("选择 S={u2,u4} 并选择媒体，满足会话材料生成条件。" if zh else "Choose S={u2,u4} and a media file so session material can be generated."),
            ("授权集合决定哪些用户会得到自己的 E[i]。" if zh else "The recipient set determines which users receive an E[i]."),
        )

    if stage == SessionStage.READY_FOR_MATERIAL:
        return DefenseGuide(
            "下一步" if zh else "Next step",
            ("点击“生成内容密钥与会话材料”。" if zh else "Click Generate content material."),
            ("强调：每次广播只生成一个 SM4 内容密钥 K。" if zh else "Emphasize: one SM4 content key K is generated per broadcast."),
        )

    if stage in {SessionStage.MATERIAL_READY, SessionStage.WRAPPING, SessionStage.PAYLOAD_ENCRYPTED}:
        remaining = [uid for uid in snapshot.recipients if uid not in snapshot.wrapped_key_fingerprints]
        need_payload = snapshot.payload_path is None
        if remaining and need_payload:
            targets = "、".join(remaining) if zh else ", ".join(remaining)
            return DefenseGuide(
                "直接操作" if zh else "Direct manipulation",
                (f"把 K 拖到 {targets} 的 PK 节点，并把 K 拖到 SM4-GCM；顺序可任意。" if zh else f"Drag K to the PK nodes for {targets}, and drag K to SM4-GCM; the order may be arbitrary."),
                ("前者执行真实 SM2 封装，后者只加密一次媒体。" if zh else "The former performs real SM2 wrapping; the latter encrypts the media exactly once."),
            )
        if remaining:
            targets = "、".join(remaining) if zh else ", ".join(remaining)
            return DefenseGuide(
                "继续封装" if zh else "Continue wrapping",
                (f"媒体已加密；继续把 K 拖到 {targets} 的 PK 节点。" if zh else f"The media is encrypted; continue dragging K to the PK nodes for {targets}."),
                ("媒体不会因为接收者增加而重复加密。" if zh else "The media is not re-encrypted as recipients are added."),
            )
        if need_payload:
            return DefenseGuide(
                "媒体加密" if zh else "Media encryption",
                ("所有 E[i] 已生成；把 K 拖到 SM4-GCM 节点。" if zh else "All E[i] values are ready; drag K to the SM4-GCM node."),
                ("检查 payload_encryption_count 最终仍为 1。" if zh else "Verify payload_encryption_count remains 1."),
            )

    if stage == SessionStage.READY_TO_ASSEMBLE:
        return DefenseGuide(
            "组装广播包" if zh else "Assemble package",
            ("点击“组装 .smre 广播包”。" if zh else "Click Assemble .smre package."),
            ("同一份包包含 E[i] 头部和唯一一份媒体密文。" if zh else "The same package contains the E[i] header and one encrypted media payload."),
        )

    if stage == SessionStage.PACKAGE_ASSEMBLED:
        status = receiver.status
        if not status:
            return DefenseGuide(
                "接收端三步验证" if zh else "Three receiver checks",
                ("先用 u2 正常解密，再用 u1 正常解密，最后执行 u1 → u2 错误私钥强制尝试。" if zh else "First decrypt normally as u2, then normally as u1, then force-try u1 → u2 with the wrong private key."),
                ("三条路径分别展示 SUCCESS、NOT_RECIPIENT、SM2_UNWRAP_FAILED。" if zh else "The three paths demonstrate SUCCESS, NOT_RECIPIENT, and SM2_UNWRAP_FAILED."),
            )
        if status == "SUCCESS":
            return DefenseGuide(
                "成功路径已验证" if zh else "Success path verified",
                ("接下来选择 u1 正常解密，展示广播包中不存在 E[u1]。" if zh else "Next decrypt normally as u1 to show that E[u1] is absent from the package."),
                ("可点击接收端节点查看真实 trace 与 K 指纹一致性。" if zh else "You can click receiver nodes to inspect the real trace and matching K fingerprints."),
            )
        if status == "NOT_RECIPIENT":
            return DefenseGuide(
                "非接收者路径已验证" if zh else "Non-recipient path verified",
                ("最后执行 u1 → u2 的错误私钥强制尝试。" if zh else "Finally force-try u1 → u2 with the wrong private key."),
                ("目标是让失败真实发生在 native SM2 解封阶段。" if zh else "The goal is to observe a real failure at the native SM2 unwrap stage."),
            )
        if status in {"SM2_UNWRAP_FAILED", "ENVELOPE_MISMATCH", "GCM_AUTH_FAILED"}:
            return DefenseGuide(
                "核心演示完成" if zh else "Core demo complete",
                ("三条接收端路径已经覆盖；现在可点击关系图/接收端路径节点讲解公式与本次真实状态。" if zh else "The receiver paths are covered; now click object-graph or receiver-path nodes to explain formulas and live state."),
                ("建议最后展示发送端 K 指纹与授权接收端恢复 K 指纹相同。" if zh else "Finish by showing that the sender K fingerprint matches the authorized receiver's recovered K fingerprint."),
            )

    return DefenseGuide(
        "答辩提示" if zh else "Defense guide",
        ("按当前高亮阶段继续手动操作。" if zh else "Continue manually according to the highlighted stage."),
        ("所有关键操作都应来自真实 InteractiveSession/GmSSL 状态。" if zh else "All critical actions should remain backed by real InteractiveSession/GmSSL state."),
    )
