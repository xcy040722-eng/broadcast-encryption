"""v0.5 defense-oriented workbench layer.

Adds a clickable principle/live-state inspector on top of the already validated
sender relationship canvas and receiver-path canvas.  It presents receiver
results in localized defense-friendly text while preserving stable backend
status codes, and adds a state-driven *manual* defense guide.  The guide never
executes actions or advances the state machine; it only suggests what the
presenter can do next.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QPointF, QRectF
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.sm2_sm4_mre.types import DecryptResult

from .defense_guide import guide_for
from .principle_inspector import PrincipleInspector
from .receiver_workbench import ReceiverVisualWorkbenchWindow
from .result_presenter import present_decrypt_result


class DefenseWorkbenchWindow(ReceiverVisualWorkbenchWindow):
    """Final teaching/defense shell with real crypto and manual guidance."""

    def _build_workspace_panel(self) -> QWidget:
        panel = super()._build_workspace_panel()

        self.defense_guide_label = QLabel()
        self.defense_guide_label.setObjectName("defenseGuide")
        self.defense_guide_label.setWordWrap(True)
        panel_layout = panel.layout()
        if isinstance(panel_layout, QVBoxLayout):
            panel_layout.insertWidget(1, self.defense_guide_label)

        self.principle_tab = QWidget()
        layout = QVBoxLayout(self.principle_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.principle_inspector = PrincipleInspector(self.i18n)
        layout.addWidget(self.principle_inspector, 1)

        tab_text = "原理 / 本次状态" if self.i18n.language == "zh_CN" else "Principle / live state"
        self.workspace_tabs.addTab(self.principle_tab, tab_text)

        # Use a release-event observer rather than replacing the already tested
        # drag/drop implementation.  The existing canvases remain the sole
        # executors/projections; this layer only interprets clicks for teaching.
        self.relation_canvas.installEventFilter(self)
        self.receiver_flow.installEventFilter(self)
        return panel

    def refresh(self) -> None:
        super().refresh()
        if hasattr(self, "principle_inspector"):
            snapshot = self.session.snapshot()
            receiver_state = self.receiver_flow.state
            self.principle_inspector.refresh_state(
                snapshot=snapshot,
                receiver_state=receiver_state,
            )
            if hasattr(self, "defense_guide_label"):
                self.defense_guide_label.setText(
                    guide_for(
                        snapshot,
                        receiver_state,
                        language=self.i18n.language,
                    ).text
                )

    def decrypt_user(self, user_id: str, password: str, output_path: Path) -> DecryptResult:
        result = super().decrypt_user(user_id, password, output_path)
        presented = present_decrypt_result(
            result,
            language=self.i18n.language,
            user_id=user_id,
            target_recipient_id=user_id,
            force=False,
        )
        self.receiver_result.setText(presented.panel_text)
        self._set_status(presented.status_line)
        self.refresh()
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
        presented = present_decrypt_result(
            result,
            language=self.i18n.language,
            user_id=attacker_user_id,
            target_recipient_id=target_recipient_id,
            force=True,
        )
        self.receiver_result.setText(presented.panel_text)
        self._set_status(presented.status_line)
        self.refresh()
        return result

    def reset_broadcast(self, *, keep_media: bool = True) -> None:
        super().reset_broadcast(keep_media=keep_media)
        if hasattr(self, "principle_inspector"):
            self.principle_inspector.clear()
        self.refresh()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 - Qt API
        if event.type() == QEvent.Type.MouseButtonRelease:
            if watched is getattr(self, "relation_canvas", None):
                topic = self._relation_topic_at(event.position())
                if topic:
                    self._show_principle(topic)
            elif watched is getattr(self, "receiver_flow", None):
                topic = self._receiver_topic_at(event.position())
                if topic:
                    self._show_principle(topic)
        return super().eventFilter(watched, event)

    def _show_principle(self, topic: str) -> None:
        self.principle_inspector.show_topic(
            topic,
            snapshot=self.session.snapshot(),
            receiver_state=self.receiver_flow.state,
        )
        self.workspace_tabs.setCurrentWidget(self.principle_tab)

    def _relation_topic_at(self, point: QPointF) -> str | None:
        regions = self.relation_canvas._layout_regions()  # safe view geometry only
        priority = ["key", "media", "engine", "package"]
        priority.extend(f"recipient:{uid}" for uid in self.relation_canvas.state.recipients)
        for name in priority:
            rect = regions.get(name)
            if rect is not None and rect.contains(point):
                return name
        return None

    def _receiver_topic_at(self, point: QPointF) -> str | None:
        canvas = self.receiver_flow
        margin = 18.0
        width = max(680.0, float(canvas.width()) - margin * 2)
        y = 70.0
        node_w = min(180.0, (width - 80.0) / 5.0)
        gap = (width - node_w * 5.0) / 4.0
        rects = [
            QRectF(margin + i * (node_w + gap), y, node_w, 72.0)
            for i in range(5)
        ]
        topics = [
            "receiver:sk",
            "receiver:wrapped",
            "receiver:unwrap",
            "receiver:key",
            "receiver:gcm",
        ]
        for rect, topic in zip(rects, topics):
            if rect.contains(point):
                return topic
        return None
