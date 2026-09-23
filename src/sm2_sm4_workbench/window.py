"""Functional PySide6 workbench backed by the real InteractiveSession.

Version 0.1 intentionally prioritizes interaction correctness over visual polish.
Every crypto action on screen delegates to InteractiveSession; this module does
not implement or duplicate cryptographic operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.sm2_sm4_mre.interactive_session import InteractiveSession, SessionStage
from src.sm2_sm4_mre.types import DecryptResult

from .widgets import ContentKeyCard, PackageCard, Sm4EngineCard, UserCard, WrappedKeyChip


T = TypeVar("T")
DEFAULT_USERS = ("u1", "u2", "u3", "u4")


LIGHT_STYLE = """
QMainWindow, QWidget { background: #F4F6FA; color: #182234; font-size: 13px; }
QFrame#panel, QFrame#userCard, QFrame#contentKeyCard, QFrame#engineCard,
QFrame#packageCard, QFrame#wrappedChip {
    background: white; border: 1px solid #DCE3EC; border-radius: 9px;
}
QFrame#userCard { min-width: 205px; }
QLabel#userTitle, QLabel#objectTitle { font-size: 15px; font-weight: 600; }
QLabel#muted { color: #728096; }
QLabel#dropTarget {
    border: 1px dashed #A9B4C4; border-radius: 7px; color: #59677D;
    background: #F8FAFD; padding: 6px;
}
QPushButton {
    background: white; border: 1px solid #C7D1DE; border-radius: 6px;
    padding: 7px 10px;
}
QPushButton:hover { background: #EEF3F9; }
QPushButton:disabled { color: #A9B4C4; background: #F7F8FA; }
QPushButton#primary { background: #EAF1FB; border-color: #8EAFE0; color: #285A9D; }
QPlainTextEdit { background: #FFFFFF; border: 1px solid #DCE3EC; border-radius: 7px; }
QComboBox { background: white; border: 1px solid #C7D1DE; border-radius: 5px; padding: 5px; }
"""


class WorkbenchWindow(QMainWindow):
    """First functional UI prototype for the SM2 + SM4 teaching system."""

    def __init__(
        self,
        *,
        session: InteractiveSession | None = None,
        workspace: Path | None = None,
        user_ids: tuple[str, ...] = DEFAULT_USERS,
    ) -> None:
        super().__init__()
        if session is None:
            root = workspace or (Path.home() / ".sm2-sm4-workbench")
            session = InteractiveSession(root)
        self.session = session
        self.user_ids = user_ids
        self._passwords: dict[str, str] = {}

        self.setWindowTitle("SM2 + SM4 Interactive Cryptography Workbench")
        self.resize(1360, 820)
        self.setStyleSheet(LIGHT_STYLE)

        self.user_cards: dict[str, UserCard] = {}
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # Public action methods. Tests and future controllers can call these
    # without dialogs; button/drop handlers call the same methods.
    # ------------------------------------------------------------------
    def generate_user(self, user_id: str, password: str) -> None:
        self.session.generate_user_key(user_id, password)
        self._passwords[user_id] = password
        self._set_status(f"Generated real SM2 key pair for {user_id}")
        self.refresh()

    def set_media_path(self, path: Path) -> None:
        self.session.set_media(Path(path))
        self._set_status(f"Selected media: {Path(path).name}")
        self.refresh()

    def set_recipient(self, user_id: str, selected: bool) -> None:
        self.session.select_recipient(user_id, selected)
        self._set_status(f"{user_id}: {'recipient selected' if selected else 'recipient removed'}")
        self.refresh()

    def generate_material(self) -> None:
        snap = self.session.generate_content_material()
        self._set_status(
            "Generated one real SM4 content key · fingerprint "
            + str(snap.content_key_fingerprint)
        )
        self.refresh()

    def wrap_for_user(self, user_id: str) -> bytes:
        wrapped = self.session.wrap_for(user_id)
        self._set_status(f"SM2 wrapped the session content key for {user_id}")
        self.refresh()
        return wrapped

    def encrypt_payload(self) -> Path:
        path = self.session.encrypt_payload()
        self._set_status("SM4-GCM encrypted the media exactly once")
        self.refresh()
        return path

    def assemble_to(self, output_path: Path) -> Path:
        path = self.session.assemble_package(Path(output_path))
        self._set_status(f"Assembled broadcast package: {path.name}")
        self.refresh()
        return path

    def decrypt_user(self, user_id: str, password: str, output_path: Path) -> DecryptResult:
        result = self.session.decrypt_as(user_id, password, Path(output_path))
        self._set_status(f"{user_id}: {result.status.value} · {result.message}")
        self.refresh()
        return result

    def force_try_user(
        self,
        attacker_user_id: str,
        password: str,
        target_recipient_id: str,
        output_path: Path,
    ) -> DecryptResult:
        result = self.session.force_try(
            attacker_user_id=attacker_user_id,
            password=password,
            target_recipient_id=target_recipient_id,
            output_path=Path(output_path),
        )
        self._set_status(
            f"Force try {attacker_user_id} → {target_recipient_id}: {result.status.value}"
        )
        self.refresh()
        return result

    def reset_broadcast(self, *, keep_media: bool = True) -> None:
        self.session.reset_broadcast(keep_media=keep_media)
        self._set_status("Broadcast reset; SM2 user keys preserved")
        self.refresh()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("SM2 + SM4 Multi-Recipient Workbench")
        title.setStyleSheet("font-size: 20px; font-weight: 650;")
        subtitle = QLabel("Direct manipulation → InteractiveSession → real GmSSL")
        subtitle.setObjectName("muted")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch(1)
        self.stage_label = QLabel()
        self.stage_label.setStyleSheet("font-weight: 600;")
        header.addWidget(self.stage_label)
        reset = QPushButton("Reset broadcast")
        reset.clicked.connect(lambda: self._safe(lambda: self.reset_broadcast(keep_media=True)))
        header.addWidget(reset)
        root.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_users_panel())
        splitter.addWidget(self._build_workspace_panel())
        splitter.addWidget(self._build_receiver_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([260, 760, 300])
        root.addWidget(splitter, 1)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("muted")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        self.setCentralWidget(central)

    def _panel(self) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)
        return frame, layout

    def _build_users_panel(self) -> QWidget:
        panel, layout = self._panel()
        title = QLabel("Users / recipient set S")
        title.setObjectName("objectTitle")
        explainer = QLabel("Generate real SM2 keys, then choose recipients before generating K.")
        explainer.setWordWrap(True)
        explainer.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(explainer)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(8)

        for user_id in self.user_ids:
            card = UserCard(user_id)
            card.generateRequested.connect(self._prompt_generate_user)
            card.recipientChanged.connect(self._recipient_changed)
            card.wrapRequested.connect(
                lambda uid, _self=self: _self._safe(lambda: _self.wrap_for_user(uid))
            )
            self.user_cards[user_id] = card
            inner_layout.addWidget(card)
        inner_layout.addStretch(1)
        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)
        return panel

    def _build_workspace_panel(self) -> QWidget:
        panel, layout = self._panel()
        title = QLabel("Workspace")
        title.setObjectName("objectTitle")
        layout.addWidget(title)

        media_row = QHBoxLayout()
        self.media_label = QLabel("No media selected")
        self.media_label.setObjectName("muted")
        self.media_label.setWordWrap(True)
        choose_media = QPushButton("Choose media…")
        choose_media.clicked.connect(self._choose_media)
        self.choose_media_button = choose_media
        media_row.addWidget(self.media_label, 1)
        media_row.addWidget(choose_media)
        layout.addLayout(media_row)

        material_row = QHBoxLayout()
        self.content_key = ContentKeyCard()
        self.generate_material_button = QPushButton("Generate content material")
        self.generate_material_button.setObjectName("primary")
        self.generate_material_button.clicked.connect(
            lambda: self._safe(self.generate_material)
        )
        material_row.addWidget(self.content_key, 1)
        material_row.addWidget(self.generate_material_button)
        layout.addLayout(material_row)

        self.engine = Sm4EngineCard()
        self.engine.encryptRequested.connect(lambda: self._safe(self.encrypt_payload))
        layout.addWidget(self.engine)

        wrapped_title = QLabel("Wrapped keys")
        wrapped_title.setObjectName("objectTitle")
        layout.addWidget(wrapped_title)
        self.wrapped_container = QWidget()
        self.wrapped_layout = QVBoxLayout(self.wrapped_container)
        self.wrapped_layout.setContentsMargins(0, 0, 0, 0)
        self.wrapped_layout.setSpacing(5)
        layout.addWidget(self.wrapped_container)

        self.package_card = PackageCard()
        self.package_card.assembleRequested.connect(self._choose_package_output)
        layout.addWidget(self.package_card)

        events_title = QLabel("Session events")
        events_title.setObjectName("objectTitle")
        self.event_log = QPlainTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMaximumBlockCount(200)
        layout.addWidget(events_title)
        layout.addWidget(self.event_log, 1)
        return panel

    def _build_receiver_panel(self) -> QWidget:
        panel, layout = self._panel()
        title = QLabel("Receiver lab")
        title.setObjectName("objectTitle")
        info = QLabel(
            "After package assembly, try an authorized user, a non-recipient, or force a wrong SM2 key onto another user's wrapped key."
        )
        info.setWordWrap(True)
        info.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(info)

        layout.addWidget(QLabel("Act as user"))
        self.receiver_user = QComboBox()
        self.receiver_user.addItems(self.user_ids)
        layout.addWidget(self.receiver_user)

        self.decrypt_button = QPushButton("Decrypt as selected user")
        self.decrypt_button.clicked.connect(self._receiver_decrypt_dialog)
        layout.addWidget(self.decrypt_button)

        layout.addWidget(QLabel("Force target wrapped key"))
        self.force_target = QComboBox()
        layout.addWidget(self.force_target)
        self.force_button = QPushButton("Force try wrong private key")
        self.force_button.clicked.connect(self._receiver_force_dialog)
        layout.addWidget(self.force_button)

        self.receiver_result = QLabel("Assemble a package first")
        self.receiver_result.setWordWrap(True)
        self.receiver_result.setObjectName("muted")
        layout.addWidget(self.receiver_result)
        layout.addStretch(1)
        return panel

    # ------------------------------------------------------------------
    # Dialog/UI handlers
    # ------------------------------------------------------------------
    def _prompt_generate_user(self, user_id: str) -> None:
        password, ok = QInputDialog.getText(
            self,
            f"Generate SM2 key for {user_id}",
            "Private-key password:",
            QLineEdit.EchoMode.Password,
        )
        if ok and password:
            self._safe(lambda: self.generate_user(user_id, password))

    def _recipient_changed(self, user_id: str, selected: bool) -> None:
        self._safe(lambda: self.set_recipient(user_id, selected))

    def _choose_media(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Choose media/file")
        if filename:
            self._safe(lambda: self.set_media_path(Path(filename)))

    def _choose_package_output(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save broadcast package",
            "broadcast.smre",
            "SM2+SM4 package (*.smre)",
        )
        if filename:
            if not filename.lower().endswith(".smre"):
                filename += ".smre"
            self._safe(lambda: self.assemble_to(Path(filename)))

    def _password_for(self, user_id: str) -> str | None:
        if user_id in self._passwords:
            return self._passwords[user_id]
        password, ok = QInputDialog.getText(
            self,
            f"Private key password for {user_id}",
            "Password:",
            QLineEdit.EchoMode.Password,
        )
        return password if ok and password else None

    def _receiver_decrypt_dialog(self) -> None:
        user_id = self.receiver_user.currentText()
        password = self._password_for(user_id)
        if not password:
            return
        suggested = f"recovered-{user_id}.bin"
        filename, _ = QFileDialog.getSaveFileName(self, "Save recovered plaintext", suggested)
        if not filename:
            return

        def run() -> None:
            result = self.decrypt_user(user_id, password, Path(filename))
            self.receiver_result.setText(f"{result.status.value}\n{result.message}")

        self._safe(run)

    def _receiver_force_dialog(self) -> None:
        attacker = self.receiver_user.currentText()
        target = self.force_target.currentText()
        if not target:
            self._set_status("No wrapped-key target is available")
            return
        password = self._password_for(attacker)
        if not password:
            return
        suggested = f"force-{attacker}-to-{target}.bin"
        filename, _ = QFileDialog.getSaveFileName(self, "Forced-try output (should not survive)", suggested)
        if not filename:
            return

        def run() -> None:
            result = self.force_try_user(attacker, password, target, Path(filename))
            self.receiver_result.setText(f"{result.status.value}\n{result.message}")

        self._safe(run)

    # ------------------------------------------------------------------
    # View synchronization
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        snap = self.session.snapshot()
        self.stage_label.setText(f"Stage: {snap.stage.value}")
        locked = snap.package_id is not None

        for user_id, card in self.user_cards.items():
            card.update_state(
                has_key=user_id in snap.users,
                selected=user_id in snap.recipients,
                wrapped=user_id in snap.wrapped_key_fingerprints,
                locked=locked,
            )

        if snap.input_path:
            path = Path(snap.input_path)
            try:
                size = path.stat().st_size
                self.media_label.setText(f"{path.name}\n{size:,} bytes")
            except OSError:
                self.media_label.setText(path.name)
        else:
            self.media_label.setText("No media selected")
        self.choose_media_button.setEnabled(not locked)

        self.generate_material_button.setEnabled(
            snap.stage == SessionStage.READY_FOR_MATERIAL
        )
        self.content_key.update_state(snap.content_key_fingerprint)
        self.engine.update_state(
            enabled=snap.package_id is not None and snap.payload_path is None,
            done=snap.payload_path is not None,
            payload_size=snap.payload_size,
        )
        self._refresh_wrapped_keys(snap.wrapped_key_fingerprints)
        self.package_card.update_state(
            can_assemble=snap.stage == SessionStage.READY_TO_ASSEMBLE,
            package_path=snap.package_path,
        )

        package_ready = snap.package_path is not None
        self.decrypt_button.setEnabled(package_ready)
        self.force_button.setEnabled(package_ready and bool(snap.recipients))
        current_target = self.force_target.currentText()
        self.force_target.blockSignals(True)
        self.force_target.clear()
        self.force_target.addItems(list(snap.recipients))
        if current_target in snap.recipients:
            self.force_target.setCurrentText(current_target)
        self.force_target.blockSignals(False)

        self.event_log.setPlainText(
            "\n".join(
                f"[{event.stage}] {event.status}: {event.detail}"
                for event in self.session.events[-80:]
            )
        )
        cursor = self.event_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.event_log.setTextCursor(cursor)

    def _refresh_wrapped_keys(self, items: dict[str, str]) -> None:
        while self.wrapped_layout.count():
            item = self.wrapped_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not items:
            label = QLabel("None yet — drag the SM4 key onto a selected user")
            label.setObjectName("muted")
            self.wrapped_layout.addWidget(label)
            return
        for user_id, fp in sorted(items.items()):
            self.wrapped_layout.addWidget(WrappedKeyChip(user_id, fp))

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def _safe(self, action: Callable[[], T]) -> T | None:
        try:
            return action()
        except Exception as exc:
            self._set_status(f"{type(exc).__name__}: {exc}")
            self.refresh()
            return None
