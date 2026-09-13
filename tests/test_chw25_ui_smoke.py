"""CHW25 可视化 UI smoke tests。

验证：页面可 import、payload 来自真实 trace、非接收者语义、hybrid 闭环、
密钥不泄露、CS 页面不受影响。不启动 Streamlit 服务。
"""

import importlib
import json
import pathlib

import pytest

from demo.media_data import PNG_BYTES
from web.components.chw25_visualizer import (
    STAGES,
    StageCursor,
    _load_template,
    build_hybrid_payload,
    build_payload,
    visible_keyset_id,
)

REPO = pathlib.Path(__file__).resolve().parents[1]


# ---- 1. 页面可 import（语法与模块级代码）----


def test_chw25_page_imports():
    m = importlib.import_module("web.pages.2_chw25_dbe")
    assert m is not None


def test_component_module_imports():
    m = importlib.import_module("web.components.chw25_visualizer")
    assert hasattr(m, "build_payload") and hasattr(m, "build_hybrid_payload")
    assert hasattr(m, "render")


# ---- 2. 默认 N=4, S={2,4} bit demo ----


def test_default_bit_demo_payload():
    p = build_payload(N=4, s_set={2, 4}, mu=1)
    assert p["recipient_ids"] == [2, 4]
    assert p["params"]["N"] == 4
    assert len(p["users"]) == 4
    assert all(u["eq66_ok"] and u["eq67_ok"] for u in p["users"])
    assert p["stages"][0] == "setup" and p["stages"][-1] == "media"


# ---- 3. u2/u4 trace payload 正确 ----


def test_authorized_trace_payload():
    p = build_payload(N=4, s_set={2, 4}, mu=1)
    for uid in ("2", "4"):
        t = p["traces"][uid]
        assert t["authorized"] is True
        assert t["decoded_mu"] == 1
        # trace 各项齐全
        for k in ("c3", "c2_dot_r_i", "c1_dot_y_ii", "c1_dot_y_0i",
                  "c1_term_total", "z_centered", "noise_residual", "threshold"):
            assert k in t, f"trace 缺字段 {k}"
        assert t["c1_term_total"] == (
            t["c1_dot_y_ii"] + t["c1_dot_y_0i"] + sum(t["c1_dot_y_ji"].values())
        )
        assert abs(t["noise_residual"]) < t["threshold"]


def test_mu_zero_and_one():
    for mu in (0, 1):
        p = build_payload(N=4, s_set={2, 4}, mu=mu)
        for uid in ("2", "4"):
            assert p["traces"][uid]["decoded_mu"] == mu


# ---- 4. u1/u3 为 NotRecipient ----


def test_non_recipient_payload():
    p = build_payload(N=4, s_set={2, 4}, mu=1)
    for uid in ("1", "3"):
        t = p["traces"][uid]
        assert t["authorized"] is False
        assert t["bit"] is None            # **不是** 0
        assert "decoded_mu" not in t        # 不能表现为「解密为 0」


# ---- 5. hybrid 闭环仍成功 ----


def test_hybrid_payload_roundtrip():
    p = build_payload(N=4, s_set={2, 4}, mu=1)
    h = build_hybrid_payload(p, PNG_BYTES, "demo.png")
    hp = h["hybrid_progress"]
    assert hp["bit_count"] == 256
    assert hp["recovered_count"] == 256
    assert hp["media"]["match"] is True
    assert hp["representative_bit_trace"]["authorized"] is True
    assert len(hp["key_fingerprint"]) == 8


# ---- 6. 密钥不泄露到 payload / HTML ----


def test_key_material_not_exposed():
    p = build_payload(N=4, s_set={2, 4}, mu=1)
    h = build_hybrid_payload(p, b"x" * 64, "f.bin")
    hp = h["hybrid_progress"]
    # 不导出完整 key 的 bit 内容
    assert "key_bits" not in hp and "recovered_bits" not in hp
    # 也不导出私钥向量
    for u in h["users"]:
        assert "self_term" not in u              # 只应有 *_fingerprint / *_marker
        assert u["self_term_marker"] == "PRIVATE"
    blob = json.dumps(h)
    assert "key_bits" not in blob


def test_template_placeholders_present():
    """模板通过占位符注入 payload 与高度。"""
    tpl = _load_template()
    assert "__PAYLOAD__" in tpl and "__H__" in tpl


# ---- 6b. Presentation-state：keyset_id 阶段门控 ----


def test_setup_does_not_expose_keyset_id():
    """Setup 阶段不得出现 keyset_id（显示 Pending）。"""
    p = build_payload(N=4, s_set={2, 4}, mu=1)
    assert visible_keyset_id(p, "setup") is None
    assert p["keyset"]["reveal_stage"] == "keygen"
    assert p["keyset"]["pending_text"] == "Pending — generated after KeyGen"
    assert STAGES.index("setup") < STAGES.index("keygen")


def test_keyset_id_appears_after_keygen():
    p = build_payload(N=4, s_set={2, 4}, mu=1)
    val = p["keyset"]["value"]
    assert isinstance(val, str) and len(val) == 64
    assert visible_keyset_id(p, "keygen") == val
    for stage in STAGES[STAGES.index("keygen"):]:
        assert visible_keyset_id(p, stage) == val


