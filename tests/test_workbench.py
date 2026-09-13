"""Interactive Execution Workbench 测试（不需要 GUI）。

验证：
- 拖放规则（W2/W4 可入，W1/W3 被拒）；
- Execute 后 W_S == 正式 build_ws()；
- cancellation 匹配/不匹配；
- 两组公共项取消后才能 compute z；
- z 与 decrypt_with_trace() 一致；
- threshold 与正式 decode_z() 一致；
- CodePanel 读取真实源码。
"""

import os

import numpy as np
import pytest

pytest.importorskip("PySide6", reason="需要 PySide6")

from desktop_workbench.demo_engine import (  # noqa: E402
    CODE_MAP,
    ROOT,
    TASK_BUILD_WS,
    TASK_CANCEL,
    TASK_DECODE,
    DemoEngine,
)
from src.chw25_dbe.construction import build_ws, decode_z  # noqa: E402


@pytest.fixture()
def eng():
    return DemoEngine()


# ---------- Experiment A ----------


def test_recipient_tokens_accepted(eng):
    assert eng.add_to_ws(2) is True
    assert eng.add_to_ws(4) is True
    assert sorted(eng.ws_slots) == [2, 4]
    assert eng.message_kind == "ok"


def test_non_recipient_rejected(eng):
    for uid in (1, 3):
        assert eng.add_to_ws(uid) is False
        assert 1 not in eng.ws_slots and 3 not in eng.ws_slots
        assert eng.message_kind == "error"
        assert "not in recipient set" in eng.message


def test_execute_requires_all_recipients(eng):
    eng.add_to_ws(2)
    assert eng.execute_build_ws() is None          # 缺 W4
    assert eng.message_kind == "error"
    eng.add_to_ws(4)
    assert eng.execute_build_ws() is not None


def test_execute_matches_real_build_ws(eng):
    eng.add_to_ws(2)
    eng.add_to_ws(4)
    r = eng.execute_build_ws()
    assert r["ok"] is True
    assert np.array_equal(r["W_S"], build_ws(eng.pp, eng.pks, {2, 4}))
    assert np.array_equal(r["W_S"], eng.true_ws)
    assert r["shape"] == (4, 8)


# ---------- Experiment B ----------


def test_matching_terms_can_cancel(eng):
    eng.select_term("L", "stp")
    eng.select_term("R", "stp")
    assert eng.can_cancel() is True
    ok, why = eng.cancel_selected()
    assert ok and why == "cancelled"
    assert "stp" in eng.cancelled


def test_mismatched_terms_rejected(eng):
    eng.select_term("L", "e2")            # 噪声项
    eng.select_term("R", "stp")           # 公共项
    assert eng.can_cancel() is False
    ok, why = eng.cancel_selected()
    assert ok is False and why == "mismatch"
    assert eng.cancelled == set()
    assert "do not match" in eng.message


def test_non_shared_term_rejected(eng):
    ok, why = eng.select_term("L", None)
    assert ok is False and why == "not-shared"


def test_compute_z_requires_all_cancelled(eng):
    assert eng.compute_z_now() is None
    assert eng.message_kind == "error"
    for key in ("stp", "w0ws"):
        eng.select_term("L", key)
        eng.select_term("R", key)
        eng.cancel_selected()
    assert eng.all_cancelled() is True
    assert eng.compute_z_now() is not None


def test_z_matches_decrypt_with_trace(eng):
    for key in ("stp", "w0ws"):
        eng.select_term("L", key)
        eng.select_term("R", key)
        eng.cancel_selected()
    z = eng.compute_z_now()

    from src.chw25_dbe import decrypt_with_trace

    _, tr = decrypt_with_trace(eng.pp, eng.pks, eng.s_set, eng.ct, eng.focus,
                               eng.sks[eng.focus])
    assert z["z_centered"] == tr["z_centered"]
    assert z["z"] == tr["z_before_center"]
    assert z["term_fp"] is not None


# ---------- Threshold ----------


def test_decode_matches_formal_decode_z(eng):
    for key in ("stp", "w0ws"):
        eng.select_term("L", key)
        eng.select_term("R", key)
        eng.cancel_selected()
    z = eng.compute_z_now()
    truth = decode_z(z["z"], eng.params.q)

    good = 1 if truth == 0 else 0
    assert eng.submit_decode(truth)["correct"] is True
    assert eng.submit_decode(good)["correct"] is False
    assert eng.submit_decode(truth)["mu"] == truth


def test_decode_requires_z(eng):
    assert eng.submit_decode(1) is None
    assert eng.message_kind == "error"


# ---------- CodePanel 读真实源码 ----------


def test_code_panel_reads_real_source(eng):
    for tag in (TASK_BUILD_WS, "execute_build_ws", TASK_CANCEL, "term", TASK_DECODE):
        rel, start, end, hl = CODE_MAP[tag]
        lines = eng.code_for(tag)
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            real = f.read().splitlines()
        assert len(lines) == min(end, len(real)) - start + 1
        for ln in lines:
            assert ln["t"] == real[ln["n"] - 1]
            assert ln["hl"] == (ln["n"] in hl)


def test_highlight_lines_are_the_formula(eng):
    txt = "".join(l["t"] for l in eng.code_for(TASK_BUILD_WS) if l["hl"])
    assert "W_S = mod_q(W_S + pks[j].W, q)" in txt
    txt2 = "".join(l["t"] for l in eng.code_for(TASK_DECODE) if l["hl"])
    assert "center_scalar" in txt2 and "q // 4" in txt2


def test_helper_refactor_consistency(eng):
    """encrypt/decrypt 与 helper 必须一致（refactor 不改语义）。"""
    from src.chw25_dbe.construction import compute_z as _cz
    from src.chw25_dbe.construction import derive_rerandomization

    assert np.array_equal(build_ws(eng.pp, eng.pks, eng.s_set), eng.true_ws)
    _, y0 = derive_rerandomization(eng.pp, eng.s_set, eng.ct.xi)
    assert eng.focus in y0
    del _cz  # 已在 test_z_matches_decrypt_with_trace 中间接验证
