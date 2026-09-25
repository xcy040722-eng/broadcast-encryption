"""Receiver-side visualization for the SM2 + SM4 teaching workbench.

The widget is a projection of a real :class:`DecryptResult`.  It never performs
cryptography and never receives raw secret-key bytes or the raw SM4 content key.
It visualizes where a real receiver attempt stopped:

    SK[user] + E[target] -> SM2 unwrap -> K -> SM4-GCM auth -> plaintext M

For a non-recipient there is no E[user].  For a wrong-key force try, the graph
normally stops at SM2 unwrap.  A successful authorized receiver reaches the
authenticated plaintext node.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from src.sm2_sm4_mre.types import DecryptResult, DecryptStatus

from .i18n import Translator


_TEXT = {
    "zh_CN": {
        "idle": "组装广播包后，在右侧选择用户执行真实解密；结果会显示在这里。",
        "sk": "私钥 SK[{user}]",
        "wrapped": "密钥封装 E[{target}]",
        "missing_wrapped": "不存在 E[{user}]",
        "unwrap": "SM2 解封",
        "key": "恢复的内容密钥 K",
        "gcm": "SM4-GCM 解密 / 认证",
        "plain": "明文 M",
        "force": "错误私钥强制尝试",
        "normal": "正常接收者解密",
        "success": "成功",
        "failed": "失败",
        "denied": "非接收者：广播包中没有该用户的密钥封装",
        "fp": "指纹 {value}",
        "auth_ok": "认证通过",
        "auth_fail": "认证失败",
        "not_reached": "未到达",
    },
    "en_US": {
        "idle": "Assemble a package, then run a real receiver attempt; the result appears here.",
        "sk": "Private key SK[{user}]",
        "wrapped": "Wrapped key E[{target}]",
        "missing_wrapped": "No E[{user}]",
        "unwrap": "SM2 unwrap",
        "key": "Recovered content key K",
        "gcm": "SM4-GCM decrypt / auth",
        "plain": "Plaintext M",
        "force": "Wrong-key force try",
        "normal": "Normal receiver decrypt",
        "success": "success",
        "failed": "failed",
        "denied": "Non-recipient: this package has no wrapped key for the user",
        "fp": "fingerprint {value}",
        "auth_ok": "authentication passed",
        "auth_fail": "authentication failed",
        "not_reached": "not reached",
    },
}


@dataclass(frozen=True)
class ReceiverCanvasState:
    package_ready: bool = False
    mode: str | None = None
    user_id: str | None = None
    target_recipient_id: str | None = None
    status: str | None = None
    wrapped_key_fingerprint: str | None = None
    content_key_fingerprint: str | None = None
    gcm_authenticated: bool | None = None
    output_name: str | None = None


class ReceiverFlowCanvas(QWidget):
    """Visualize one real receiver/decryption result without exposing secrets."""

    def __init__(self, i18n: Translator | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.i18n = i18n or Translator()
        self._text = _TEXT[self.i18n.language]
        self.state = ReceiverCanvasState()
        self.setMinimumHeight(260)
        self.setObjectName("receiverFlowCanvas")
        self.setToolTip(self._text["idle"])

    def clear(self, *, package_ready: bool = False) -> None:
        self.state = ReceiverCanvasState(package_ready=package_ready)
        self.update()

    def set_package_ready(self, ready: bool) -> None:
        if not ready:
            self.clear(package_ready=False)
            return
        if not self.state.package_ready:
            self.state = ReceiverCanvasState(package_ready=True)
            self.update()

    def show_result(
        self,
        result: DecryptResult,
        *,
        mode: str,
        user_id: str,
        target_recipient_id: str | None = None,
    ) -> None:
        if mode not in {"normal", "force"}:
            raise ValueError("mode must be 'normal' or 'force'")
        trace = result.trace
        self.state = ReceiverCanvasState(
            package_ready=True,
            mode=mode,
            user_id=user_id,
            target_recipient_id=target_recipient_id or trace.target_recipient_id or user_id,
            status=result.status.value,
            wrapped_key_fingerprint=trace.wrapped_key_fingerprint,
            content_key_fingerprint=trace.content_key_fingerprint,
            gcm_authenticated=trace.gcm_authenticated,
            output_name=result.output_path.name if result.output_path else None,
        )
        self.update()

    def _colors(self) -> tuple[QColor, QColor, QColor, QColor]:
        return (
            QColor("#FFFFFF"),
            QColor("#EAF7F0"),
            QColor("#FFF4E8"),
            QColor("#FDEEEE"),
        )

    def _draw_node(
        self,
        painter: QPainter,
        rect: QRectF,
        title: str,
        subtitle: str = "",
        *,
        state: str = "idle",
    ) -> None:
        idle, success, warning, failure = self._colors()
        fill = {
            "idle": idle,
            "success": success,
            "warning": warning,
            "failure": failure,
        }.get(state, idle)
        border = {
            "idle": QColor("#B8C7DA"),
            "success": QColor("#68B187"),
            "warning": QColor("#D99A42"),
            "failure": QColor("#D96B6B"),
        }.get(state, QColor("#B8C7DA"))
        painter.setPen(QPen(border, 1.5))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 9, 9)
        painter.setPen(QColor("#17304F"))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect.adjusted(10, 7, -8, -rect.height() / 2 + 2), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        if subtitle:
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor("#60738D"))
            painter.drawText(rect.adjusted(10, rect.height() / 2 - 4, -8, -6), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, subtitle)

    def _draw_arrow(self, painter: QPainter, a: QRectF, b: QRectF, *, ok: bool | None) -> None:
        if ok is True:
            color = QColor("#68B187")
            style = Qt.PenStyle.SolidLine
            width = 2.0
        elif ok is False:
            color = QColor("#D96B6B")
            style = Qt.PenStyle.SolidLine
            width = 2.0
        else:
            color = QColor("#C3CEDC")
            style = Qt.PenStyle.DashLine
            width = 1.4
        painter.setPen(QPen(color, width, style))
        start = a.center()
        end = b.center()
        start.setX(a.right())
        end.setX(b.left())
        painter.drawLine(start, end)
        painter.drawLine(end, end + self._point(-7, -4))
        painter.drawLine(end, end + self._point(-7, 4))

    @staticmethod
    def _point(x: float, y: float):
        from PySide6.QtCore import QPointF

        return QPointF(x, y)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#FBFCFE"))

        margin = 18.0
        width = max(680.0, float(self.width()) - margin * 2)
        y = 70.0
        node_w = min(180.0, (width - 80.0) / 5.0)
        gap = (width - node_w * 5.0) / 4.0
        rects = [QRectF(margin + i * (node_w + gap), y, node_w, 72.0) for i in range(5)]

        if not self.state.package_ready or not self.state.mode:
            painter.setPen(QColor("#71809A"))
            painter.drawText(QRectF(margin, 20, width, 36), Qt.AlignmentFlag.AlignCenter, self._text["idle"])
            labels = ["SK[i]", "E[i]", "SM2", "K", "SM4-GCM → M"]
            for rect, label in zip(rects, labels):
                self._draw_node(painter, rect, label)
            for a, b in zip(rects, rects[1:]):
                self._draw_arrow(painter, a, b, ok=None)
            return

        s = self.state
        user = s.user_id or "?"
        target = s.target_recipient_id or user
        mode_title = self._text["force"] if s.mode == "force" else self._text["normal"]
        painter.setPen(QColor("#52647E"))
        painter.drawText(QRectF(margin, 18, width, 34), Qt.AlignmentFlag.AlignCenter, mode_title)

        status = DecryptStatus(s.status) if s.status else None
        not_recipient = status == DecryptStatus.NOT_RECIPIENT
        unwrap_failed = status in {
            DecryptStatus.SM2_UNWRAP_FAILED,
            DecryptStatus.PRIVATE_KEY_LOAD_FAILED,
            DecryptStatus.ENVELOPE_MISMATCH,
        }
        success = status == DecryptStatus.SUCCESS
        gcm_failed = status == DecryptStatus.GCM_AUTH_FAILED

        self._draw_node(painter, rects[0], self._text["sk"].format(user=user), state="failure" if unwrap_failed else "success")

        if not_recipient:
            self._draw_node(painter, rects[1], self._text["missing_wrapped"].format(user=user), self._text["denied"], state="failure")
            self._draw_arrow(painter, rects[0], rects[1], ok=False)
            for rect, label in zip(rects[2:], [self._text["unwrap"], self._text["key"], self._text["gcm"]]):
                self._draw_node(painter, rect, label, self._text["not_reached"])
            return

        wrapped_sub = self._text["fp"].format(value=s.wrapped_key_fingerprint) if s.wrapped_key_fingerprint else ""
        self._draw_node(painter, rects[1], self._text["wrapped"].format(target=target), wrapped_sub, state="success" if s.wrapped_key_fingerprint else "idle")
        self._draw_arrow(painter, rects[0], rects[1], ok=True if s.wrapped_key_fingerprint else None)

        unwrap_ok = s.content_key_fingerprint is not None
        self._draw_node(
            painter,
            rects[2],
            self._text["unwrap"],
            self._text["success"] if unwrap_ok else self._text["failed"] if unwrap_failed else self._text["not_reached"],
            state="success" if unwrap_ok else "failure" if unwrap_failed else "idle",
        )
        self._draw_arrow(painter, rects[1], rects[2], ok=True if unwrap_ok else False if unwrap_failed else None)

        key_sub = self._text["fp"].format(value=s.content_key_fingerprint) if s.content_key_fingerprint else self._text["not_reached"]
        self._draw_node(painter, rects[3], self._text["key"], key_sub, state="success" if unwrap_ok else "idle")
        self._draw_arrow(painter, rects[2], rects[3], ok=True if unwrap_ok else None)

        if success:
            gcm_sub = self._text["auth_ok"] + (f" · {s.output_name}" if s.output_name else "")
            gcm_state = "success"
            gcm_edge: bool | None = True
        elif gcm_failed:
            gcm_sub = self._text["auth_fail"]
            gcm_state = "failure"
            gcm_edge = False
        else:
            gcm_sub = self._text["not_reached"]
            gcm_state = "idle"
            gcm_edge = None
        self._draw_node(painter, rects[4], self._text["gcm"] + " → " + self._text["plain"], gcm_sub, state=gcm_state)
        self._draw_arrow(painter, rects[3], rects[4], ok=gcm_edge)