# ---- 6c. Presentation-state：无 session-key 字节 ----


def test_no_session_key_bytes_in_payload():
    """payload 中不存在任何 session-key raw bytes / partial bytes。"""
    p = build_payload(N=4, s_set={2, 4}, mu=1)
    h = build_hybrid_payload(p, PNG_BYTES, "demo.png")
    hp = h["hybrid_progress"]

    # 不得出现 key 的字节导出字段（含前后缀 hex / bit 内容）
    for forbidden in ("key_head_hex", "key_tail_hex", "key_bits",
                      "recovered_bits", "key_bytes", "key_hex"):
        assert forbidden not in hp, f"payload 不应包含 {forbidden}"

    # 只允许「非字节」的派生信息
    assert isinstance(hp["key_fingerprint"], str) and len(hp["key_fingerprint"]) == 8
    assert hp["key_length_bytes"] == 32
    assert hp["key_recovered"] is True
    assert hp["grid_kind"] == "aggregate-progress"

    # 序列化后也不应出现 64-hex 的完整 key
    blob = json.dumps(h)
    assert "key_head_hex" not in blob and "key_bits" not in blob


# ---- 6d. Presentation-state：S / μ 变化 → 旧 trace 不复用 ----


def test_scenario_id_changes_with_S():
    """改变 S 后 scenario_id 变化，且 trace 对应新的 S。"""
    p1 = build_payload(N=4, s_set={2, 4}, mu=1)
    p2 = build_payload(N=4, s_set={1, 3}, mu=1)
    assert p1["scenario_id"] != p2["scenario_id"]
    assert p1["scenario"]["S"] == [2, 4]
    assert p2["scenario"]["S"] == [1, 3]
    # trace 与新 S 一致
    assert p2["traces"]["1"]["authorized"] is True
    assert p2["traces"]["3"]["authorized"] is True
    assert p2["traces"]["2"]["authorized"] is False
    assert p2["traces"]["4"]["authorized"] is False


def test_scenario_id_changes_with_mu():
    """改变 μ 后 scenario_id 变化。"""
    p0 = build_payload(N=4, s_set={2, 4}, mu=0)
    p1 = build_payload(N=4, s_set={2, 4}, mu=1)
    assert p0["scenario_id"] != p1["scenario_id"]
    assert p0["scenario"]["mu"] == 0 and p1["scenario"]["mu"] == 1
    assert p0["traces"]["2"]["decoded_mu"] == 0
    assert p1["traces"]["2"]["decoded_mu"] == 1


# ---- 6e. Presentation-state：Replay / 阶段导航 ----


def test_stage_cursor_navigation_and_replay():
    c = StageCursor(STAGES)
    assert c.index == 0 and c.dec_phase == 0
    # 前进到 decrypt
    while STAGES[c.index] != "decrypt":
        c.next()
    # decrypt 有 5 个子阶段
    for _ in range(4):
        c.next()
    assert c.dec_phase == 4
    c.next()
    assert STAGES[c.index] == "recover" and c.dec_phase == 0
    # Replay 重置
    assert c.reset() == 0
    assert c.index == 0 and c.dec_phase == 0


def test_stage_cursor_prev():
    c = StageCursor(STAGES)
    c.next(); c.next()
    assert c.prev() == 1
    assert c.prev() == 0
    assert c.prev() == 0  # 边界不越界


# ---- 6f. Presentation-state：non-recipient 不进入 cancellation 成功路径 ----


def test_non_recipient_not_in_cancellation_path():
    """非接收者 trace 不含 cancellation / 解码字段。"""
    p = build_payload(N=4, s_set={2, 4}, mu=1)
    success_fields = ("c3", "c2_dot_r_i", "c1_term_total", "z_centered",
                      "noise_residual", "decoded_mu")
    for uid in ("1", "3"):
        t = p["traces"][uid]
        assert t["authorized"] is False
        assert t["bit"] is None
        for f in success_fields:
            assert f not in t, f"非接收者不应含 {f}"


# ---- 7. 不影响现有 CS 页面 ----


def test_cs_page_untouched():
    app = (REPO / "web" / "app.py").read_text(encoding="utf-8")
    assert "chw25" not in app.lower(), "CS 主页面不应包含 CHW25 代码"
    # CHW25 通过 multipage 机制并存
    assert (REPO / "web" / "pages" / "2_chw25_dbe.py").exists()
    # CS 依赖文件仍在
    assert (REPO / "web" / "cs_visualize.py").exists()
    assert (REPO / "web" / "media_page.py").exists()


# ---- 8. payload 数值来自真实 trace（一致性）----


def test_payload_values_match_recompute():
    """payload 中的 z_centered 必须等于 c3 + c2ᵀr − c1ᵀΣ 的中心代表。"""
    from src.chw25_dbe.algebra import center_scalar

    p = build_payload(N=4, s_set={2, 4}, mu=1)
    q = p["params"]["q"]
    for uid in ("2", "4"):
        t = p["traces"][uid]
        z_raw = (t["c3"] + t["c2_dot_r_i"] - t["c1_term_total"]) % q
        assert center_scalar(z_raw, q) == t["z_centered"]
