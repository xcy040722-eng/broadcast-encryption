"""DemoEngine：教学执行层。

**只保存算法状态与交互状态；所有数学一律调用 CHW25 正式 helper**
（build_ws / compute_c1…c3 / build_decryption_term / compute_z / decode_z）。

禁止在本层重写公式。
"""

from __future__ import annotations

import hashlib
import os

import numpy as np
from PySide6.QtCore import QObject, Signal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in os.sys.path:
    os.sys.path.insert(0, ROOT)

from src.chw25_dbe.algebra import center_scalar, mod_q  # noqa: E402
from src.chw25_dbe.construction import (  # noqa: E402
    build_decryption_term,
    build_ws,
    compute_z,
    decode_z,
    derive_rerandomization,
    encrypt,
    keygen,
    setup,
)
from src.chw25_dbe.types import Params  # noqa: E402

CONSTRUCTION = "src/chw25_dbe/construction.py"

TASK_BUILD_WS = "Build W_S from recipient public keys"
TASK_CANCEL = "Cancel matching terms"
TASK_DECODE = "Decode z against the threshold"

# 任务 → 真实源码位置（source_file, start_line, end_line, highlight_lines）
CODE_MAP = {
    TASK_BUILD_WS: (CONSTRUCTION, 136, 143, [140, 141, 142]),      # build_ws  (1)
    "execute_build_ws": (CONSTRUCTION, 225, 225, [225]),           # W_S = build_ws(...)
    TASK_CANCEL: (CONSTRUCTION, 190, 192, [192]),                  # compute_z (6)
    "term": (CONSTRUCTION, 173, 187, [182, 183, 184, 185, 186]),   # build_decryption_term (5)
    TASK_DECODE: (CONSTRUCTION, 195, 198, [197, 198]),             # decode_z (7)
}


def _fp(arr) -> str:
    return hashlib.sha256(np.asarray(arr, dtype=np.int64).tobytes()).hexdigest()[:8]


def read_source(rel: str, start: int, end: int, hl: list[int]) -> list[dict]:
    """读取真实源文件并切片（CodePanel 唯一数据来源）。"""
    path = os.path.join(ROOT, rel)
    with open(path, encoding="utf-8") as f:
        all_lines = f.read().splitlines()
    hi = set(hl)
    return [
        {"n": n, "t": all_lines[n - 1], "hl": n in hi, "cur": False}
        for n in range(start, min(end, len(all_lines)) + 1)
    ]


