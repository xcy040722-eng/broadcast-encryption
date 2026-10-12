"""Manual defense/demo guidance derived only from safe Complete Subtree state.

The guide never executes cryptography or mutates the session.  It only suggests
what the presenter should do next.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.complete_subtree_mre.interactive_session import CsSessionSnapshot, CsSessionStage

from .principle_inspector import CsReceiverState


@dataclass(frozen=True)
class CsDefenseGuide:
    title: str
    instruction: str
    emphasis: str

    @property
    def text(self) -> str:
        return f"{self.title} · {self.instruction}\n{self.emphasis}"


def guide_for(
    snapshot: CsSessionSnapshot,
    receiver: CsReceiverState,
    *,
    language: str = "zh_CN",
) -> CsDefenseGuide:
    zh = language == "zh_CN"
    stage = snapshot.stage

    if stage == CsSessionStage.CONFIGURING:
        return CsDefenseGuide(
            "答辩提示" if zh else "Defense guide",
            (
                "建议选择 R={u3}，然后计算 ST(R) 与 Cover。"
                if zh
                else "Choose R={u3}, then compute ST(R) and the Cover."
            ),
            (
                "Complete Subtree 从撤销集合 R 出发，而不是直接为授权用户逐个生成 Header。"
                if zh
                else "Complete Subtree starts from revocation set R rather than creating one Header per authorized user."
            ),
        )

    if stage == CsSessionStage.COVER_READY:
        return CsDefenseGuide(
            "下一步" if zh else "Next step",
            (
                "生成本次广播唯一的内容密钥 K。"
                if zh
                else "Generate the single content key K for this broadcast."
            ),
            (
                "Cover 根决定哪些长期节点密钥 L_i 会用于保护同一个 K。"
                if zh
                else "The Cover roots determine which long-lived node keys L_i protect the same K."
            ),
        )

    if stage in {CsSessionStage.MATERIAL_READY, CsSessionStage.WRAPPING}:
        remaining = [node for node in snapshot.cover_roots if node not in snapshot.wrapped_nodes]
        roots = "、".join(f"v{node}" for node in remaining) if zh else ", ".join(f"v{node}" for node in remaining)
        return CsDefenseGuide(
            "直接操作" if zh else "Direct manipulation",
            (
                f"把 K 拖到尚未完成的 Cover 根 {roots}。"
                if zh
                else f"Drag K onto the remaining Cover roots {roots}."
            ),
            (
                "每次拖拽都会真实执行一次 GmSSL SM4-GCM 的 E[L_i](K)，不是预设动画。"
                if zh
                else "Each drop runs one real GmSSL SM4-GCM E[L_i](K) operation; it is not a prerecorded animation."
            ),
        )

    if stage == CsSessionStage.HEADER_READY:
        status = receiver.status
        if not status:
            return CsDefenseGuide(
                "接收端三步验证" if zh else "Three receiver checks",
                (
                    "先以 u4 恢复 K，再以撤销用户 u3 恢复 K，最后执行 u3 → v3 错误路径密钥强制尝试。"
                    if zh
                    else "First recover K as u4, then as revoked user u3, then force-try u3 -> v3 with a wrong path key."
                ),
                (
                    "三条路径分别展示 SUCCESS、REVOKED、HEADER_UNWRAP_FAILED。"
                    if zh
                    else "The three paths demonstrate SUCCESS, REVOKED, and HEADER_UNWRAP_FAILED."
                ),
            )
        if status == "SUCCESS":
            return CsDefenseGuide(
                "成功路径已验证" if zh else "Success path verified",
                (
                    "接下来选择 u3 恢复 K，展示撤销用户路径不命中任何 Cover 根。"
                    if zh
                    else "Next recover K as u3 to show that a revoked receiver path matches no Cover root."
                ),
                (
                    "可在“接收路径”页面展示 u4 命中 v11，且恢复 K 指纹与发送端一致。"
                    if zh
                    else "Use the Receiver path page to show that u4 matches v11 and its recovered-K fingerprint equals the sender fingerprint."
                ),
            )
        if status == "REVOKED":
            return CsDefenseGuide(
                "撤销路径已验证" if zh else "Revoked path verified",
                (
                    "最后选择目标 v3，执行 u3 → v3 的错误路径密钥强制尝试。"
                    if zh
                    else "Finally select target v3 and force-try u3 -> v3 with a wrong path key."
                ),
                (
                    "目标是让失败真实发生在 GmSSL SM4-GCM 认证阶段，而不是只依赖 revoked 判断。"
                    if zh
                    else "The goal is to observe a real GmSSL SM4-GCM authentication failure rather than relying only on a revoked flag."
                ),
            )
        if status in {"HEADER_UNWRAP_FAILED", "ENVELOPE_MISMATCH", "INVALID_HEADER"}:
            return CsDefenseGuide(
                "核心演示完成" if zh else "Core demo complete",
                (
                    "三条接收路径已经覆盖；现在可点击 R、ST(R)、Cover、L_i、K 与 Header 讲解公式和本次真实状态。"
                    if zh
                    else "The receiver paths are covered; now explain R, ST(R), Cover, L_i, K, and Header using the Principle/live-state pages."
                ),
                (
                    "最后对比 SM2+SM4：CS 用树型共享密钥压缩 Header，SM2+SM4 则为每个授权用户独立封装 K。"
                    if zh
                    else "Finish by comparing SM2+SM4: CS compresses recipients through shared tree keys, whereas SM2+SM4 wraps K separately for each authorized user."
                ),
            )

    return CsDefenseGuide(
        "答辩提示" if zh else "Defense guide",
        "按当前高亮阶段继续手动操作。" if zh else "Continue manually according to the highlighted stage.",
        "所有提示只读取安全状态，不会自动推进密码学流程。" if zh else "The guide reads safe state only and never advances the cryptographic workflow.",
    )
