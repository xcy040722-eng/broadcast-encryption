"""UserItem：用户节点（圆形）+ 其 public-key token W_i。"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsObject

from ..palette import AUTHORIZED, DISABLED, MUTED, TEXT


class UserItem(QGraphicsObject):
    R = 40.0

    def __init__(self, uid: int, recipient: bool, parent=None):
        super().__init__(parent)
        self.uid = uid
        self.recipient = recipient
        self.holding: list = []      # 已放入 aggregator 的 token key
        self.setZValue(5)

    def boundingRect(self) -> QRectF:
        return QRectF(-self.R, -self.R, 2 * self.R, 2 * self.R)

    def paint(self, p: QPainter, option, widget=None):
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        accent = QColor(AUTHORIZED if self.recipient else DISABLED)
        fill = QColor(accent)
        fill.setAlpha(60 if self.recipient else 28)

        p.setBrush(QBrush(fill))
        p.setPen(QPen(accent, 2.5))
        p.drawEllipse(self.boundingRect())

        p.setPen(QPen(QColor(TEXT if self.recipient else MUTED)))
        p.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        p.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, f"u{self.uid}")
