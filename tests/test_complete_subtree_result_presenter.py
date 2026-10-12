from __future__ import annotations

from src.complete_subtree_mre.types import (
    CsRecoverResult,
    CsRecoverStatus,
    CsRecoverTrace,
)
from src.complete_subtree_workbench.result_presenter import present_cs_result


def _result(
    status: CsRecoverStatus,
    *,
    user_id: int = 3,
    matched: int | None = None,
    attempted: int | None = None,
) -> CsRecoverResult:
    return CsRecoverResult(
        status=status,
        message="raw backend diagnostic should not be primary UI text",
        trace=CsRecoverTrace(
            user_id=user_id,
            matched_node_id=matched,
            attempted_key_node_id=attempted,
        ),
    )


def test_chinese_success_keeps_status_and_explains_cover_match():
    shown = present_cs_result(
        _result(CsRecoverStatus.SUCCESS, user_id=4, matched=11),
        language="zh_CN",
    )
    assert shown.panel_text.startswith("SUCCESS\n")
    assert "授权验证通过" in shown.panel_text
    assert "v11" in shown.panel_text
    assert "raw backend diagnostic" not in shown.panel_text
    assert shown.status_line.startswith("u4：SUCCESS")


def test_chinese_revoked_explains_missing_cover_match():
    shown = present_cs_result(
        _result(CsRecoverStatus.REVOKED, user_id=3),
        language="zh_CN",
    )
    assert "REVOKED" in shown.panel_text
    assert "撤销生效" in shown.panel_text
    assert "未命中任何 Cover 节点" in shown.panel_text


def test_chinese_force_try_names_wrong_path_key_and_header():
    shown = present_cs_result(
        _result(
            CsRecoverStatus.HEADER_UNWRAP_FAILED,
            user_id=3,
            matched=3,
            attempted=10,
        ),
        language="zh_CN",
        force=True,
        target_node_id=3,
    )
    assert "HEADER_UNWRAP_FAILED" in shown.panel_text
    assert "L[10]" in shown.panel_text
    assert "E[L3](K)" in shown.panel_text
    assert "SM4-GCM" in shown.panel_text
    assert shown.status_line.startswith("强制尝试 u3 → v3：")


def test_english_result_has_no_cjk_or_fullwidth_colon():
    shown = present_cs_result(
        _result(
            CsRecoverStatus.HEADER_UNWRAP_FAILED,
            user_id=3,
            matched=3,
            attempted=10,
        ),
        language="en_US",
        force=True,
        target_node_id=3,
    )
    combined = shown.panel_text + shown.status_line
    assert "Wrong path key" in combined
    assert "L[10]" in combined and "E[L3](K)" in combined
    assert "：" not in combined
    assert not any("\u4e00" <= ch <= "\u9fff" for ch in combined)
