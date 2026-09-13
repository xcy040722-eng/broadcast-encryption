"""ConnectionItem：两个 term 之间的连接线（用于 cancellation 的公共项）。"""

from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsPathItem


class ConnectionItem(QGraphicsPathItem):
    def __init__(self, a: QPointF, b: QPointF, color: str, parent=None):
        super().__init__(parent)
        path = QPainterPath(a)
        dx = (b.x() - a.x()) * 0.45
        path.cubicTo(QPointF(a.x() + dx, a.y()), QPointF(b.x() - dx, b.y()), b)
        self.setPath(path)
        self.setPen(QPen(QColor(color), 2.4))
        self.setZValue(0)
