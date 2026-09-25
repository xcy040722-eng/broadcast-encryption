from __future__ import annotations

from src.sm2_sm4_mre.types import DecryptResult, DecryptStatus, DecryptTrace
from src.sm2_sm4_workbench.result_presenter import present_decrypt_result


def _result(status: DecryptStatus) -> DecryptResult:
    return DecryptResult(
        status=status,
        message="raw backend diagnostic should not be used as the primary localized UI message",
        output_path=None,
        trace=DecryptTrace(user_id="u1", target_recipient_id="u2"),
    )


def test_chinese_success_keeps_machine_status_and_localizes_detail():
    shown = present_decrypt_result(
        _result(DecryptStatus.SUCCESS),
        language="zh_CN",
        user_id="u2",
    )
    assert shown.panel_text.startswith("SUCCESS\n")
    assert "授权验证通过" in shown.panel_text
    assert "SM4-GCM" in shown.panel_text
    assert "raw backend diagnostic" not in shown.panel_text
    assert shown.status_line.startswith("u2：SUCCESS")


def test_chinese_non_recipient_names_missing_wrapped_key():
    shown = present_decrypt_result(
        _result(DecryptStatus.NOT_RECIPIENT),
        language="zh_CN",
        user_id="u1",
    )
    assert "NOT_RECIPIENT" in shown.panel_text
    assert "非接收者" in shown.panel_text
    assert "E[u1]" in shown.panel_text


def test_chinese_force_try_explains_wrong_private_key_pairing():
    shown = present_decrypt_result(
        _result(DecryptStatus.SM2_UNWRAP_FAILED),
        language="zh_CN",
        user_id="u1",
        target_recipient_id="u2",
        force=True,
    )
    assert "SM2_UNWRAP_FAILED" in shown.panel_text
    assert "SK[u1]" in shown.panel_text
    assert "E[u2]" in shown.panel_text
    assert shown.status_line.startswith("强制尝试 u1 → u2：SM2_UNWRAP_FAILED")


def test_english_presentation_contains_no_chinese_text():
    shown = present_decrypt_result(
        _result(DecryptStatus.GCM_AUTH_FAILED),
        language="en_US",
        user_id="u2",
    )
    assert "GCM_AUTH_FAILED" in shown.panel_text
    assert "SM4-GCM authentication failed" in shown.panel_text
    assert shown.status_line.startswith("u2: GCM_AUTH_FAILED")
    for ch in shown.panel_text + shown.status_line:
        assert not ("\u4e00" <= ch <= "\u9fff")
        assert ch != "："
