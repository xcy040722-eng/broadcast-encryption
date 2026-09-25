"""v0.2.2 receiver-visualization layer for the validated workbench.

This subclass deliberately reuses every existing WorkbenchWindow action.  It
adds one central tab that renders the *result* of the real backend receiver
attempt, without duplicating decryption logic or retaining raw secret material.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.sm2_sm4_mre.types import DecryptResult

from .receiver_canvas import ReceiverFlowCanvas
from .window import WorkbenchWindow


class ReceiverVisualWorkbenchWindow(WorkbenchWindow):
    """Workbench with an additional receiver/decryption relationship canvas."""

    def _build_workspace_panel(self) -> QWidget:
        panel = super()._build_workspace_panel()

        self.receiver_tab = QWidget()
        layout = QVBoxLayout(self.receiver_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title_text = (
            "接收端真实解密路径"
            if self.i18n.language == "zh_CN"
            else "Real receiver decryption path"
        )
        title = QLabel(title_text)
        title.setObjectName("objectTitle")
        layout.addWidget(title)

        help_text = (
            "在右侧执行授权解密、非接收者尝试或错误私钥强制尝试；这里显示真实后端实际走到哪一步。"
            if self.i18n.language == "zh_CN"
            else "Run an authorized decrypt, non-recipient attempt, or wrong-key force try on the right; this graph shows how far the real backend actually progressed."
        )
        help_label = QLabel(help_text)
        help_label.setObjectName("muted")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        self.receiver_flow = ReceiverFlowCanvas(self.i18n)
        layout.addWidget(self.receiver_flow, 1)

        tab_text = "接收端路径" if self.i18n.language == "zh_CN" else "Receiver path"
        self.workspace_tabs.addTab(self.receiver_tab, tab_text)
        return panel

    def refresh(self) -> None:
        super().refresh()
        if hasattr(self, "receiver_flow"):
            self.receiver_flow.set_package_ready(
                self.session.snapshot().package_path is not None
            )

    def decrypt_user(self, user_id: str, password: str, output_path: Path) -> DecryptResult:
        result = super().decrypt_user(user_id, password, output_path)
        self.receiver_flow.show_result(
            result,
            mode="normal",
            user_id=user_id,
            target_recipient_id=user_id,
        )
        self.workspace_tabs.setCurrentWidget(self.receiver_tab)
        return result

    def force_try_user(
        self,
        attacker_user_id: str,
        password: str,
        target_recipient_id: str,
        output_path: Path,
    ) -> DecryptResult:
        result = super().force_try_user(
            attacker_user_id,
            password,
            target_recipient_id,
            output_path,
        )
        self.receiver_flow.show_result(
            result,
            mode="force",
            user_id=attacker_user_id,
            target_recipient_id=target_recipient_id,
        )
        self.workspace_tabs.setCurrentWidget(self.receiver_tab)
        return result

    def reset_broadcast(self, *, keep_media: bool = True) -> None:
        super().reset_broadcast(keep_media=keep_media)
        self.receiver_flow.clear(package_ready=False)
        self.workspace_tabs.setCurrentIndex(0)