class DemoEngine(QObject):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.params = Params(N=4, m=8)
        self.pp = setup(self.params)
        self.pks, self.sks = {}, {}
        for i in range(1, self.params.N + 1):
            pk, sk = keygen(self.pp, i)
            self.pks[i], self.sks[i] = pk, sk

        self.s_set = {2, 4}
        self.mu = 1
        self.focus = 2
        self.ct = encrypt(self.pp, self.pks, self.s_set, self.mu)

        # 真实的 W_S（正式 helper）
        self.true_ws = build_ws(self.pp, self.pks, self.s_set)

        # ---- Experiment A 状态 ----
        self.ws_slots: list[int] = []
        self.ws_executed = False
        self.ws_result = None
        self.message = ""
        self.message_kind = "info"      # info | ok | error

        # ---- Experiment B 状态 ----
        self.left_terms = [
            {"key": None,      "label": "mu*floor(q/2)"},
            {"key": "stp",     "label": "+ s^T p"},
            {"key": "w0ws",    "label": "+ s^T (W0+WS) r" + str(self.focus)},
            {"key": "e2",      "label": "+ e~2"},
        ]
        self.right_terms = [
            {"key": "stp",     "label": "+ s^T p"},
            {"key": "w0ws",    "label": "+ s^T (W0+WS) r" + str(self.focus)},
            {"key": "e1",      "label": "+ e~1"},
        ]
        self.selected: dict[str, str | None] = {"L": None, "R": None}
        self.cancelled: set[str] = set()
        self.z_result = None
        self.decode_guess = None
        self.decode_ok = None

    # ================= Experiment A =================

    def user_label(self, uid: int) -> str:
        return f"W{uid}"

    def add_to_ws(self, uid: int) -> bool:
        """把 W_uid 放入 aggregator；非 S 成员被拒绝。"""
        if uid not in self.s_set:
            self._msg(f"User not in recipient set S  (u{uid} ∉ S)", "error")
            return False
        if uid in self.ws_slots:
            self._msg(f"W{uid} already in aggregator", "info")
            return False
        self.ws_slots.append(uid)
        self._msg(f"W{uid} added   →   [ " + " ] + [ ".join(
            self.user_label(j) for j in self.ws_slots) + " ]", "ok")
        return True

    def remove_from_ws(self, uid: int) -> bool:
        if uid in self.ws_slots:
            self.ws_slots.remove(uid)
            self._msg(f"W{uid} removed", "info")
            return True
        return False

    def execute_build_ws(self) -> dict | None:
        """Execute：**真实调用** build_ws()。"""
        if self.ws_slots != sorted(self.s_set):
            self._msg("Place all recipient public keys ( W2, W4 ) first", "error")
            return None
        result = build_ws(self.pp, self.pks, set(self.ws_slots))   # ← 正式 helper
        self.ws_result = result
        self.ws_executed = True
        ok = bool(np.array_equal(result, self.true_ws))
        self._msg("build_ws() executed  →  W_S matches build_ws() ✓" if ok
                  else "W_S mismatch ✗", "ok" if ok else "error")
        return {"W_S": result, "shape": result.shape, "fp": _fp(result), "ok": ok}

    def reset_ws(self):
        self.ws_slots = []
        self.ws_executed = False
        self.ws_result = None
        self._msg("", "info")

    # ================= Experiment B =================

    def select_term(self, side: str, key: str | None) -> tuple[bool, str]:
        if key is None:
            self._msg("This term is not a shared term", "error")
            return False, "not-shared"
        if key in self.cancelled:
            return False, "already"
        self.selected[side] = key
        self.changed.emit()
        return True, "selected"

    def can_cancel(self) -> bool:
        l, r = self.selected["L"], self.selected["R"]
        return l is not None and r is not None and l == r and l not in self.cancelled

    def cancel_selected(self) -> tuple[bool, str]:
        l, r = self.selected["L"], self.selected["R"]
        if l is None or r is None:
            self._msg("Select one LEFT term and one RIGHT term", "error")
            return False, "incomplete"
        if l != r:
            self._msg("Terms do not match", "error")
            return False, "mismatch"
        if l in self.cancelled:
            return False, "already"
        self.cancelled.add(l)
        self.selected = {"L": None, "R": None}
        self._msg(f"Matching terms  ✓  —  cancelled '{l}'", "ok")
        self.changed.emit()
        return True, "cancelled"

    def all_cancelled(self) -> bool:
        return {"stp", "w0ws"} <= self.cancelled

    def compute_z_now(self) -> dict | None:
        """**真实调用** build_decryption_term() + compute_z()。"""
        if not self.all_cancelled():
            self._msg("Cancel all shared terms first", "error")
            return None
        q = self.params.q
        _, y0 = derive_rerandomization(self.pp, self.s_set, self.ct.xi)
        term = build_decryption_term(                   # ← (5)
            self.pp, self.pks, self.s_set, self.focus, self.sks[self.focus], y0
        )
        r_i = self.pp.R[:, self.focus - 1]
        z_raw = compute_z(self.ct, r_i, term)           # ← (6)
        z = int(mod_q(z_raw, q))
        zc = center_scalar(z, q)
        self.z_result = {"z_raw": z_raw, "z": z, "z_centered": zc,
                         "term_fp": _fp(term), "half_q": self.params.half_q}
        self._msg(f"compute_z() executed  →  z_centered = {zc}", "ok")
        return self.z_result

    # ================= Threshold =================

    def submit_decode(self, guess: int) -> dict | None:
        """用户先选 0/1，再**真实调用** decode_z() 判定。"""
        if self.z_result is None:
            self._msg("Compute z first", "error")
            return None
        truth = decode_z(self.z_result["z"], self.params.q)      # ← (7)
        ok = (guess == truth)
        self.decode_guess = guess
        self.decode_ok = ok
        self._msg(("Correct ✓" if ok else "Incorrect ✗")
                  + f"   mu = {truth}", "ok" if ok else "error")
        return {"guess": guess, "mu": truth, "correct": ok, "z_centered": self.z_result["z_centered"]}

    # ================= 源码 / 变量 =================

    def code_for(self, tag: str) -> list[dict]:
        rel, s, e, hl = CODE_MAP[tag]
        return read_source(rel, s, e, hl)

    def variables(self) -> list[tuple[str, str]]:
        p = self.params
        v = [
            ("q", str(p.q)),
            ("S", "{" + ",".join(str(x) for x in sorted(self.s_set)) + "}"),
            ("mu", str(self.mu)),
        ]
        if self.ws_slots:
            v.append(("j (in aggregator)", ",".join(str(x) for x in self.ws_slots)))
        if self.ws_executed and self.ws_result is not None:
            v.append(("W_S", f"matrix{self.ws_result.shape}"))
            v.append(("W_S.fp", _fp(self.ws_result)))
        if self.cancelled:
            v.append(("cancelled", ",".join(sorted(self.cancelled))))
        if self.z_result:
            v.append(("z", str(self.z_result["z"])))
            v.append(("z_centered", str(self.z_result["z_centered"])))
        if self.decode_guess is not None:
            v.append(("guess", str(self.decode_guess)))
            v.append(("decode_z()", str(self.decode_ok)))
        return v

    # ================= 内部 =================

    def _msg(self, text: str, kind: str):
        self.message = text
        self.message_kind = kind
        self.changed.emit()
