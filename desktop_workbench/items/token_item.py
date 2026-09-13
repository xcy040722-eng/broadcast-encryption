"""TokenItem：可拖动的语义 token（W_i / W_S / c_i …）。"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsObject

from ..palette import TEXT


class TokenItem(QGraphicsObject):
    dropped = Signal(object)     # 拖动释放（携带自身）
    clicked = Signal(object)

    def __init__(self, key: str, label: str, color: str,
                 w: float = 96, h: float = 34, parent=None):
        super().__init__(parent)
        self.key = key
        self.label = label
        self.accent = QColor(color)
        self._w, self._h = w, h
        self._selected = False
        self._dimmed = False
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(10)

    # ---- 绘制 ----
    def boundingRect(self) -> QRectF:
        return QRectF(-self._w / 2, -self._h / 2, self._w, self._h)

    def paint(self, p: QPainter, option, widget=None):
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = self.boundingRect()
        path = QPainterPath()
        path.addRoundedRect(r, 9, 9)

        fill = QColor(self.accent)
        fill.setAlpha(70 if self._selected else 40)
        if self._dimmed:
            fill.setAlpha(16)

        p.setBrush(QBrush(fill))
        pen = QPen(self.accent, 3 if self._selected else 2)
        if self._dimmed:
            pen.setColor(QColor(self.accent).darker(220))
        p.setPen(pen)
        p.drawPath(path)

        col = TEXT if not self._dimmed else "#4b5568"
        p.setPen(QPen(QColor(col)))
        f = QFont("Segoe UI", 9)
        p.setFont(f)
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.label)

    # ---- 状态 ----
    def set_selected(self, on: bool):
        self._selected = on
        self.update()

    def set_dimmed(self, on: bool):
        self._dimmed = on
        self.update()

    def set_label(self, text: str):
        self.label = text
        self.update()

    # ---- 交互 ----
    def mousePressEvent(self, e):
        self.clicked.emit(self)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.dropped.emit(self)
