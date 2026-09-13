"""TermItem：cancellation 中的一项（可点击选择 / 划消）。"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsObject

from ..palette import BORDER, DISABLED, MUTED, TEXT


class TermItem(QGraphicsObject):
    clicked = Signal(object)

    def __init__(self, side: str, key: str | None, label: str, color: str,
                 w: float = 300, h: float = 40, parent=None):
        super().__init__(parent)
        self.side = side          # "L" / "R"
        self.key = key            # 公共项的标识；None 表示不可消去（μ⌊q/2⌋ / ẽ）
        self.label = label
        self.accent = QColor(color)
        self._w, self._h = w, h
        self._selected = False
        self._cancelled = False
        self.setAcceptHoverEvents(True)
        self.setZValue(10)

    def boundingRect(self) -> QRectF:
        return QRectF(-self._w / 2, -self._h / 2, self._w, self._h)

    def paint(self, p: QPainter, option, widget=None):
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = self.boundingRect()
        path = QPainterPath()
        path.addRoundedRect(r, 8, 8)

        if self._cancelled:
            fill = QColor(self.accent)
            fill.setAlpha(10)
            p.setBrush(QBrush(fill))
            pen = QPen(QColor(DISABLED), 1.5)
            p.setPen(pen)
            p.drawPath(path)
            p.setPen(QPen(QColor("#4b5568")))
        else:
            fill = QColor(self.accent)
            fill.setAlpha(60 if self._selected else 30)
            p.setBrush(QBrush(fill))
            p.setPen(QPen(self.accent, 2.5 if self._selected else 1.5))
            p.drawPath(path)
            p.setPen(QPen(QColor(TEXT)))

        p.setFont(QFont("Consolas", 11))
        p.drawText(r.adjusted(10, 0, -10, 0),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.label)

        if self._cancelled:
            # 手绘删除线（避免依赖字体支持）
            y = r.center().y()
            p.setPen(QPen(QColor("#4b5568"), 1.6))
            p.drawLine(int(r.left() + 8), int(y), int(r.right() - 8), int(y))

    # ---- 状态 ----
    def set_selected(self, on: bool):
        self._selected = on
        self.update()

    def set_cancelled(self, on: bool):
        self._cancelled = on
        self.update()

    def mousePressEvent(self, e):
        if not self._cancelled:
            self.clicked.emit(self)
        e.accept()
