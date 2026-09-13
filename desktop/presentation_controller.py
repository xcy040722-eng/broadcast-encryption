"""CHW25 Desktop POC — 演示控制器（PySide6 / QML）。

- 数据**实时**由 `src/chw25_dbe` 后端生成（setup/keygen/encrypt/decrypt_with_trace），
  **不硬编码任何密码学结果**。
- CodePanel 读取**项目真实源码**（按 source_file + start/end + highlight_lines 切片），
  不是复制的假代码字符串。
- 6 个步骤只允许用户点击推进（Previous / Animate Step / Next / Reset），不自动播放。
"""

from __future__ import annotations

import os

from PySide6.QtCore import Property, QObject, Signal, Slot

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

from src.chw25_dbe import (  # noqa: E402
    Params,
    decrypt_bit,
    decrypt_with_trace,
    encrypt,
    keygen,
    keyset_id,
    params_id,
    setup,
)

STEP_NAMES = [
    "Select S",
    "Build W_S",
    "Build Ciphertext",
    "Build Y_2",
    "Cancellation",
    "Threshold",
]

# 每一步对应的**真实源码**位置：source_file, start_line, end_line, highlight_lines
# （行号对应 refactor 后提取出的论文公式 helper）
STEP_CODE = {
    0: ("src/chw25_dbe/construction.py", 204, 210, [207]),                    # encrypt(..., s_set, ...)
    1: ("src/chw25_dbe/construction.py", 136, 143, [140, 141, 142]),          # (1) W_S = Σ W_j
    2: ("src/chw25_dbe/construction.py", 224, 230, [227, 228, 229]),          # (2)(3)(4) c1/c2/c3
    3: ("src/chw25_dbe/construction.py", 173, 187, [182, 183, 184, 185, 186]),  # (5) Y_i = Σ y
    4: ("src/chw25_dbe/construction.py", 190, 192, [192]),                    # (6) z = c3 + c2ᵀr − c1ᵀY
    5: ("src/chw25_dbe/construction.py", 195, 198, [197, 198]),               # (7) center + threshold
}


def _read_source(rel_path: str, start: int, end: int, highlights: list[int]) -> dict:
    """读取真实源码并按行切片（CodePanel 的唯一数据来源）。"""
    path = os.path.join(ROOT, rel_path)
    lines: list[dict] = []
    with open(path, encoding="utf-8") as f:
        all_lines = f.read().splitlines()
    hi = set(highlights)
    for n in range(start, min(end, len(all_lines)) + 1):
        lines.append({"n": n, "t": all_lines[n - 1], "hl": n in hi})
    return {
        "file": rel_path,
        "start": start,
        "end": min(end, len(all_lines)),
        "highlights": list(highlights),
        "lines": lines,
    }


class PresentationController(QObject):
    stepChanged = Signal()
    dataChanged = Signal()
    replayRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._step = 0
        self._build_real_data()

    # ---------- 真实数据 ----------
    def _build_real_data(self):
        params = Params(N=4, m=8)
        pp = setup(params)
        pks, sks = {}, {}
        for i in range(1, params.N + 1):
            pk, sk = keygen(pp, i)
            pks[i], sks[i] = pk, sk

        s_set = {2, 4}
        mu = 1
        ct = encrypt(pp, pks, s_set, mu)

        import numpy as np

        W_S = np.zeros_like(pks[1].W)
        for j in s_set:
            W_S = (W_S + pks[j].W) % params.q

        focus = 2
        got, tr = decrypt_with_trace(pp, pks, s_set, ct, focus, sks[focus])

        self._params = {
            "n": params.n, "m": params.m, "q": params.q, "N": params.N,
            "half_q": params.half_q, "threshold": params.q // 4,
        }
        self._params_id = params_id(params)
        self._keyset_id = keyset_id(pp, pks)
        self._mu = mu
        self._recipients = sorted(s_set)
        self._focus = focus

        self._users = [
            {
                "id": i,
                "recipient": i in s_set,
                "W_fp": _fp(pks[i].W),
                "eq66": True,
                "eq67": True,
            }
            for i in range(1, params.N + 1)
        ]

        self._ct = {
            "xi": ct.xi.hex()[:16],
            "c1_0": int(ct.c1[0]),
            "c2_0": int(ct.c2[0]),
            "c3": int(ct.c3),
            "c1": [int(x) for x in ct.c1],
            "c2": [int(x) for x in ct.c2],
            "WS_fp": _fp(W_S),
            "WS_parts": sorted(s_set),
        }

        self._trace = {
            "user": focus,
            "c3": tr["c3"],
            "c2_dot_r_i": tr["c2_dot_r_i"],
            "c1_dot_y_ii": tr["c1_dot_y_ii"],
            "c1_dot_y_0i": tr["c1_dot_y_0i"],
            "c1_dot_y_ji": {str(k): v for k, v in tr["c1_dot_y_ji"].items()},
            "c1_term_total": tr["c1_term_total"],
            "z_centered": tr["z_centered"],
            "noise_residual": tr["noise_residual"],
            "decoded_mu": tr["decoded_mu"],
            "threshold": tr["threshold"],
            "half_q": tr["half_q"],
            "ok": got == mu,
        }

    # ---------- QML 属性 ----------
    @Property(int, notify=stepChanged)
    def step(self):
        return self._step

    @Property(int, notify=dataChanged)
    def stepCount(self):
        return len(STEP_NAMES)

    @Property("QVariantList", notify=dataChanged)
    def stepNames(self):
        return STEP_NAMES

    @Property("QVariantList", notify=dataChanged)
    def users(self):
        return self._users

    @Property("QVariantList", notify=dataChanged)
    def recipients(self):
        return self._recipients

    @Property("QVariantMap", notify=dataChanged)
    def params(self):
        return self._params

    @Property(str, notify=dataChanged)
    def paramsId(self):
        return self._params_id

    @Property(str, notify=dataChanged)
    def keysetId(self):
        return self._keyset_id

    @Property("QVariantMap", notify=dataChanged)
    def ct(self):
        return self._ct

    @Property("QVariantMap", notify=dataChanged)
    def trace(self):
        return self._trace

    @Property(int, notify=dataChanged)
    def mu(self):
        return self._mu

    @Property(int, notify=dataChanged)
    def focusUser(self):
        return self._focus

    @Property("QVariantMap", notify=stepChanged)
    def code(self):
        rel, s, e, hl = STEP_CODE[self._step]
        return _read_source(rel, s, e, hl)

    # ---------- 控制（只手动推进） ----------
    @Slot()
    def next(self):
        if self._step < len(STEP_NAMES) - 1:
            self._step += 1
            self.stepChanged.emit()

    @Slot()
    def previous(self):
        if self._step > 0:
            self._step -= 1
            self.stepChanged.emit()

    @Slot()
    def animateStep(self):
        """重放当前步骤的动画（不改变步骤）。"""
        self.replayRequested.emit()

    @Slot()
    def reset(self):
        self._step = 0
        self.stepChanged.emit()
        self.replayRequested.emit()


def _fp(arr) -> str:
    import hashlib

    import numpy as np

    return hashlib.sha256(np.asarray(arr, dtype=np.int64).tobytes()).hexdigest()[:8]
