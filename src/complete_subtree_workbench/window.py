"""PySide6 teaching workbench for the unified Complete Subtree backend."""

from __future__ import annotations

from typing import Callable, TypeVar

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.complete_subtree_mre.interactive_session import (
    CompleteSubtreeSession,
    CsSessionStage,
)
from src.complete_subtree_mre.types import CsRecoverResult
from src.sm2_sm4_workbench.window import LIGHT_STYLE

from .defense_guide import guide_for
from .i18n import DEFAULT_LANGUAGE, Translator
from .principle_inspector import CsReceiverState, CompleteSubtreePrincipleInspector
from .result_presenter import present_cs_result
from .tree_canvas import CompleteSubtreeCanvas
from .widgets import ContentKeyCard


T = TypeVar("T")


class CompleteSubtreeWorkbenchWindow(QMainWindow):
    """Direct-manipulation Complete Subtree workbench backed by real session calls."""

    def __init__(
        self,
        *,
        session: CompleteSubtreeSession | None = None,
        n: int = 8,
        language: str = DEFAULT_LANGUAGE,
    ) -> None:
        super().__init__()
        self.session = session if session is not None else CompleteSubtreeSession(n)
        self.i18n = Translator(language)
        self.setWindowTitle(self.i18n("window_title"))
        self.resize(1440, 860)
        self.setStyleSheet(LIGHT_STYLE)
        self._revoked_checks: dict[int, QCheckBox] = {}
        self._receiver_state = CsReceiverState()
        self._build_ui()
        self.refresh()

    def _panel(self) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)
        return frame, layout

    def _build_ui(self) -> None:
        root_widget = QWidget()
        root = QVBoxLayout(root_widget)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel(self.i18n("header_title"))
        title.setStyleSheet("font-size: 21px; font-weight: 700;")
        subtitle = QLabel(self.i18n("header_subtitle"))
        subtitle.setObjectName("muted")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch(1)
        self.stage_label = QLabel()
        self.stage_label.setObjectName("stageBadge")
        header.addWidget(self.stage_label)
        reset = QPushButton(self.i18n("reset"))
        reset.clicked.connect(lambda: self._safe(self.reset_broadcast))
        header.addWidget(reset)
        root.addLayout(header)

        self.flow_labels: list[QLabel] = []
        flow = QHBoxLayout()
        for key in ("stage_config", "stage_cover", "stage_key", "stage_header", "stage_receiver"):
            label = QLabel(self.i18n(key))
            label.setObjectName("flowStep")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.flow_labels.append(label)
            flow.addWidget(label)
        root.addLayout(flow)

        self.guide = QLabel()
        self.guide.setWordWrap(True)
        self.guide.setStyleSheet(
            "background:#FFF8DB;border:1px solid #E8D68A;border-radius:8px;"
            "padding:8px 10px;color:#66551B;"
        )
        root.addWidget(self.guide)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_revocation_panel())
        splitter.addWidget(self._build_workspace_panel())
        splitter.addWidget(self._build_receiver_panel())
        splitter.setSizes([270, 850, 310])
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        self.status = QLabel(self.i18n("status_ready"))
        self.status.setObjectName("statusBar")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.setCentralWidget(root_widget)

    def _build_revocation_panel(self) -> QWidget:
        panel, layout = self._panel()
        title = QLabel(self.i18n("panel_revocation"))
        title.setObjectName("objectTitle")
        help_text = QLabel(self.i18n("panel_revocation_help"))
        help_text.setObjectName("muted")
        help_text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(help_text)

        for user_id in range(1, self.session.tree.n + 1):
            cb = QCheckBox(f"u{user_id}")
            cb.toggled.connect(
                lambda checked, uid=user_id: self._safe(
                    lambda: self.session.set_revoked(uid, checked)
                )
            )
            self._revoked_checks[user_id] = cb
            layout.addWidget(cb)

        layout.addStretch(1)
        self.compute_button = QPushButton(self.i18n("compute_cover"))
        self.compute_button.setObjectName("primary")
        self.compute_button.clicked.connect(lambda: self._safe(self.compute_cover))
        layout.addWidget(self.compute_button)
        return panel

    def _build_workspace_panel(self) -> QWidget:
        panel, layout = self._panel()
        title = QLabel(self.i18n("tree_title"))
        title.setObjectName("objectTitle")
        layout.addWidget(title)

        self.summary = QLabel()
        self.summary.setObjectName("muted")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        material_row = QHBoxLayout()
        self.key_card = ContentKeyCard(self.i18n)
        material_row.addWidget(self.key_card, 1)
        controls = QVBoxLayout()
        self.material_button = QPushButton(self.i18n("generate_material"))
        self.material_button.setObjectName("primary")
        self.material_button.clicked.connect(lambda: self._safe(self.generate_material))
        self.wrap_all_button = QPushButton(self.i18n("wrap_all"))
        self.wrap_all_button.clicked.connect(lambda: self._safe(self.wrap_all))
        controls.addWidget(self.material_button)
        controls.addWidget(self.wrap_all_button)
        controls.addStretch(1)
        material_row.addLayout(controls)
        layout.addLayout(material_row)

        self.workspace_tabs = QTabWidget()

        graph_tab = QWidget()
        graph_layout = QVBoxLayout(graph_tab)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(7)

        self.canvas = CompleteSubtreeCanvas(self.session.tree)
        self.canvas.wrapRequested.connect(
            lambda node_id: self._safe(lambda: self.wrap_for_node(node_id))
        )
        self.canvas.nodeSelected.connect(self._node_selected)
        graph_layout.addWidget(self.canvas, 1)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(125)
        graph_layout.addWidget(QLabel(self.i18n("log")))
        graph_layout.addWidget(self.log)

        self.principle_inspector = CompleteSubtreePrincipleInspector(self.i18n)
        self.principle_inspector.topicRequested.connect(self._principle_topic_requested)

        graph_text = "关系图" if self.i18n.language == "zh_CN" else "Object graph"
        principle_text = (
            "原理 / 本次状态"
            if self.i18n.language == "zh_CN"
            else "Principle / live state"
        )
        self.workspace_tabs.addTab(graph_tab, graph_text)
        self.workspace_tabs.addTab(self.principle_inspector, principle_text)
        layout.addWidget(self.workspace_tabs, 1)
        return panel

    def _build_receiver_panel(self) -> QWidget:
        panel, layout = self._panel()
        title = QLabel(self.i18n("receiver"))
        title.setObjectName("objectTitle")
        help_text = QLabel(self.i18n("receiver_help"))
        help_text.setObjectName("muted")
        help_text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(help_text)

        self.receiver_user = QComboBox()
        self.receiver_user.addItems(
            [f"u{i}" for i in range(1, self.session.tree.n + 1)]
        )
        layout.addWidget(self.receiver_user)
        self.recover_button = QPushButton(self.i18n("recover"))
        self.recover_button.clicked.connect(lambda: self._safe(self.recover_selected))
        layout.addWidget(self.recover_button)

        layout.addWidget(QLabel(self.i18n("force_target")))
        self.force_target = QComboBox()
        layout.addWidget(self.force_target)
        self.force_button = QPushButton(self.i18n("force_try"))
        self.force_button.clicked.connect(lambda: self._safe(self.force_try_selected))
        layout.addWidget(self.force_button)

        self.receiver_result = QLabel(self.i18n("result_wait"))
        self.receiver_result.setObjectName("muted")
        self.receiver_result.setWordWrap(True)
        layout.addWidget(self.receiver_result)
        layout.addStretch(1)
        return panel

    def _selected_user_id(self) -> int:
        return int(self.receiver_user.currentText().removeprefix("u"))

    def compute_cover(self) -> None:
        snap = self.session.compute_cover()
        self.status.setText(
            self.i18n(
                "status_cover",
                roots=", ".join(f"v{i}" for i in snap.cover_roots) or "∅",
            )
        )
        self._append_log(self.status.text())
        self.refresh()

    def generate_material(self) -> None:
        snap = self.session.generate_content_material()
        self.status.setText(
            self.i18n("status_material", fp=snap.content_key_fingerprint)
        )
        self._append_log(self.status.text())
        self.refresh()

    def wrap_for_node(self, node_id: int) -> None:
        self.session.wrap_for_node(node_id)
        self.status.setText(self.i18n("status_wrapped", node=node_id))
        self._append_log(self.status.text())
        self.refresh()

    def wrap_all(self) -> None:
        before = set(self.session.snapshot().wrapped_nodes)
        snap = self.session.wrap_all()
        for node in snap.wrapped_nodes:
            if node not in before:
                self._append_log(self.i18n("status_wrapped", node=node))
        self.refresh()

    def recover_selected(self) -> CsRecoverResult:
        user_id = self._selected_user_id()
        result = self.session.recover_as(user_id)
        self._receiver_state = CsReceiverState.from_result(result, mode="recover")
        presented = present_cs_result(
            result,
            language=self.i18n.language,
            force=False,
        )
        self.receiver_result.setText(presented.panel_text)
        self.status.setText(presented.status_line)
        self.canvas.set_receiver_result(
            path=result.trace.user_path_nodes,
            matched_node=result.trace.matched_node_id,
        )
        self._append_log(self.status.text())
        self.refresh(keep_receiver_projection=True)
        return result

    def force_try_selected(self) -> CsRecoverResult:
        user_id = self._selected_user_id()
        target = self.force_target.currentData()
        if target is None:
            raise RuntimeError("no Complete Subtree header target is available")
        target = int(target)
        result = self.session.force_try(user_id, target)
        self._receiver_state = CsReceiverState.from_result(result, mode="force")
        presented = present_cs_result(
            result,
            language=self.i18n.language,
            force=True,
            target_node_id=target,
        )
        self.receiver_result.setText(presented.panel_text)
        self.status.setText(presented.status_line)
        self.canvas.set_receiver_result(
            path=result.trace.user_path_nodes,
            failed_target=target,
        )
        self._append_log(self.status.text())
        self.refresh(keep_receiver_projection=True)
        return result

    def reset_broadcast(self) -> None:
        self.session.reset_broadcast()
        self._receiver_state = CsReceiverState()
        self.canvas.clear_receiver_result()
        self.receiver_result.setText(self.i18n("result_wait"))
        self.principle_inspector.clear()
        self.workspace_tabs.setCurrentIndex(0)
        self.status.setText(self.i18n("status_reset"))
        self._append_log(self.status.text())
        self.refresh()

    def _node_selected(self, node_id: int) -> None:
        users = ", ".join(f"u{i}" for i in self.session.tree.users_in_subtree(node_id))
        self._append_log(f"v{node_id}: {{{users}}}")
        snap = self.session.snapshot()
        if node_id in snap.wrapped_nodes:
            topic = f"header:{node_id}"
        elif node_id in snap.cover_roots:
            topic = f"cover:{node_id}"
        elif node_id in snap.steiner_nodes:
            topic = f"steiner:{node_id}"
        else:
            topic = f"nodekey:{node_id}"
        self.principle_inspector.show_topic(
            topic,
            snapshot=snap,
            receiver=self._receiver_state,
        )
        self.workspace_tabs.setCurrentWidget(self.principle_inspector)

    def _principle_topic_requested(self, topic: str) -> None:
        self.principle_inspector.show_topic(
            topic,
            snapshot=self.session.snapshot(),
            receiver=self._receiver_state,
        )

    def _append_log(self, text: str) -> None:
        self.log.appendPlainText(text)

    def _guide_text(self, stage: CsSessionStage) -> str:
        return {
            CsSessionStage.CONFIGURING: self.i18n("guide_initial"),
            CsSessionStage.COVER_READY: self.i18n("guide_cover"),
            CsSessionStage.MATERIAL_READY: self.i18n("guide_material"),
            CsSessionStage.WRAPPING: self.i18n("guide_wrapping"),
            CsSessionStage.HEADER_READY: self.i18n("guide_ready"),
        }[stage]

    def refresh(self, *, keep_receiver_projection: bool = False) -> None:
        snap = self.session.snapshot()
        self.stage_label.setText(self.i18n("stage_badge", stage=snap.stage.value))
        self.guide.setText(
            guide_for(
                snap,
                self._receiver_state,
                language=self.i18n.language,
            ).text
        )
        self.summary.setText(
            self.i18n(
                "cover_summary",
                revoked="{" + ",".join(f"u{i}" for i in snap.revoked_users) + "}",
                st="{" + ",".join(f"v{i}" for i in snap.steiner_nodes) + "}",
                cover="{" + ",".join(f"v{i}" for i in snap.cover_roots) + "}",
            )
        )

        for uid, cb in self._revoked_checks.items():
            cb.blockSignals(True)
            cb.setChecked(uid in snap.revoked_users)
            cb.setEnabled(snap.stage == CsSessionStage.CONFIGURING)
            cb.blockSignals(False)

        self.compute_button.setEnabled(snap.stage == CsSessionStage.CONFIGURING)
        self.material_button.setEnabled(snap.stage == CsSessionStage.COVER_READY)
        self.wrap_all_button.setEnabled(
            snap.stage in {CsSessionStage.MATERIAL_READY, CsSessionStage.WRAPPING}
        )
        self.key_card.set_state(
            snap.content_key_fingerprint,
            draggable=snap.stage in {
                CsSessionStage.MATERIAL_READY,
                CsSessionStage.WRAPPING,
            },
        )
        self.canvas.set_snapshot(snap)
        self.principle_inspector.set_state(
            snapshot=snap,
            receiver=self._receiver_state,
        )
        if not keep_receiver_projection and snap.stage != CsSessionStage.HEADER_READY:
            self.canvas.clear_receiver_result()

        self.force_target.blockSignals(True)
        current_target = self.force_target.currentData()
        self.force_target.clear()
        for node in snap.wrapped_nodes:
            self.force_target.addItem(f"v{node} · E[L{node}](K)", node)
        if current_target is not None:
            idx = self.force_target.findData(current_target)
            if idx >= 0:
                self.force_target.setCurrentIndex(idx)
        self.force_target.blockSignals(False)

        ready = snap.stage == CsSessionStage.HEADER_READY
        self.recover_button.setEnabled(ready)
        self.force_button.setEnabled(ready and self.force_target.count() > 0)

        stage_index = {
            CsSessionStage.CONFIGURING: 0,
            CsSessionStage.COVER_READY: 1,
            CsSessionStage.MATERIAL_READY: 2,
            CsSessionStage.WRAPPING: 3,
            CsSessionStage.HEADER_READY: 4,
        }[snap.stage]
        for idx, label in enumerate(self.flow_labels):
            label.setProperty("done", idx < stage_index)
            label.setProperty("active", idx == stage_index)
            label.style().unpolish(label)
            label.style().polish(label)

    def _safe(self, action: Callable[[], T]) -> T | None:
        try:
            value = action()
            self.refresh()
            return value
        except Exception as exc:
            self.status.setText(f"{type(exc).__name__}: {exc}")
            self._append_log(self.status.text())
            self.refresh()
            return None
