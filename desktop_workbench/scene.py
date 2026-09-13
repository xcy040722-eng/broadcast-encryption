"""交互场景：Build W_S（拖放）+ Interactive Cancellation（点选消去）。

用 QGraphicsScene 的 persistent objects / drag / hit-test / connection，
而不是 QML 的 state-transition timeline。
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from .items.aggregator_item import AggregatorItem
from .items.connection_item import ConnectionItem
from .items.term_item import TermItem
from .items.token_item import TokenItem
from .items.user_item import UserItem
from .palette import (
    AUTHORIZED,
    BG,
    BORDER,
    CIPHERTEXT,
    DISABLED,
    MUTED,
    NOISE,
    PUBLIC,
    RERANDOM,
    SECRET,
    SURFACE,
    TEXT,
)

TERM_COLOR = {
    "stp": PUBLIC,       # 公共项：s^T p（两侧同色）
    "w0ws": RERANDOM,    # 公共项：s^T (W0+WS) r
    "e2": NOISE,
    "e1": NOISE,
    None: SECRET,        # μ⌊q/2⌋
}


class StageView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setBackgroundBrush(QBrush(QColor(BG)))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


# ===================== Experiment A: Build W_S =====================


class BuildWSScene(QGraphicsScene):
    token_dropped = Signal(str)      # token.key
    token_clicked = Signal(str)

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setBackgroundBrush(QBrush(QColor(SURFACE)))
        self.setSceneRect(0, 0, 940, 560)

        # Sender
        self.sender_tok = TokenItem("sender", "Sender", CIPHERTEXT, w=120, h=36)
        self.sender_tok.setPos(470, 54)
        self.addItem(self.sender_tok)
        self.sender_tok.setFlag(TokenItem.GraphicsItemFlag.ItemIsMovable, False)

        # Aggregator
        self.aggregator = AggregatorItem()
        self.aggregator.setPos(470, 280)
        self.addItem(self.aggregator)

        # Users + their W tokens
        self.users: dict[int, UserItem] = {}
        self.tokens: dict[int, TokenItem] = {}
        xs = [150, 350, 590, 790]
        for idx, uid in enumerate(range(1, 5)):
            u = UserItem(uid, recipient=(uid in engine.s_set))
            u.setPos(xs[idx], 470)
            self.addItem(u)
            self.users[uid] = u

            tk = TokenItem(f"W{uid}", f"W{uid}",
                           PUBLIC if uid in engine.s_set else DISABLED,
                           w=60, h=30)
            tk.setPos(xs[idx], 380)
            tk.setFlag(TokenItem.GraphicsItemFlag.ItemIsMovable, uid in engine.s_set)
            self.addItem(tk)
            self.tokens[uid] = tk
            tk.clicked.connect(lambda t: self.token_clicked.emit(t.key))
            tk.dropped.connect(lambda t: self.token_dropped.emit(t.key))

    def refresh(self):
        ev = self.engine
        self.aggregator.set_slots([ev.user_label(j) for j in ev.ws_slots])
        if ev.ws_executed and ev.ws_result is not None:
            import hashlib

            import numpy as _np

            fp = hashlib.sha256(
                _np.asarray(ev.ws_result, dtype=_np.int64).tobytes()
            ).hexdigest()[:8]
            self.aggregator.set_result("W_S", f"{ev.ws_result.shape}   fp {fp}")
        for uid, tk in self.tokens.items():
            tk.set_dimmed(uid in ev.ws_slots)

    def on_release(self, token_key: str):
        """Release 时判断是否落在 aggregator 上。"""
        if not token_key.startswith("W"):
            return
        uid = int(token_key[1:])
        tk = self.tokens[uid]
        if self.aggregator.sceneBoundingRect().intersects(tk.sceneBoundingRect()):
            self.engine.add_to_ws(uid)
            self.refresh()
        else:
            # 回到原处
            tk.setPos(self.users[uid].pos() + QPointF(0, -90))

    def merge_tokens(self):
        """Execute 后：W2/W4 归位到 aggregator 并淡出（视觉 merge）。"""
        for uid in self.engine.ws_slots:
            tk = self.tokens[uid]
            tk.setPos(self.aggregator.pos())
            tk.setVisible(False)


# ===================== Experiment B: Cancellation =====================


class CancellationScene(QGraphicsScene):
    term_clicked = Signal(str, object)     # side, key

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setBackgroundBrush(QBrush(QColor(SURFACE)))
        self.setSceneRect(0, 0, 940, 560)
        self.items_L: list[TermItem] = []
        self.items_R: list[TermItem] = []
        self.conns: list[ConnectionItem] = []
        self._build()

    def _build(self):
        ev = self.engine
        self.addItem(self._caption("LEFT   L = c3 + c2^T r2", 170, 40, TEXT))
        self.addItem(self._caption("RIGHT   R = c1^T Y2", 700, 40, TEXT))

        y = 110
        for t in ev.left_terms:
            it = TermItem("L", t["key"], t["label"], TERM_COLOR[t["key"]], w=300)
            it.setPos(180, y)
            it.clicked.connect(lambda o: self.term_clicked.emit("L", o.key))
            self.addItem(it)
            self.items_L.append(it)
            y += 56

        y = 110
        for t in ev.right_terms:
            it = TermItem("R", t["key"], t["label"], TERM_COLOR[t["key"]], w=300)
            it.setPos(700, y)
            it.clicked.connect(lambda o: self.term_clicked.emit("R", o.key))
            self.addItem(it)
            self.items_R.append(it)
            y += 56

        self.result = self.addText("", QFont("Consolas", 13))
        self.result.setDefaultTextColor(QColor(TEXT))
        self.result.setPos(180, 430)

    def _caption(self, text: str, x: float, y: float, color: str):
        t = self.addText(text, QFont("Consolas", 11))
        t.setDefaultTextColor(QColor(color))
        t.setPos(x, y)
        return t

    def refresh(self):
        ev = self.engine
        for it in self.items_L + self.items_R:
            if it.key is None:
                continue
            it.set_selected(ev.selected[it.side] == it.key)
            if it.key in ev.cancelled and not it._cancelled:
                self._strike(it)
        self.result.setPlainText(
            "z = c3 + c2^T r2 - c1^T Y2" if not ev.all_cancelled()
            else ("z = mu*floor(q/2) - e~1 + e~2" +
                  (f"   =  {ev.z_result['z_centered']}" if ev.z_result else ""))
        )

    def _strike(self, it: TermItem):
        """划消：连线 + 删除线 + 淡出。"""
        it.set_cancelled(True)
        mate = None
        for other in (self.items_R if it.side == "L" else self.items_L):
            if other.key == it.key and not other._cancelled:
                mate = other
                break
        if mate is not None:
            mate.set_cancelled(True)
            c = ConnectionItem(it.scenePos(), mate.scenePos(), TERM_COLOR[it.key])
            self.addItem(c)
            self.conns.append(c)

    def reset_visual(self):
        for it in self.items_L + self.items_R:
            it.set_cancelled(False)
            it.set_selected(False)
        for c in self.conns:
            self.removeItem(c)
        self.conns.clear()
        self.result.setPlainText("")


# ===================== Threshold =====================


class ThresholdScene(QGraphicsScene):
    guess = Signal(int)

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setBackgroundBrush(QBrush(QColor(SURFACE)))
        self.setSceneRect(0, 0, 940, 560)
        self.x0, self.x1, self.y = 110.0, 830.0, 250.0

    def npos(self, frac: float) -> float:
        return self.x0 + (frac + 1) / 2 * (self.x1 - self.x0)

    def build(self):
        self.clear()
        q = self.engine.params.q
        band = self.addRect(self.npos(-0.5), self.y - 5,
                            self.npos(0.5) - self.npos(-0.5), 10,
                            QPen(Qt.PenStyle.NoPen), QBrush(QColor(85, 214, 139, 90)))
        band.setZValue(-1)
        self.addLine(self.x0, self.y, self.x1, self.y, QPen(QColor(MUTED), 2))
        for frac, lab in [(-1.0, "-q/2"), (-0.5, "-q/4"), (0.0, "0"),
                          (0.5, "q/4"), (1.0, "q/2")]:
            x = self.npos(frac)
            self.addLine(x, self.y - 9, x, self.y + 9, QPen(QColor(MUTED), 1.5))
            t = self.addText(lab, QFont("Consolas", 10))
            t.setDefaultTextColor(QColor(MUTED))
            t.setPos(x - 18, self.y + 16)

        zr = self.engine.z_result
        if zr:
            frac = max(-1.0, min(1.0, zr["z_centered"] / zr["half_q"]))
            dot = self.addEllipse(self.npos(frac) - 8, self.y - 8, 16, 16,
                                  QPen(QColor(NOISE), 2), QBrush(QColor(NOISE)))
            dot.setZValue(3)
            zt = self.addText(f"z_centered = {zr['z_centered']}", QFont("Consolas", 12))
            zt.setDefaultTextColor(QColor(TEXT))
            zt.setPos(self.x0, self.y - 70)

        if self.engine.decode_ok is not None:
            msg = ("Correct ✓   mu = " + str(
                decode_mu_of(self.engine))) if self.engine.decode_ok else "Incorrect ✗"
            rt = self.addText(msg, QFont("Consolas", 15, QFont.Weight.Bold))
            rt.setDefaultTextColor(QColor(AUTHORIZED if self.engine.decode_ok else NOISE))
            rt.setPos(self.x0, self.y + 70)


def decode_mu_of(engine) -> int:
    from src.chw25_dbe.construction import decode_z

    return decode_z(engine.z_result["z"], engine.params.q)
