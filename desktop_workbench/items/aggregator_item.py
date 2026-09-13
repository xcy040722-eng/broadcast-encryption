"""AggregatorItem：W_S 聚合器（拖放目标）。"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsObject

from ..palette import BORDER, CIPHERTEXT, MUTED, TEXT


class AggregatorItem(QGraphicsObject):
    W = 300.0
    H = 132.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.slots: list[str] = []
        self.result_label = ""
        self._hot = False
        self.setAcceptHoverEvents(True)
        self.setZValue(1)

    def boundingRect(self) -> QRectF:
        return QRectF(-self.W / 2, -self.H / 2, self.W, self.H)

    def paint(self, p: QPainter, option, widget=None):
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = self.boundingRect()
        path = QPainterPath()
        path.addRoundedRect(r, 12, 12)

        accent = QColor(CIPHERTEXT)
        fill = QColor(accent)
        fill.setAlpha(34 if self._hot else 20)
        p.setBrush(QBrush(fill))
        pen = QPen(accent, 3 if self._hot else 2, Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawPath(path)

        p.setPen(QPen(QColor(MUTED)))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(r.left(), r.top() + 8, r.width(), 18),
                   Qt.AlignmentFlag.AlignHCenter, "W_S Aggregator")

        # 槽位表达式：[ W2 ] + [ ? ]
        expr = " + ".join(f"[ {s} ]" for s in self.slots) if self.slots else "[ ? ]"
        p.setPen(QPen(QColor(TEXT)))
        p.setFont(QFont("Consolas", 12))
        p.drawText(QRectF(r.left(), r.top() + 44, r.width(), 24),
                   Qt.AlignmentFlag.AlignHCenter, expr)

        if self.result_label:
            p.setPen(QPen(QColor(TEXT)))
            p.setFont(QFont("Consolas", 13, QFont.Weight.Bold))
            p.drawText(QRectF(r.left(), r.top() + 74, r.width(), 22),
                       Qt.AlignmentFlag.AlignHCenter, self.result_label)
            p.setPen(QPen(QColor(MUTED)))
            p.setFont(QFont("Consolas", 9))
            p.drawText(QRectF(r.left(), r.top() + 98, r.width(), 20),
                       Qt.AlignmentFlag.AlignHCenter, self.footer)

    # ---- 状态 ----
    def set_slots(self, slots: list[str]):
        self.slots = list(slots)
        self.update()

    def set_result(self, label: str, footer: str = ""):
        self.result_label = label
        self.footer = footer
        self.update()

    def set_hot(self, on: bool):
        self._hot = on
        self.update()
