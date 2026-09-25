"""Interactive relationship canvas for the SM2 + SM4 workbench.

The canvas is a visual projection of InteractiveSession state. It never owns or
receives raw secret key material. The only content-key value exposed here is
its SM3 fingerprint.

Direct manipulation remains real: dragging the visible K node emits the same
content-key MIME token used by the functional cards; dropping it on an
eligible recipient emits wrapRequested(user_id), and dropping it on the media
engine emits encryptRequested(). WorkbenchWindow maps those signals onto the
validated InteractiveSession methods.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QMimeData, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .i18n import Translator
from .widgets import CONTENT_KEY_MIME


_CANVAS_TEXT = {
    "zh_CN": {
        "help": "从 K 节点直接拖拽到接收者公钥或 SM4-GCM 节点，操作会真实调用后端。",
        "key_title": "SM4 内容密钥 K",
        "key_empty": "尚未生成",
        "media_title": "媒体 M",
        "media_empty": "尚未选择",
        "engine_title": "SM4-GCM",
        "drop_key": "将 K 拖到这里",
        "done": "已完成",
        "package_title": "广播包",
        "package_done": "已组装 .smre",
        "package_ready": "已满足组包条件",
        "package_wait": "等待 E[i] 与媒体密文",
        "wrapped": "已生成密钥封装",
        "no_recipients": "先在左侧选择接收者集合 S；这里会出现对应的 PK[i] → E[i] 节点。",
    },
    "en_US": {
        "help": "Drag K directly to a recipient public-key node or SM4-GCM; the drop calls the real backend.",
        "key_title": "SM4 content key K",
        "key_empty": "not generated",
        "media_title": "Media M",
        "media_empty": "not selected",
        "engine_title": "SM4-GCM",
        "drop_key": "Drop K here",
        "done": "complete",
        "package_title": "Broadcast package",
        "package_done": ".smre assembled",
        "package_ready": "ready to assemble",
        "package_wait": "waiting for E[i] + media ciphertext",
        "wrapped": "wrapped key ready",
        "no_recipients": "Choose recipient set S on the left; matching PK[i] → E[i] nodes will appear here.",
    },
}


@dataclass(frozen=True)
class CanvasState:
    recipients: tuple[str, ...] = ()
    wrapped: tuple[str, ...] = ()
    content_key_fingerprint: str | None = None
    media_name: str | None = None
    payload_ready: bool = False
    package_ready: bool = False
    package_assembled: bool = False


class CryptoRelationCanvas(QWidget):
    """Draw and directly manipulate the live cryptographic object graph."""

    wrapRequested = Signal(str)
    encryptRequested = Signal()

    def __init__(self, i18n: Translator | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.i18n = i18n or Translator()
        self.state = CanvasState()
        self._regions: dict[str, QRectF] = {}
        self._hover_target: str | None = None
        self.setAcceptDrops(True)
        self.setMinimumHeight(280)
        self.setMouseTracking(True)
        self.setObjectName("cryptoRelationCanvas")
        self.setToolTip(self._t("help"))

    def _t(self, key: str) -> str:
        language = self.i18n.language if self.i18n.language in _CANVAS_TEXT else "en_US"
        return _CANVAS_TEXT[language][key]

    def update_state(
        self,
        *,
        recipients: tuple[str, ...],
        wrapped: tuple[str, ...],
        content_key_fingerprint: str | None,
        media_name: str | None,
        payload_ready: bool,
        package_ready: bool,
        package_assembled: bool,
    ) -> None:
        self.state = CanvasState(
            recipients=tuple(recipients),
            wrapped=tuple(wrapped),
            content_key_fingerprint=content_key_fingerprint,
            media_name=media_name,
            payload_ready=payload_ready,
            package_ready=package_ready,
            package_assembled=package_assembled,
        )
        self._hover_target = None
        self.update()

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------
    def _layout_regions(self) -> dict[str, QRectF]:
        w = max(720.0, float(self.width()))
        h = max(260.0, float(self.height()))
        margin = 18.0
        node_w = 160.0
        node_h = 58.0

        regions: dict[str, QRectF] = {
            "key": QRectF(margin, 38.0, node_w, node_h),
            "media": QRectF(margin, h - node_h - 28.0, node_w, node_h),
            "engine": QRectF(w * 0.42, h - node_h - 28.0, 190.0, node_h),
            "package": QRectF(w - node_w - margin, h * 0.5 - 34.0, node_w, 68.0),
        }

        recipients = self.state.recipients
        center_x = w * 0.42
        if recipients:
            available_top = 24.0
            available_bottom = regions["engine"].top() - 24.0
            total = max(1.0, available_bottom - available_top)
            slot = total / len(recipients)
            rh = min(54.0, max(38.0, slot - 8.0))
            for index, user_id in enumerate(recipients):
                y = available_top + index * slot + (slot - rh) / 2.0
                regions[f"recipient:{user_id}"] = QRectF(center_x, y, 190.0, rh)
        return regions

    @staticmethod
    def _center_left(rect: QRectF) -> QPointF:
        return QPointF(rect.left(), rect.center().y())

    @staticmethod
    def _center_right(rect: QRectF) -> QPointF:
        return QPointF(rect.right(), rect.center().y())

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().paintEvent(event)
        self._regions = self._layout_regions()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#FBFCFE"))

        key = self._regions["key"]
        media = self._regions["media"]
        engine = self._regions["engine"]
        package = self._regions["package"]

        # Relationship edges are painted first so nodes remain visually crisp.
        for user_id in self.state.recipients:
            recipient = self._regions[f"recipient:{user_id}"]
            self._draw_arrow(
                painter,
                self._center_right(key),
                self._center_left(recipient),
                done=user_id in self.state.wrapped,
            )
            self._draw_arrow(
                painter,
                self._center_right(recipient),
                self._center_left(package),
                done=user_id in self.state.wrapped,
            )

        self._draw_arrow(
            painter,
            self._center_right(key),
            self._center_left(engine),
            done=self.state.payload_ready,
        )
        self._draw_arrow(
            painter,
            self._center_right(media),
            self._center_left(engine),
            done=self.state.payload_ready,
        )
        self._draw_arrow(
            painter,
            self._center_right(engine),
            self._center_left(package),
            done=self.state.payload_ready,
        )

        self._draw_node(
            painter,
            key,
            self._t("key_title"),
            self._key_detail(),
            ready=self.state.content_key_fingerprint is not None,
            draggable=self.state.content_key_fingerprint is not None,
            hovered=self._hover_target == "key",
        )
        self._draw_node(
            painter,
            media,
            self._t("media_title"),
            self.state.media_name or self._t("media_empty"),
            ready=self.state.media_name is not None,
        )
        self._draw_node(
            painter,
            engine,
            self._t("engine_title"),
            self._t("done") if self.state.payload_ready else self._t("drop_key"),
            ready=self.state.payload_ready,
            hovered=self._hover_target == "engine",
        )
        self._draw_node(
            painter,
            package,
            self._t("package_title"),
            self._package_detail(),
            ready=self.state.package_assembled,
            pending=self.state.package_ready and not self.state.package_assembled,
        )

        for user_id in self.state.recipients:
            rect = self._regions[f"recipient:{user_id}"]
            wrapped = user_id in self.state.wrapped
            self._draw_node(
                painter,
                rect,
                f"PK[{user_id}] → E[{user_id}]",
                self._t("wrapped") if wrapped else self._t("drop_key"),
                ready=wrapped,
                hovered=self._hover_target == f"recipient:{user_id}",
            )

        if not self.state.recipients:
            painter.setPen(QColor("#7B879A"))
            painter.drawText(
                QRectF(self.width() * 0.35, 55.0, self.width() * 0.35, 80.0),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self._t("no_recipients"),
            )

        painter.end()

    def _key_detail(self) -> str:
        fp = self.state.content_key_fingerprint
        if not fp:
            return self._t("key_empty")
        return f"SM3 fp: {fp[:16]}"

    def _package_detail(self) -> str:
        if self.state.package_assembled:
            return self._t("package_done")
        if self.state.package_ready:
            return self._t("package_ready")
        return self._t("package_wait")

    def _draw_node(
        self,
        painter: QPainter,
        rect: QRectF,
        title: str,
        detail: str,
        *,
        ready: bool = False,
        pending: bool = False,
        draggable: bool = False,
        hovered: bool = False,
    ) -> None:
        if ready:
            fill = QColor("#EEF8F3")
            border = QColor("#77B792")
        elif pending:
            fill = QColor("#FFF8E8")
            border = QColor("#D9B35D")
        elif hovered:
            fill = QColor("#EAF2FF")
            border = QColor("#4D8EDC")
        else:
            fill = QColor("#FFFFFF")
            border = QColor("#C9D5E4")

        painter.setPen(QPen(border, 1.4))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 9.0, 9.0)

        title_rect = QRectF(rect.left() + 10, rect.top() + 7, rect.width() - 20, 20)
        detail_rect = QRectF(rect.left() + 10, rect.top() + 29, rect.width() - 20, rect.height() - 34)
        painter.setPen(QColor("#17304F"))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#6D7D93"))
        painter.drawText(
            detail_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
            detail,
        )
        if draggable:
            painter.setPen(QColor("#2D69AE"))
            painter.drawText(
                QRectF(rect.right() - 28, rect.top() + 5, 20, 20),
                Qt.AlignmentFlag.AlignCenter,
                "↗",
            )

    def _draw_arrow(
        self,
        painter: QPainter,
        start: QPointF,
        end: QPointF,
        *,
        done: bool,
    ) -> None:
        color = QColor("#6EAE88") if done else QColor("#C0CBD8")
        pen = QPen(color, 2.0 if done else 1.4)
        if not done:
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(color)

        mid_x = (start.x() + end.x()) / 2.0
        painter.drawLine(start, QPointF(mid_x, start.y()))
        painter.drawLine(QPointF(mid_x, start.y()), QPointF(mid_x, end.y()))
        painter.drawLine(QPointF(mid_x, end.y()), end)
        painter.drawLine(end, QPointF(end.x() - 7, end.y() - 4))
        painter.drawLine(end, QPointF(end.x() - 7, end.y() + 4))

    # ------------------------------------------------------------------
    # Direct manipulation
    # ------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API
        regions = self._layout_regions()
        if (
            self.state.content_key_fingerprint is not None
            and event.button() == Qt.MouseButton.LeftButton
            and regions["key"].contains(event.position())
        ):
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData(CONTENT_KEY_MIME, b"session-content-key")
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)
            event.accept()
            return
        super().mousePressEvent(event)

    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self._can_process_drag(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: N802 - Qt API
        if not self._can_process_drag(event):
            self._set_hover(None)
            event.ignore()
            return
        target = self._target_at(event.position())
        self._set_hover(target if self._target_allowed(target) else None)
        if self._hover_target:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._set_hover(None)
        event.accept()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt API
        if not self._can_process_drag(event):
            self._set_hover(None)
            event.ignore()
            return
        target = self._target_at(event.position())
        if not self._target_allowed(target):
            self._set_hover(None)
            event.ignore()
            return

        if target == "engine":
            self.encryptRequested.emit()
        elif target and target.startswith("recipient:"):
            self.wrapRequested.emit(target.split(":", 1)[1])
        else:
            event.ignore()
            return
        self._set_hover(None)
        event.acceptProposedAction()

    def _can_process_drag(self, event) -> bool:
        return (
            self.state.content_key_fingerprint is not None
            and event.mimeData().hasFormat(CONTENT_KEY_MIME)
        )

    def _target_at(self, point: QPointF) -> str | None:
        regions = self._layout_regions()
        for name, rect in regions.items():
            if name == "engine" or name.startswith("recipient:"):
                if rect.contains(point):
                    return name
        return None

    def _target_allowed(self, target: str | None) -> bool:
        if target == "engine":
            return self.state.media_name is not None and not self.state.payload_ready
        if target and target.startswith("recipient:"):
            user_id = target.split(":", 1)[1]
            return user_id in self.state.recipients and user_id not in self.state.wrapped
        return False

    def _set_hover(self, target: str | None) -> None:
        if target == self._hover_target:
            return
        self._hover_target = target
        self.update()
