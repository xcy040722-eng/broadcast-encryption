"""Small reusable widgets for the Complete Subtree workbench."""

from __future__ import annotations

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from .i18n import Translator


CS_K_MIME = "application/x-complete-subtree-content-key"


class ContentKeyCard(QFrame):
    """Safe draggable projection of K; only the SM3 fingerprint is displayed."""

    def __init__(self, i18n: Translator):
        super().__init__()
        self.i18n = i18n
        self.setObjectName("contentKeyCard")
        self._drag_enabled = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        self.title = QLabel(self.i18n("content_key"))
        self.title.setObjectName("objectTitle")
        self.value = QLabel(self.i18n("not_generated"))
        self.value.setObjectName("muted")
        self.hint = QLabel(self.i18n("drag_hint"))
        self.hint.setObjectName("muted")
        self.hint.setWordWrap(True)
        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.hint)

    def set_state(self, fingerprint: str | None, *, draggable: bool) -> None:
        self._drag_enabled = bool(fingerprint) and draggable
        self.value.setText(
            self.i18n("fp", fp=fingerprint)
            if fingerprint
            else self.i18n("not_generated")
        )
        self.setCursor(
            Qt.CursorShape.OpenHandCursor
            if self._drag_enabled
            else Qt.CursorShape.ArrowCursor
        )

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._drag_enabled or not (event.buttons() & Qt.MouseButton.LeftButton):
            return super().mouseMoveEvent(event)
        mime = QMimeData()
        mime.setData(CS_K_MIME, b"K")
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)
