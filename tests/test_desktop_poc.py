"""Desktop POC（PySide6/QML）控制器测试。

不需要 GUI（不加载 QML），只验证：
- 步骤表与真实源码行号映射；
- 数据来自真实后端（可复算）；
- CodePanel 读取的是**真实源文件内容**；
- 不泄露 key / 私钥明文。
"""

import os

import pytest

pytest.importorskip("PySide6", reason="需要 PySide6")

from desktop.presentation_controller import (  # noqa: E402
    ROOT,
    STEP_CODE,
    STEP_NAMES,
    PresentationController,
)


@pytest.fixture(scope="module")
def ctrl():
    return PresentationController()


def test_step_names():
    assert STEP_NAMES == ["Select S", "Build W_S", "Build Ciphertext",
                          "Build Y_2", "Cancellation", "Threshold"]
    assert len(STEP_CODE) == len(STEP_NAMES)


def test_navigation_is_manual_only(ctrl):
    assert ctrl.step == 0
    ctrl.next()
    assert ctrl.step == 1
    ctrl.previous()
    assert ctrl.step == 0
    ctrl.previous()          # 边界不越界
    assert ctrl.step == 0
    for _ in range(len(STEP_NAMES) + 3):
        ctrl.next()
    assert ctrl.step == len(STEP_NAMES) - 1   # 不越界
    assert ctrl.reset() is None
    assert ctrl.step == 0


def test_real_data_from_backend(ctrl):
    tr = ctrl.trace
    ct = ctrl.ct
    p = ctrl.params
    q = p["q"]
    # z = c3 + c2ᵀr − c1ᵀΣy（mod q），中心代表一致
    from src.chw25_dbe.algebra import center_scalar

    z_raw = (tr["c3"] + tr["c2_dot_r_i"] - tr["c1_term_total"]) % q
    assert center_scalar(z_raw, q) == tr["z_centered"]
    assert abs(tr["noise_residual"]) < tr["threshold"]
    assert tr["ok"] is True and tr["decoded_mu"] == ctrl.mu == 1
    assert ctrl.recipients == [2, 4]
    assert ct["WS_parts"] == [2, 4]
    assert len(ct["c1"]) == p["m"]


def test_code_panel_reads_real_source(ctrl):
    """CodePanel 必须读取真实源码文件内容（不是伪代码字符串）。"""
    for s in range(len(STEP_NAMES)):
        ctrl.reset()
        for _ in range(s):
            ctrl.next()
        code = ctrl.code
        rel, start, end, hl = STEP_CODE[s]
        assert code["file"] == rel
        assert code["start"] == start and code["end"] == end
        assert code["highlights"] == hl
        # 逐行与磁盘上的真实文件比对
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            real = f.read().splitlines()
        for line in code["lines"]:
            assert line["t"] == real[line["n"] - 1], f"第 {line['n']} 行不符"
            assert line["hl"] == (line["n"] in hl)


def test_highlight_lines_are_meaningful(ctrl):
    """Build Ciphertext 的高亮行必须真的包含 c1/c2/c3 赋值。"""
    ctrl.reset()
    ctrl.next(); ctrl.next()          # step 2
    code = ctrl.code
    hl_text = "".join(l["t"] for l in code["lines"] if l["hl"])
    assert "c1 = " in hl_text and "c2 = " in hl_text and "c3 = " in hl_text


def test_no_secret_leak(ctrl):
    """不得导出私钥向量 / 会话密钥字节；只允许指纹与派生标量。"""
    # 用户侧：只有 id / recipient / W 指纹 / 等式布尔
    for u in ctrl.users:
        assert set(u.keys()) == {"id", "recipient", "W_fp", "eq66", "eq67"}
        assert len(u["W_fp"]) == 8
    # trace 侧：全部是标量（int），不存在向量/字节
    for k, v in ctrl.trace.items():
        assert not isinstance(v, (list, bytes, bytearray)), f"{k} 不应是向量/字节"
    for k, v in ctrl.ct.items():
        if k in ("c1", "c2"):
            assert all(isinstance(x, int) for x in v)   # 公开密文分量
        else:
            assert not isinstance(v, (bytes, bytearray)), f"{k} 不应是字节"
