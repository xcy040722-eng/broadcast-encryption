"""PySide6 workbench backed by the real InteractiveSession.

The UI is Chinese-first by default, with an English fallback. Every cryptographic
action still delegates to InteractiveSession; this module contains no duplicate
cryptographic implementation.
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.sm2_sm4_mre.interactive_session import InteractiveSession, SessionStage
from src.sm2_sm4_mre.types import DecryptResult

from .i18n import DEFAULT_LANGUAGE, Translator
from .relation_canvas import CryptoRelationCanvas
from .widgets import (
    ContentKeyCard,
    FlowStrip,
    PackageCard,
    Sm4EngineCard,
    UserCard,
    WrappedKeyChip,
)


T = TypeVar("T")
DEFAULT_USERS = ("u1", "u2", "u3", "u4")


LIGHT_STYLE = """
QMainWindow, QWidget {
    background: #F4F7FB;
    color: #172033;
    font-size: 13px;
}
QFrame#panel, QFrame#userCard, QFrame#contentKeyCard, QFrame#engineCard,
QFrame#packageCard, QFrame#wrappedChip, QFrame#flowStrip {
    background: #FFFFFF;
    border: 1px solid #DCE4EE;
    border-radius: 10px;
}
QFrame#userCard { min-width: 205px; }
QWidget#cryptoRelationCanvas {
    background: #FBFCFE;
    border: 1px solid #D8E2EF;
    border-radius: 10px;
}
QLabel#userTitle, QLabel#objectTitle {
    font-size: 15px;
    font-weight: 650;
    color: #14213A;
}
QLabel#muted { color: #71809A; }
QLabel#stageBadge {
    background: #EAF2FF;
    color: #215AA5;
    border: 1px solid #B7CEF1;
    border-radius: 11px;
    padding: 5px 10px;
    font-weight: 650;
}
QLabel#flowStep {
    background: #F4F6F9;
    color: #78869A;
    border: 1px solid #E0E6EF;
    border-radius: 7px;
    padding: 7px 5px;
}
QLabel#flowStep[done="true"] {
    background: #EEF7F2;
    color: #317052;
    border-color: #C6E3D2;
}
QLabel#flowStep[active="true"] {
    background: #EAF2FF;
    color: #174F98;
    border: 1px solid #8EB4E8;
    font-weight: 650;
}
QLabel#dropTarget {
    border: 1px dashed #9CB0CA;
    border-radius: 8px;
    color: #52647E;
    background: #F8FAFD;
    padding: 7px;
}
QPushButton {
    background: #FFFFFF;
    border: 1px solid #C7D2E1;
    border-radius: 7px;
    padding: 7px 11px;
}
QPushButton:hover { background: #EEF4FC; border-color: #9BB7DC; }
QPushButton:disabled { color: #A8B3C3; background: #F6F8FA; }
QPushButton#primary {
    background: #E8F1FF;
    border-color: #87ADE1;
    color: #205B9F;
    font-weight: 600;
}
QPlainTextEdit {
    background: #FFFFFF;
    border: 1px solid #DCE4EE;
    border-radius: 8px;
    padding: 4px;
}
QComboBox {
    background: #FFFFFF;
    border: 1px solid #C7D2E1;
    border-radius: 6px;
    padding: 5px;
}
QTabWidget::pane {
    background: #FFFFFF;
    border: 1px solid #DCE4EE;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: #F1F4F8;
    color: #6A7890;
    border: 1px solid #DCE4EE;
    border-bottom: none;
    padding: 7px 14px;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background: #FFFFFF;
    color: #1F568F;
    font-weight: 600;
}
QLabel#statusBar {
    background: #EDF3FA;
    border: 1px solid #D9E3F0;
    border-radius: 7px;
    padding: 7px 10px;
    color: #52647E;
}
"""


class WorkbenchWindow(QMainWindow):
    """Interactive teaching UI for the validated SM2 + SM4 backend."""

    def __init__(
        self,
        *,
        session: InteractiveSession | None = None,
        workspace: Path | None = None,
        user_ids: tuple[str, ...] = DEFAULT_USERS,
        language: str = DEFAULT_LANGUAGE,
    ) -> None:
        super().__init__()
        if session is None:
            root = workspace or (Path.home() / ".sm2-sm4-workbench")
            session = InteractiveSession(root)
        self.session = session
        self.user_ids = user_ids
        self.i18n = Translator(language)
        self._passwords: dict[str, str] = {}

        self.setWindowTitle(self.i18n("window_title"))
        self.resize(1440, 860)
        self.setStyleSheet(LIGHT_STYLE)

        self.user_cards: dict[str, UserCard] = {}
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------
    def generate_user(self, user_id: str, password: str) -> None:
        self.session.generate_user_key(user_id, password)
        self._passwords[user_id] = password
        self._set_status(self.i18n("status_key_generated", user_id=user_id))
        self.refresh()

    def set_media_path(self, path: Path) -> None:
        self.session.set_media(Path(path))
        self._set_status(self.i18n("status_media_selected", name=Path(path).name))
        self.refresh()

    def set_recipient(self, user_id: str, selected: bool) -> None:
        self.session.select_recipient(user_id, selected)
        key = "status_recipient_selected" if selected else "status_recipient_removed"
        self._set_status(self.i18n(key, user_id=user_id))
        self.refresh()

    def generate_material(self) -> None:
        snap = self.session.generate_content_material()
        self._set_status(
            self.i18n(
                "status_material_generated",
                fingerprint=str(snap.content_key_fingerprint),
            )
        )
        self.refresh()

    def wrap_for_user(self, user_id: str) -> bytes:
        wrapped = self.session.wrap_for(user_id)
        self._set_status(self.i18n("status_wrapped", user_id=user_id))
        self.refresh()
        return wrapped

    def encrypt_payload(self) -> Path:
        path = self.session.encrypt_payload()
        self._set_status(self.i18n("status_payload_encrypted"))
        self.refresh()
        return path

    def assemble_to(self, output_path: Path) -> Path:
        path = self.session.assemble_package(Path(output_path))
        self._set_status(self.i18n("status_package_assembled", name=path.name))
        self.receiver_result.setText(self.i18n("receiver_ready"))
        self.refresh()
        return path

    def decrypt_user(self, user_id: str, password: str, output_path: Path) -> DecryptResult:
        result = self.session.decrypt_as(user_id, password, Path(output_path))
        self._set_status(
            self.i18n(
                "status_receiver",
                user_id=user_id,
                status=result.status.value,
                message=result.message,
            )
        )
        self.receiver_result.setText(f"{result.status.value}\n{result.message}")
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
            self.i18n(
                "status_force",
                attacker=attacker_user_id,
                target=target_recipient_id,
                status=result.status.value,
            )
        )
        self.receiver_result.setText(f"{result.status.value}\n{result.message}")
        self.refresh()
        return result

    def reset_broadcast(self, *, keep_media: bool = True) -> None:
        self.session.reset_broadcast(keep_media=keep_media)
        self.receiver_result.setText(self.i18n("receiver_wait"))
        self._set_status(self.i18n("status_reset"))
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
        title = QLabel(self.i18n("header_title"))
        title.setStyleSheet("font-size: 21px; font-weight: 700;")
        subtitle = QLabel(self.i18n("header_subtitle"))
        subtitle.setObjectName("muted")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch(1)
        self.stage_label = QLabel()
        self.stage_label.setObjectName("stageBadge")
        header.addWidget(self.stage_label)
        reset = QPushButton(self.i18n("reset_broadcast"))
        reset.clicked.connect(lambda: self._safe(lambda: self.reset_broadcast(keep_media=True)))
        header.addWidget(reset)
        root.addLayout(header)

        self.flow_strip = FlowStrip(self.i18n)
        root.addWidget(self.flow_strip)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_users_panel())
        splitter.addWidget(self._build_workspace_panel())
        splitter.addWidget(self._build_receiver_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([270, 820, 310])
        root.addWidget(splitter, 1)

        self.status_label = QLabel(self.i18n("status_ready"))
        self.status_label.setObjectName("statusBar")
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
        title = QLabel(self.i18n("panel_users"))
        title.setObjectName("objectTitle")
        explainer = QLabel(self.i18n("panel_users_help"))
        explainer.setWordWrap(True)
        explainer.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(explainer)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(8)

        for user_id in self.user_ids:
            card = UserCard(user_id, self.i18n)
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
        title = QLabel(self.i18n("panel_workspace"))
        title.setObjectName("objectTitle")
        layout.addWidget(title)

        media_row = QHBoxLayout()
        self.media_label = QLabel(self.i18n("no_media"))
        self.media_label.setObjectName("muted")
        self.media_label.setWordWrap(True)
        choose_media = QPushButton(self.i18n("choose_media"))
        choose_media.clicked.connect(self._choose_media)
        self.choose_media_button = choose_media
        media_row.addWidget(self.media_label, 1)
        media_row.addWidget(choose_media)
        layout.addLayout(media_row)

        material_row = QHBoxLayout()
        self.content_key = ContentKeyCard(self.i18n)
        self.generate_material_button = QPushButton(self.i18n("generate_material"))
        self.generate_material_button.setObjectName("primary")
        self.generate_material_button.clicked.connect(
            lambda: self._safe(self.generate_material)
        )
        material_row.addWidget(self.content_key, 1)
        material_row.addWidget(self.generate_material_button)
        layout.addLayout(material_row)

        # v0.2.1: the main workspace is now an object relationship canvas rather
        # than a vertical form.  It is still direct manipulation: the K node is
        # draggable and its drop targets emit real InteractiveSession actions.
        self.workspace_tabs = QTabWidget()
        graph_tab = QWidget()
        graph_layout = QVBoxLayout(graph_tab)
        graph_layout.setContentsMargins(8, 8, 8, 8)
        graph_layout.setSpacing(8)

        graph_title = QLabel(
            "密码学对象关系图" if self.i18n.language == "zh_CN" else "Cryptographic object graph"
        )
        graph_title.setObjectName("objectTitle")
        graph_layout.addWidget(graph_title)

        self.relation_canvas = CryptoRelationCanvas(self.i18n)
        self.relation_canvas.wrapRequested.connect(
            lambda uid: self._safe(lambda: self.wrap_for_user(uid))
        )
        self.relation_canvas.encryptRequested.connect(
            lambda: self._safe(self.encrypt_payload)
        )
        graph_layout.addWidget(self.relation_canvas, 1)

        self.package_card = PackageCard(self.i18n)
        self.package_card.assembleRequested.connect(self._choose_package_output)
        graph_layout.addWidget(self.package_card)

        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        details_layout.setContentsMargins(8, 8, 8, 8)
        details_layout.setSpacing(7)

        self.engine = Sm4EngineCard(self.i18n)
        self.engine.encryptRequested.connect(lambda: self._safe(self.encrypt_payload))
        details_layout.addWidget(self.engine)

        wrapped_title = QLabel(self.i18n("wrapped_keys"))
        wrapped_title.setObjectName("objectTitle")
        details_layout.addWidget(wrapped_title)
        self.wrapped_container = QWidget()
        self.wrapped_layout = QVBoxLayout(self.wrapped_container)
        self.wrapped_layout.setContentsMargins(0, 0, 0, 0)
        self.wrapped_layout.setSpacing(5)
        details_layout.addWidget(self.wrapped_container)

        events_title = QLabel(self.i18n("session_events"))
        events_title.setObjectName("objectTitle")
        self.event_log = QPlainTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMaximumBlockCount(200)
        details_layout.addWidget(events_title)
        details_layout.addWidget(self.event_log, 1)

        graph_tab_text = "关系图" if self.i18n.language == "zh_CN" else "Object graph"
        details_tab_text = "对象细节 / 日志" if self.i18n.language == "zh_CN" else "Details / log"
        self.workspace_tabs.addTab(graph_tab, graph_tab_text)
        self.workspace_tabs.addTab(details_tab, details_tab_text)
        layout.addWidget(self.workspace_tabs, 1)
        return panel

    def _build_receiver_panel(self) -> QWidget:
        panel, layout = self._panel()
        title = QLabel(self.i18n("panel_receiver"))
        title.setObjectName("objectTitle")
        info = QLabel(self.i18n("panel_receiver_help"))
        info.setWordWrap(True)
        info.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(info)

        layout.addWidget(QLabel(self.i18n("act_as_user")))
        self.receiver_user = QComboBox()
        self.receiver_user.addItems(self.user_ids)
        layout.addWidget(self.receiver_user)

        self.decrypt_button = QPushButton(self.i18n("decrypt_selected"))
        self.decrypt_button.clicked.connect(self._receiver_decrypt_dialog)
        layout.addWidget(self.decrypt_button)

        layout.addWidget(QLabel(self.i18n("force_target")))
        self.force_target = QComboBox()
        layout.addWidget(self.force_target)
        self.force_button = QPushButton(self.i18n("force_try"))
        self.force_button.clicked.connect(self._receiver_force_dialog)
        layout.addWidget(self.force_button)

        self.receiver_result = QLabel(self.i18n("receiver_wait"))
        self.receiver_result.setWordWrap(True)
        self.receiver_result.setObjectName("muted")
        layout.addWidget(self.receiver_result)
        layout.addStretch(1)
        return panel

    # ------------------------------------------------------------------
    # Dialog handlers
    # ------------------------------------------------------------------
    def _prompt_generate_user(self, user_id: str) -> None:
        password, ok = QInputDialog.getText(
            self,
            self.i18n("dialog_generate_title", user_id=user_id),
            self.i18n("dialog_private_password"),
            QLineEdit.EchoMode.Password,
        )
        if ok and password:
            self._safe(lambda: self.generate_user(user_id, password))

    def _recipient_changed(self, user_id: str, selected: bool) -> None:
        self._safe(lambda: self.set_recipient(user_id, selected))

    def _choose_media(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, self.i18n("dialog_choose_media"))
        if filename:
            self._safe(lambda: self.set_media_path(Path(filename)))

    def _choose_package_output(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.i18n("dialog_save_package"),
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
            self.i18n("dialog_password_title", user_id=user_id),
            self.i18n("dialog_password"),
            QLineEdit.EchoMode.Password,
        )
        return password if ok and password else None

    def _receiver_decrypt_dialog(self) -> None:
        user_id = self.receiver_user.currentText()
        password = self._password_for(user_id)
        if not password:
            return
        suggested = f"recovered-{user_id}.bin"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.i18n("dialog_save_plaintext"),
            suggested,
        )
        if not filename:
            return
        self._safe(lambda: self.decrypt_user(user_id, password, Path(filename)))

    def _receiver_force_dialog(self) -> None:
        attacker = self.receiver_user.currentText()
        target = self.force_target.currentText()
        if not target:
            self._set_status(self.i18n("status_no_force_target"))
            return
        password = self._password_for(attacker)
        if not password:
            return
        suggested = f"force-{attacker}-to-{target}.bin"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.i18n("dialog_force_output"),
            suggested,
        )
        if not filename:
            return
        self._safe(
            lambda: self.force_try_user(attacker, password, target, Path(filename))
        )

    # ------------------------------------------------------------------
    # View synchronization
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        snap = self.session.snapshot()
        self.stage_label.setText(
            self.i18n("stage", value=self.i18n.stage(snap.stage.value))
        )
        self.flow_strip.update_stage(snap.stage.value)
        locked = snap.package_id is not None

        for user_id, card in self.user_cards.items():
            card.update_state(
                has_key=user_id in snap.users,
                selected=user_id in snap.recipients,
                wrapped=user_id in snap.wrapped_key_fingerprints,
                locked=locked,
            )

        media_name: str | None = None
        if snap.input_path:
            path = Path(snap.input_path)
            media_name = path.name
            try:
                size = path.stat().st_size
                self.media_label.setText(f"{path.name}\n{size:,} bytes")
            except OSError:
                self.media_label.setText(path.name)
        else:
            self.media_label.setText(self.i18n("no_media"))
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
        self.relation_canvas.update_state(
            recipients=tuple(snap.recipients),
            wrapped=tuple(sorted(snap.wrapped_key_fingerprints)),
            content_key_fingerprint=snap.content_key_fingerprint,
            media_name=media_name,
            payload_ready=snap.payload_path is not None,
            package_ready=snap.stage == SessionStage.READY_TO_ASSEMBLE,
            package_assembled=snap.package_path is not None,
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
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        if not items:
            label = QLabel(self.i18n("wrapped_none"))
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
