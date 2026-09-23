"""Reusable widgets for the SM2 + SM4 interactive workbench.

The widgets contain no cryptographic implementation. They expose direct
manipulation signals that the window maps onto InteractiveSession actions.
"""

from __future__ import annotations

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .i18n import Translator


CONTENT_KEY_MIME = "application/x-sm2-sm4-content-key"


class FlowStrip(QFrame):
    """Compact visual summary of the six teaching stages."""

    _STAGE_INDEX = {
        "EMPTY": 0,
        "CONFIGURING": 0,
        "READY_FOR_MATERIAL": 1,
        "MATERIAL_READY": 1,
        "WRAPPING": 2,
        "PAYLOAD_ENCRYPTED": 3,
        "READY_TO_ASSEMBLE": 4,
        "PACKAGE_ASSEMBLED": 5,
    }

    def __init__(self, i18n: Translator | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.i18n = i18n or Translator()
        self.setObjectName("flowStrip")
        self._labels: list[QLabel] = []

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(6)
        for index in range(1, 7):
            label = QLabel(self.i18n(f"flow_{index}"))
            label.setObjectName("flowStep")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setProperty("active", False)
            label.setProperty("done", False)
            self._labels.append(label)
            row.addWidget(label, 1)

    def update_stage(self, stage_name: str) -> None:
        current = self._STAGE_INDEX.get(stage_name, 0)
        for index, label in enumerate(self._labels):
            label.setProperty("active", index == current)
            label.setProperty("done", index < current)
            style = label.style()
            style.unpolish(label)
            style.polish(label)
            label.update()


class UserCard(QFrame):
    """One user, their key-pair state, recipient state and SM2 wrap drop target."""

    generateRequested = Signal(str)
    recipientChanged = Signal(str, bool)
    wrapRequested = Signal(str)

    def __init__(
        self,
        user_id: str,
        i18n: Translator | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.i18n = i18n or Translator()
        self.user_id = user_id
        self._has_key = False
        self._wrapped = False
        self._locked = False
        self.setAcceptDrops(True)
        self.setObjectName("userCard")

        title = QLabel(user_id)
        title.setObjectName("userTitle")
        self.key_status = QLabel(self.i18n("user_key_not_generated"))
        self.key_status.setObjectName("muted")
        self.recipient = QCheckBox(self.i18n("recipient"))
        self.generate_button = QPushButton(self.i18n("generate_sm2_key"))
        self.drop_hint = QLabel(self.i18n("hint_generate_key"))
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_hint.setMinimumHeight(44)
        self.drop_hint.setWordWrap(True)
        self.drop_hint.setObjectName("dropTarget")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(7)
        layout.addWidget(title)
        layout.addWidget(self.key_status)
        layout.addWidget(self.recipient)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.drop_hint)

        self.generate_button.clicked.connect(lambda: self.generateRequested.emit(self.user_id))
        self.recipient.toggled.connect(
            lambda selected: self.recipientChanged.emit(self.user_id, selected)
        )

    def update_state(
        self,
        *,
        has_key: bool,
        selected: bool,
        wrapped: bool,
        locked: bool,
    ) -> None:
        self._has_key = has_key
        self._wrapped = wrapped
        self._locked = locked

        self.key_status.setText(
            self.i18n("user_key_ready") if has_key else self.i18n("user_key_not_generated")
        )
        self.generate_button.setEnabled(not has_key and not locked)
        self.recipient.blockSignals(True)
        self.recipient.setChecked(selected)
        self.recipient.blockSignals(False)
        self.recipient.setEnabled(has_key and not locked)

        if not has_key:
            hint = self.i18n("hint_generate_key")
        elif wrapped:
            hint = self.i18n("hint_wrapped_ready")
        elif selected and not locked:
            hint = self.i18n("hint_material_first")
        elif selected:
            hint = self.i18n("hint_drop_wrap")
        else:
            hint = self.i18n("hint_select_recipient")
        self.drop_hint.setText(hint)

    def _can_accept_content_key(self, event) -> bool:
        return (
            self._has_key
            and not self._wrapped
            and self.recipient.isChecked()
            and event.mimeData().hasFormat(CONTENT_KEY_MIME)
        )

    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self._can_accept_content_key(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self._can_accept_content_key(event):
            self.wrapRequested.emit(self.user_id)
            event.acceptProposedAction()
        else:
            event.ignore()


class ContentKeyCard(QFrame):
    """Draggable representation of the real session SM4 content key.

    Only the SM3 fingerprint is shown. The raw key never enters the widget.
    """

    def __init__(self, i18n: Translator | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.i18n = i18n or Translator()
        self.setObjectName("contentKeyCard")
        self._available = False
        self.title = QLabel(self.i18n("content_key_title"))
        self.title.setObjectName("objectTitle")
        self.fingerprint = QLabel(self.i18n("not_generated"))
        self.fingerprint.setObjectName("muted")
        self.hint = QLabel(self.i18n("content_key_wait"))
        self.hint.setWordWrap(True)
        self.hint.setObjectName("muted")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addWidget(self.title)
        layout.addWidget(self.fingerprint)
        layout.addWidget(self.hint)

    def update_state(self, fingerprint: str | None) -> None:
        self._available = fingerprint is not None
        self.fingerprint.setText(
            f"SM3 fp: {fingerprint}" if fingerprint else self.i18n("not_generated")
        )
        self.hint.setText(
            self.i18n("content_key_drag") if fingerprint else self.i18n("content_key_wait")
        )
        self.setCursor(
            Qt.CursorShape.OpenHandCursor if fingerprint else Qt.CursorShape.ArrowCursor
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API
        if self._available and event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData(CONTENT_KEY_MIME, b"session-content-key")
            drag.setMimeData(mime)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mousePressEvent(event)


class Sm4EngineCard(QFrame):
    """Drop target that triggers the real session.encrypt_payload() operation."""

    encryptRequested = Signal()

    def __init__(self, i18n: Translator | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.i18n = i18n or Translator()
        self.setAcceptDrops(True)
        self.setObjectName("engineCard")
        self._enabled = False
        self._done = False

        self.title = QLabel(self.i18n("engine_title"))
        self.title.setObjectName("objectTitle")
        self.status = QLabel(self.i18n("engine_wait"))
        self.status.setWordWrap(True)
        self.status.setObjectName("muted")
        self.drop_hint = QLabel(self.i18n("engine_drop"))
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_hint.setMinimumHeight(58)
        self.drop_hint.setObjectName("dropTarget")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addWidget(self.title)
        layout.addWidget(self.status)
        layout.addWidget(self.drop_hint)

    def update_state(self, *, enabled: bool, done: bool, payload_size: int | None) -> None:
        self._enabled = enabled
        self._done = done
        if done:
            self.status.setText(self.i18n("engine_payload_ready", size=payload_size or 0))
            self.drop_hint.setText(self.i18n("engine_done"))
        elif enabled:
            self.status.setText(self.i18n("engine_ready"))
            self.drop_hint.setText(self.i18n("engine_drop"))
        else:
            self.status.setText(self.i18n("engine_wait"))
            self.drop_hint.setText(self.i18n("engine_not_ready"))

    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt API
        if (
            self._enabled
            and not self._done
            and event.mimeData().hasFormat(CONTENT_KEY_MIME)
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.mimeData().hasFormat(CONTENT_KEY_MIME) and self._enabled and not self._done:
            self.encryptRequested.emit()
            event.acceptProposedAction()
        else:
            event.ignore()


class WrappedKeyChip(QFrame):
    def __init__(
        self,
        user_id: str,
        fingerprint: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("wrappedChip")
        row = QHBoxLayout(self)
        row.setContentsMargins(9, 6, 9, 6)
        row.addWidget(QLabel(f"E[{user_id}]"))
        fp = QLabel(fingerprint)
        fp.setObjectName("muted")
        row.addWidget(fp)
        row.addStretch(1)


class PackageCard(QFrame):
    assembleRequested = Signal()

    def __init__(self, i18n: Translator | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.i18n = i18n or Translator()
        self.setObjectName("packageCard")
        self.title = QLabel(self.i18n("package_title"))
        self.title.setObjectName("objectTitle")
        self.status = QLabel(self.i18n("package_not_assembled"))
        self.status.setObjectName("muted")
        self.button = QPushButton(self.i18n("package_assemble"))
        self.button.clicked.connect(self.assembleRequested)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addWidget(self.title)
        layout.addWidget(self.status)
        layout.addWidget(self.button)

    def update_state(self, *, can_assemble: bool, package_path: str | None) -> None:
        if package_path:
            self.status.setText(package_path)
            self.button.setText(self.i18n("package_assembled"))
            self.button.setEnabled(False)
        else:
            self.status.setText(
                self.i18n("package_ready") if can_assemble else self.i18n("package_needs")
            )
            self.button.setText(self.i18n("package_assemble"))
            self.button.setEnabled(can_assemble)
