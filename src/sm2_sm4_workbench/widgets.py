"""Small reusable widgets for the SM2 + SM4 functional workbench.

These widgets intentionally keep the first UI prototype simple.  Their job is
to map direct manipulation (select, drag, drop, click) onto real
InteractiveSession actions.  Visual polish comes later.
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


CONTENT_KEY_MIME = "application/x-sm2-sm4-content-key"


class UserCard(QFrame):
    """One user, their key-pair state, recipient state and SM2 wrap drop target."""

    generateRequested = Signal(str)
    recipientChanged = Signal(str, bool)
    wrapRequested = Signal(str)

    def __init__(self, user_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.user_id = user_id
        self._has_key = False
        self._wrapped = False
        self._locked = False
        self.setAcceptDrops(True)
        self.setObjectName("userCard")

        title = QLabel(user_id)
        title.setObjectName("userTitle")
        self.key_status = QLabel("SM2 key: not generated")
        self.key_status.setObjectName("muted")
        self.recipient = QCheckBox("Recipient")
        self.generate_button = QPushButton("Generate SM2 key")
        self.drop_hint = QLabel("Generate key first")
        self.drop_hint.setAlignment(Qt.AlignCenter)
        self.drop_hint.setMinimumHeight(44)
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

        self.key_status.setText("SM2 key: ready" if has_key else "SM2 key: not generated")
        self.generate_button.setEnabled(not has_key and not locked)
        self.recipient.blockSignals(True)
        self.recipient.setChecked(selected)
        self.recipient.blockSignals(False)
        self.recipient.setEnabled(has_key and not locked)

        if not has_key:
            hint = "Generate key first"
        elif wrapped:
            hint = "Wrapped key ready"
        elif selected and not locked:
            hint = "Generate content material first"
        elif selected:
            hint = "Drop SM4 key here → real SM2 wrap"
        else:
            hint = "Select as recipient"
        self.drop_hint.setText(hint)

    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt API
        if (
            self._has_key
            and not self._wrapped
            and self.recipient.isChecked()
            and event.mimeData().hasFormat(CONTENT_KEY_MIME)
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.mimeData().hasFormat(CONTENT_KEY_MIME):
            self.wrapRequested.emit(self.user_id)
            event.acceptProposedAction()
        else:
            event.ignore()


class ContentKeyCard(QFrame):
    """Draggable representation of the real session SM4 content key.

    Only the SM3 fingerprint is shown.  The raw key never enters the widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("contentKeyCard")
        self._available = False
        self.title = QLabel("SM4 content key")
        self.title.setObjectName("objectTitle")
        self.fingerprint = QLabel("not generated")
        self.fingerprint.setObjectName("muted")
        self.hint = QLabel("Select recipients + media, then generate material")
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
            f"SM3 fp: {fingerprint}" if fingerprint else "not generated"
        )
        self.hint.setText(
            "Drag this object to a selected user's public-key target, or to the SM4-GCM engine"
            if fingerprint
            else "Select recipients + media, then generate material"
        )
        self.setCursor(Qt.OpenHandCursor if fingerprint else Qt.ArrowCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API
        if self._available and event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData(CONTENT_KEY_MIME, b"session-content-key")
            drag.setMimeData(mime)
            self.setCursor(Qt.ClosedHandCursor)
            drag.exec(Qt.CopyAction)
            self.setCursor(Qt.OpenHandCursor)
        super().mousePressEvent(event)


class Sm4EngineCard(QFrame):
    """Drop target that triggers the real session.encrypt_payload() operation."""

    encryptRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("engineCard")
        self._enabled = False
        self._done = False

        self.title = QLabel("SM4-GCM engine")
        self.title.setObjectName("objectTitle")
        self.status = QLabel("Waiting for media + content key")
        self.status.setWordWrap(True)
        self.status.setObjectName("muted")
        self.drop_hint = QLabel("Drop SM4 key here")
        self.drop_hint.setAlignment(Qt.AlignCenter)
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
            self.status.setText(f"Encrypted payload ready · {payload_size or 0} bytes")
            self.drop_hint.setText("SM4-GCM complete")
        elif enabled:
            self.status.setText("Ready. The drop performs real SM4-GCM encryption.")
            self.drop_hint.setText("Drop SM4 key here")
        else:
            self.status.setText("Waiting for generated content material")
            self.drop_hint.setText("Not ready")

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
    def __init__(self, user_id: str, fingerprint: str, parent: QWidget | None = None) -> None:
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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("packageCard")
        self.title = QLabel("Broadcast package")
        self.title.setObjectName("objectTitle")
        self.status = QLabel("Not assembled")
        self.status.setObjectName("muted")
        self.button = QPushButton("Assemble .smre package")
        self.button.clicked.connect(self.assembleRequested)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addWidget(self.title)
        layout.addWidget(self.status)
        layout.addWidget(self.button)

    def update_state(self, *, can_assemble: bool, package_path: str | None) -> None:
        if package_path:
            self.status.setText(package_path)
            self.button.setText("Package assembled")
            self.button.setEnabled(False)
        else:
            self.status.setText(
                "Ready to assemble" if can_assemble else "Needs all wrapped keys + encrypted payload"
            )
            self.button.setText("Assemble .smre package")
            self.button.setEnabled(can_assemble)
