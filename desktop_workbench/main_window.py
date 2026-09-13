"""MainWindow：OBJECTS | WORKSPACE | CODE 三栏 + Current Task 任务栏。

交互模型：**用户直接操作算法对象**（拖 W_i 进聚合器 / 点选 term 消去 / 自己判断解码），
Execute 才真实调用 CHW25 helper。动画只表现「操作发生 → 算法状态变化」。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .code_panel import CodePanel
from .demo_engine import (
    TASK_BUILD_WS,
    TASK_CANCEL,
    TASK_DECODE,
    DemoEngine,
)
from .palette import (
    AUTHORIZED,
    BG,
    BORDER,
    CIPHERTEXT,
    DISABLED,
    MUTED,
    NOISE,
    PUBLIC,
    RERANDOM,
    SECRET,
    SURFACE,
    SURFACE2,
    TEXT,
)
from .scene import (
    BuildWSScene,
    CancellationScene,
    StageView,
    ThresholdScene,
)

TASKS = [TASK_BUILD_WS, TASK_CANCEL, TASK_DECODE]

HINTS = {
    TASK_BUILD_WS: "Drag W2 and W4 (recipient public keys) into the aggregator, then Execute.\n"
                   "W1 / W3 are not in S and will be rejected.",
    TASK_CANCEL: "Click one LEFT term and one matching RIGHT term, then Execute to cancel.\n"
                 "Cancel both shared terms ( s^T p  and  s^T (W0+WS) r2 ) to unlock z.",
    TASK_DECODE: "Choose 0 or 1, then Execute to run decode_z().",
}


class ObjectPanel(QWidget):
    """左栏 OBJECTS：舞台对象的语义清单。"""

    def __init__(self, engine: DemoEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setStyleSheet(f"background:{SURFACE2};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(6)
        t = QLabel("OBJECTS")
        t.setStyleSheet(f"color:{PUBLIC}; font:bold 11px 'Consolas';")
        lay.addWidget(t)
        self.list = QListWidget()
        self.list.setFrameShape(QFrame.Shape.NoFrame)
        self.list.setStyleSheet(
            f"QListWidget {{ background:{SURFACE2}; color:{TEXT}; font:11px 'Consolas'; }}"
        )
        lay.addWidget(self.list, 1)
        self.refresh()

    def refresh(self):
        ev = self.engine
        self.list.clear()

        def add(txt, color, dim=False):
            it = QListWidgetItem(txt)
            it.setForeground(QColor(DISABLED if dim else color))
            self.list.addItem(it)

        add("Sender", CIPHERTEXT)
        add("A , p", PUBLIC)
        add("", MUTED)
        for u in range(1, ev.params.N + 1):
            rec = u in ev.s_set
            add(f"u{u}   {ev.user_label(u)}", AUTHORIZED if rec else MUTED, dim=not rec)
        add("", MUTED)
        add("W_S Aggregator", CIPHERTEXT)
        if ev.ws_slots:
            add("  <- " + " + ".join(ev.user_label(j) for j in ev.ws_slots), AUTHORIZED)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CHW25 Interactive Execution Workbench")
        self.resize(1680, 940)
        self.engine = DemoEngine()
        self.task_idx = 0
        self.guess = None

        central = QWidget()
        central.setStyleSheet(f"background:{BG};")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # ---- 三栏 ----
        cols = QHBoxLayout()
        cols.setSpacing(8)

        self.objects = ObjectPanel(self.engine)
        self.objects.setFixedWidth(210)
        cols.addWidget(self.objects)

        # workspace: 三个交互场景
        self.ws_scene = BuildWSScene(self.engine)
        self.cancel_scene = CancellationScene(self.engine)
        self.thr_scene = ThresholdScene(self.engine)
        self.ws_scene.token_dropped.connect(self.ws_scene.on_release)
        self.cancel_scene.term_clicked.connect(self._on_term_clicked)

        self.stack = QStackedWidget()
        self.ws_view = StageView(self.ws_scene)
        self.cancel_view = StageView(self.cancel_scene)
        self.thr_view = StageView(self.thr_scene)
        for v in (self.ws_view, self.cancel_view, self.thr_view):
            v.setStyleSheet(f"border:1px solid {BORDER}; border-radius:8px;")
            self.stack.addWidget(v)
        cols.addWidget(self.stack, 1)

        self.code = CodePanel()
        self.code.setFixedWidth(400)
        cols.addWidget(self.code)

        root.addLayout(cols, 1)

        # ---- 任务栏 ----
        bar = QWidget()
        bar.setStyleSheet(f"background:{SURFACE}; border:1px solid {BORDER}; border-radius:8px;")
        b = QHBoxLayout(bar)
        b.setContentsMargins(12, 8, 12, 8)
        b.setSpacing(10)

        tl = QLabel("Current Task:")
        tl.setStyleSheet(f"color:{MUTED}; font:11px 'Consolas';")
        b.addWidget(tl)
        self.task_lbl = QLabel(TASKS[0])
        self.task_lbl.setStyleSheet(f"color:{TEXT}; font:bold 12px 'Consolas';")
        b.addWidget(self.task_lbl, 1)

        if True:
            self.btn0 = QPushButton("0")
            self.btn1 = QPushButton("1")
            for btn in (self.btn0, self.btn1):
                btn.setFixedWidth(46)
                btn.setVisible(False)
                b.addWidget(btn)
            self.btn0.clicked.connect(lambda: self._pick_guess(0))
            self.btn1.clicked.connect(lambda: self._pick_guess(1))

        for name, slot in (("Back", self.on_back), ("Hint", self.on_hint),
                           ("Execute", self.on_execute), ("Reset", self.on_reset)):
            btn = QPushButton(name)
            btn.setFixedWidth(96)
            btn.setStyleSheet(
                f"QPushButton {{ background:{SURFACE2}; color:{TEXT};"
                f" border:1px solid {BORDER}; border-radius:6px; padding:6px;"
                f" font:11px 'Segoe UI'; }}"
                f"QPushButton:hover {{ border-color:{PUBLIC}; }}"
            )
            btn.clicked.connect(slot)
            if name == "Execute":
                self.exec_btn = btn
                btn.setStyleSheet(
                    f"QPushButton {{ background:#1D4ED8; color:white; border:none;"
                    f" border-radius:6px; padding:6px; font:bold 11px 'Segoe UI'; }}"
                )
            b.addWidget(btn)

        root.addWidget(bar)

        self.msg = QLabel("")
        self.msg.setStyleSheet(f"color:{MUTED}; font:11px 'Consolas'; padding-left:4px;")
        root.addWidget(self.msg)

        self.engine.changed.connect(self.refresh)
        self.refresh()

    # ---------------- 任务切换 ----------------

    def on_back(self):
        if self.task_idx > 0:
            self.task_idx -= 1
            self.refresh()

    def on_hint(self):
        self.engine.message = HINTS[TASKS[self.task_idx]]
        self.engine.message_kind = "info"
        self.engine.changed.emit()

    def on_reset(self):
        t = TASKS[self.task_idx]
        if t == TASK_BUILD_WS:
            self.engine.reset_ws()
            for tk in self.ws_scene.tokens.values():
                tk.setVisible(True)
            self.ws_scene.refresh()
        elif t == TASK_CANCEL:
            self.engine.cancelled.clear()
            self.engine.selected = {"L": None, "R": None}
            self.engine.z_result = None
            self.cancel_scene.reset_visual()
        else:
            self.engine.decode_guess = None
            self.engine.decode_ok = None
        self.refresh()

    def on_execute(self):
        t = TASKS[self.task_idx]
        if t == TASK_BUILD_WS:
            if self.engine.execute_build_ws():
                self.ws_scene.merge_tokens()
                self.ws_scene.refresh()
        elif t == TASK_CANCEL:
            if self.engine.can_cancel():
                self.engine.cancel_selected()
            elif self.engine.all_cancelled() and self.engine.z_result is None:
                self.engine.compute_z_now()
            else:
                self.engine.message = "Select a matching pair first"
                self.engine.message_kind = "error"
                self.engine.changed.emit()
        else:
            if self.guess is None:
                self.engine.message = "Choose 0 or 1 first"
                self.engine.message_kind = "error"
                self.engine.changed.emit()
            else:
                self.engine.submit_decode(self.guess)
                self.thr_scene.build()
        self.refresh()

    def _pick_guess(self, g: int):
        self.guess = g
        self.engine.message = f"Decode as: {g}  —  press Execute"
        self.engine.message_kind = "info"
        self.engine.changed.emit()

    def _on_term_clicked(self, side: str, key):
        self.engine.select_term(side, key)

    # ---------------- 刷新 ----------------

    def refresh(self):
        t = TASKS[self.task_idx]
        self.task_lbl.setText(t)
        self.stack.setCurrentIndex(self.task_idx)
        self.btn0.setVisible(t == TASK_DECODE)
        self.btn1.setVisible(t == TASK_DECODE)

        self.objects.refresh()
        self.ws_scene.refresh()
        self.cancel_scene.refresh()
        if t == TASK_DECODE:
            self.thr_scene.build()

        # CodePanel：按任务展示对应 helper
        tag = {TASK_BUILD_WS: TASK_BUILD_WS,
               TASK_CANCEL: "term" if not self.engine.all_cancelled() else TASK_CANCEL,
               TASK_DECODE: TASK_DECODE}[t]
        if t == TASK_BUILD_WS and self.engine.ws_executed:
            tag = "execute_build_ws"
        self.code.set_code(self.engine.code_for(tag), "construction.py")
        self.code.set_variables(self.engine.variables())

        kind_color = {"ok": AUTHORIZED, "error": NOISE}.get(self.engine.message_kind, MUTED)
        self.msg.setText(self.engine.message)
        self.msg.setStyleSheet(f"color:{kind_color}; font:11px 'Consolas'; padding-left:4px;")
