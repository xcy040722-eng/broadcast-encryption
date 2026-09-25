"""Localized presentation helpers for decrypt/force-try results.

The backend deliberately keeps machine-stable status codes and diagnostic
messages.  This module turns those results into defense/demo-friendly Chinese
or English UI text without changing the cryptographic result itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.sm2_sm4_mre.types import DecryptResult, DecryptStatus


@dataclass(frozen=True)
class PresentedDecryptResult:
    """Safe, localized text derived only from non-secret result metadata."""

    panel_text: str
    status_line: str


def present_decrypt_result(
    result: DecryptResult,
    *,
    language: str,
    user_id: str,
    target_recipient_id: str | None = None,
    force: bool = False,
) -> PresentedDecryptResult:
    """Return localized human-readable text while preserving the status code.

    The function never consumes private-key bytes or raw SM4 key material.  It
    uses only the result status plus the logical user/target identifiers already
    visible in the receiver experiment.
    """

    zh = language == "zh_CN"
    status = result.status
    target = target_recipient_id or user_id

    if zh:
        details = {
            DecryptStatus.SUCCESS: "授权验证通过：SM2 成功恢复内容密钥，SM4-GCM 解密与认证成功。",
            DecryptStatus.NOT_RECIPIENT: (
                f"非接收者：广播包中不存在属于 {user_id} 的密钥封装 E[{user_id}]。"
            ),
            DecryptStatus.INVALID_PACKAGE: "广播包无效：格式、结构或完整性检查失败。",
            DecryptStatus.PRIVATE_KEY_LOAD_FAILED: (
                f"私钥加载失败：请检查 {user_id} 的私钥文件与保护口令。"
            ),
            DecryptStatus.SM2_UNWRAP_FAILED: (
                f"错误私钥：SK[{user_id}] 无法解封 E[{target}]。"
                if force
                else f"SM2 解封失败：SK[{user_id}] 无法解开 E[{target}]。"
            ),
            DecryptStatus.ENVELOPE_MISMATCH: (
                "密钥封装绑定不匹配：package_id 或 user_id 校验失败。"
            ),
            DecryptStatus.GCM_AUTH_FAILED: (
                "SM4-GCM 认证失败：内容密钥错误，或媒体密文/AAD 已被修改。"
            ),
            DecryptStatus.IO_ERROR: "文件读写失败：最终明文未被正常释放。",
        }
        detail = details[status]
        if force:
            status_line = f"强制尝试 {user_id} → {target}：{status.value} · {detail}"
        else:
            status_line = f"{user_id}：{status.value} · {detail}"
    else:
        details = {
            DecryptStatus.SUCCESS: (
                "Authorized receiver verified: SM2 recovered the content key and "
                "SM4-GCM decryption/authentication succeeded."
            ),
            DecryptStatus.NOT_RECIPIENT: (
                f"Non-recipient: the package contains no wrapped key E[{user_id}] for {user_id}."
            ),
            DecryptStatus.INVALID_PACKAGE: (
                "Invalid package: format, structure, or integrity validation failed."
            ),
            DecryptStatus.PRIVATE_KEY_LOAD_FAILED: (
                f"Private-key load failed: check {user_id}'s key file and password."
            ),
            DecryptStatus.SM2_UNWRAP_FAILED: (
                f"Wrong private key: SK[{user_id}] cannot unwrap E[{target}]."
                if force
                else f"SM2 unwrap failed: SK[{user_id}] cannot decrypt E[{target}]."
            ),
            DecryptStatus.ENVELOPE_MISMATCH: (
                "Envelope binding mismatch: package_id or user_id validation failed."
            ),
            DecryptStatus.GCM_AUTH_FAILED: (
                "SM4-GCM authentication failed: the content key is wrong or the ciphertext/AAD was modified."
            ),
            DecryptStatus.IO_ERROR: (
                "File I/O failed: the final plaintext was not released normally."
            ),
        }
        detail = details[status]
        if force:
            status_line = f"Force try {user_id} → {target}: {status.value} · {detail}"
        else:
            status_line = f"{user_id}: {status.value} · {detail}"

    return PresentedDecryptResult(
        panel_text=f"{status.value}\n{detail}",
        status_line=status_line,
    )
