"""Interactive tree canvas for the unified Complete Subtree workbench."""

from __future__ import annotations

from math import hypot

from PySide6.QtCore import QPointF, QRectF, Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from src.complete_subtree_mre.interactive_session import CsSessionSnapshot
from src.complete_subtree_mre.tree import CompleteSubtreeTree

from .widgets import CS_K_MIME


class CompleteSubtreeCanvas(QWidget):
    """Projection of ST(R), Cover, wrapped headers and the current receiver path."""

    wrapRequested = Signal(int)
    nodeSelected = Signal(int)

    def __init__(self, tree: CompleteSubtreeTree):
        super().__init__()
        self.tree = tree
        self.setAcceptDrops(True)
        self.setMinimumSize(620, 430)
        self._snapshot: CsSessionSnapshot | None = None
        self._receiver_path: tuple[int, ...] = ()
        self._matched_node: int | None = None
        self._failed_target: int | None = None
        self._centers: dict[int, QPointF] = {}

    def set_snapshot(self, snapshot: CsSessionSnapshot) -> None:
        self._snapshot = snapshot
        self.update()

    def set_receiver_result(
        self,
        *,
        path: tuple[int, ...] = (),
        matched_node: int | None = None,
        failed_target: int | None = None,
    ) -> None:
        self._receiver_path = path
        self._matched_node = matched_node
        self._failed_target = failed_target
        self.update()

    def clear_receiver_result(self) -> None:
        self.set_receiver_result()

    def _layout(self) -> dict[int, QPointF]:
        width = max(1, self.width())
        height = max(1, self.height())
        left, right, top, bottom = 34.0, 34.0, 38.0, 48.0
        usable_h = max(1.0, height - top - bottom)
        centers: dict[int, QPointF] = {}
        for node in range(1, self.tree.node_count + 1):
            depth = node.bit_length() - 1
            level_start = 1 << depth
            pos = node - level_start
            count = 1 << depth
            x = left + (width - left - right) * ((pos + 0.5) / count)
            y = top if self.tree.height == 0 else top + usable_h * depth / self.tree.height
            centers[node] = QPointF(x, y)
        self._centers = centers
        return centers

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        centers = self._layout()

        edge_pen = QPen(Qt.GlobalColor.lightGray, 1.4)
        painter.setPen(edge_pen)
        for node, center in centers.items():
            for child in self.tree.children(node):
                painter.drawLine(center, centers[child])

        snapshot = self._snapshot
        revoked = set(snapshot.revoked_users) if snapshot else set()
        st = set(snapshot.steiner_nodes) if snapshot else set()
        cover = set(snapshot.cover_roots) if snapshot else set()
        wrapped = set(snapshot.wrapped_nodes) if snapshot else set()
        path = set(self._receiver_path)

        for node, center in centers.items():
            rect = QRectF(center.x() - 20, center.y() - 20, 40, 40)
            fill = Qt.GlobalColor.white
            border = Qt.GlobalColor.gray

            if node in st:
                fill = Qt.GlobalColor.yellow
                border = Qt.GlobalColor.darkYellow
            if node in cover:
                fill = Qt.GlobalColor.green
                border = Qt.GlobalColor.darkGreen
            if node in wrapped:
                fill = Qt.GlobalColor.green
                border = Qt.GlobalColor.darkGreen
            if self.tree.is_leaf(node) and self.tree.user_of_leaf(node) in revoked:
                fill = Qt.GlobalColor.red
                border = Qt.GlobalColor.darkRed

            pen_width = 2.0 if node in cover or node in st else 1.2
            if node in path:
                border = Qt.GlobalColor.blue
                pen_width = 3.0
            if node == self._matched_node:
                border = Qt.GlobalColor.darkGreen
                pen_width = 4.0
            if node == self._failed_target:
                border = Qt.GlobalColor.red
                pen_width = 4.0

            painter.setPen(QPen(border, pen_width))
            painter.setBrush(fill)
            painter.drawEllipse(rect)

            label = f"v{node}"
            if self.tree.is_leaf(node):
                label += f"\nu{self.tree.user_of_leaf(node)}"
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

            if node in wrapped:
                badge = QRectF(rect.right() - 7, rect.top() - 7, 14, 14)
                painter.setBrush(Qt.GlobalColor.darkGreen)
                painter.setPen(Qt.GlobalColor.darkGreen)
                painter.drawEllipse(badge)

    def _node_at(self, point: QPointF) -> int | None:
        if not self._centers:
            self._layout()
        nearest: tuple[float, int] | None = None
        for node, center in self._centers.items():
            distance = hypot(point.x() - center.x(), point.y() - center.y())
            if distance <= 25 and (nearest is None or distance < nearest[0]):
                nearest = (distance, node)
        return None if nearest is None else nearest[1]

    def request_wrap_for_node(self, node_id: int) -> bool:
        """Shared guard used by real drop events and headless signal tests."""
        snap = self._snapshot
        if snap is None:
            return False
        if node_id not in snap.cover_roots or node_id in snap.wrapped_nodes:
            return False
        if snap.content_key_fingerprint is None:
            return False
        self.wrapRequested.emit(node_id)
        return True

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(CS_K_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if not event.mimeData().hasFormat(CS_K_MIME):
            event.ignore()
            return
        node = self._node_at(event.position())
        if node is not None and self.request_wrap_for_node(node):
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event) -> None:
        node = self._node_at(event.position())
        if node is not None:
            self.nodeSelected.emit(node)
        super().mousePressEvent(event)
