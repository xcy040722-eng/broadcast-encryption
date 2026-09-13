"""Manim trace_adapter 测试：确保动画数据全部来自真实运行。

不依赖 Manim（不 import manim），因此可在无渲染环境下运行。
"""

import numpy as np

from demo.media_data import PNG_BYTES
from src.chw25_dbe.algebra import center_scalar
from visualization.manim.trace_adapter import build_scene_data


def test_scene_data_basic():
    d = build_scene_data(N=4, s_set={2, 4}, mu=1, focus_user=2)
    assert d["params"]["N"] == 4
    assert d["recipient_ids"] == [2, 4]
    assert d["A_shape"] == [4, 8]
    assert len(d["users"]) == 4
    assert d["users"][1]["is_recipient"] is True
    assert d["users"][0]["is_recipient"] is False


def test_scene_data_trace_is_real():
    """trace 数值必须与真实公式一致（可复算验证）。"""
    d = build_scene_data(N=4, s_set={2, 4}, mu=1, focus_user=2)
    t = d["trace"]
    q = d["params"]["q"]

    # z = c3 + c2ᵀr − c1ᵀΣy  （mod q，再取中心代表）
    z_raw = (t["c3"] + t["c2_dot_r_i"] - t["c1_term_total"]) % q
    assert center_scalar(z_raw, q) == t["z_centered"]

    # 各项之和恒等式
    assert t["c1_term_total"] == (
        t["c1_dot_y_ii"] + t["c1_dot_y_0i"] + sum(t["c1_dot_y_ji"].values())
    )
    # 噪声远小于阈值
    assert abs(t["noise_residual"]) < t["threshold"]
    # 焦点用户解密正确
    assert t["ok"] is True and t["decoded_mu"] == 1


def test_scene_data_recipients_and_js_terms():
    """S={2,4}, u2：交叉项应含 y_4,2（j∈S\\{i}）。"""
    d = build_scene_data(N=4, s_set={2, 4}, mu=1, focus_user=2)
    assert "4" in d["trace"]["c1_dot_y_ji"]
    assert d["W_S_parts"] == [2, 4]


def test_scene_data_hybrid_real_roundtrip():
    """hybrid 段使用真实媒体闭环：恢复的图片与原图字节一致。"""
    d = build_scene_data(
        N=4, s_set={2, 4}, mu=1, focus_user=2,
        media_bytes=PNG_BYTES, media_name="recovered.png",
    )
    h = d["hybrid"]
    assert h is not None
    assert h["bit_count"] == 256
    assert h["match"] is True
    assert h["recovered_sha256"] == h["original_sha256"]
    assert h["recovered_image_path"] is not None
    # 恢复出的文件确实是原始 PNG
    with open(h["recovered_image_path"], "rb") as f:
        assert f.read() == PNG_BYTES
    # 不导出任何 key 字节
    assert "key_bits" not in h and "key_bytes" not in h
    assert len(h["key_fingerprint"]) == 8


def test_scene_data_no_key_leak():
    d = build_scene_data(N=4, s_set={2, 4}, mu=1, focus_user=2)
    blob = str(d)
    for bad in ("key_bits", "key_bytes", "key_head_hex", "key_tail_hex"):
        assert bad not in blob
    # 用户也不导出私钥向量（只有指纹）
    for u in d["users"]:
        assert "y_vector" not in u and "y_i" not in u
        assert len(u["y_ii_fp"]) == 8
