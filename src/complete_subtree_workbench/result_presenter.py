"""Localized presentation helpers for Complete Subtree receiver results.

Backend status codes remain machine-stable.  This module maps them to concise
Chinese/English teaching text without changing cryptographic semantics or
reading raw key material.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.complete_subtree_mre.types import CsRecoverResult, CsRecoverStatus


@dataclass(frozen=True)
class PresentedCsResult:
    panel_text: str
    status_line: str


def present_cs_result(
    result: CsRecoverResult,
    *,
    language: str,
    force: bool = False,
    target_node_id: int | None = None,
) -> PresentedCsResult:
    zh = language == "zh_CN"
    status = result.status
    trace = result.trace
    user_id = trace.user_id
    matched = trace.matched_node_id
    attempted = trace.attempted_key_node_id
    target = target_node_id if target_node_id is not None else matched

    if zh:
        if status == CsRecoverStatus.SUCCESS:
            detail = (
                f"授权验证通过：u{user_id} 的路径命中 Cover 节点 "
                f"v{matched}，并成功恢复广播内容密钥 K。"
            )
        elif status == CsRecoverStatus.REVOKED:
            detail = (
                f"撤销生效：u{user_id} 的根到叶路径未命中任何 Cover 节点，"
                "因此无法获得可用于恢复 K 的 Header 密钥。"
            )
        elif status == CsRecoverStatus.HEADER_UNWRAP_FAILED:
            if force:
                detail = (
                    f"错误路径密钥：L[{attempted}] 无法解开 "
                    f"E[L{target}](K)，SM4-GCM 认证失败。"
                )
            else:
                detail = "Header 解封失败：SM4-GCM 认证未通过。"
        elif status == CsRecoverStatus.ENVELOPE_MISMATCH:
            detail = "Header 绑定不匹配：package_id 或 node_id 校验失败。"
        else:
            detail = "Complete Subtree Header 无效：结构或 Cover 不变量检查失败。"

        prefix = (
            f"强制尝试 u{user_id} → v{target}："
            if force
            else f"u{user_id}："
        )
    else:
        if status == CsRecoverStatus.SUCCESS:
            detail = (
                f"Authorized receiver verified: u{user_id}'s path matched Cover "
                f"node v{matched} and recovered the broadcast content key K."
            )
        elif status == CsRecoverStatus.REVOKED:
            detail = (
                f"Revocation enforced: u{user_id}'s root-to-leaf path matches no "
                "Cover node, so it has no Header key that can recover K."
            )
        elif status == CsRecoverStatus.HEADER_UNWRAP_FAILED:
            if force:
                detail = (
                    f"Wrong path key: L[{attempted}] cannot unwrap "
                    f"E[L{target}](K); SM4-GCM authentication failed."
                )
            else:
                detail = "Header unwrap failed: SM4-GCM authentication did not succeed."
        elif status == CsRecoverStatus.ENVELOPE_MISMATCH:
            detail = "Header binding mismatch: package_id or node_id validation failed."
        else:
            detail = "Invalid Complete Subtree Header: structure or Cover invariant validation failed."

        prefix = (
            f"Force try u{user_id} -> v{target}: "
            if force
            else f"u{user_id}: "
        )

    return PresentedCsResult(
        panel_text=f"{status.value}\n{detail}",
        status_line=f"{prefix}{status.value} · {detail}",
    )
