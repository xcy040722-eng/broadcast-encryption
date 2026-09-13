"""CodePanel：Debugger 风格（source + current line marker + variables）。

- 读取**真实源码**（由 demo_engine.read_source 切片）；
- 当前执行行用「左侧 accent bar + 极轻 background tint」，不用大片蓝块；
- 下方 Variables 表：执行 → 变量变化 → 视觉变化。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .palette import (
    AUTHORIZED,
    BORDER,
    MUTED,
    NOISE,
    PUBLIC,
    SURFACE,
    SURFACE2,
    TEXT,
)


class SourceView(QPlainTextEdit):
    """源码视图：手绘 current-line accent bar + 轻 tint。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)   # 代码不折行
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet(
            f"QPlainTextEdit {{ background:{SURFACE}; color:{TEXT}; border:none;"
            f" font-family: Consolas, 'Microsoft YaHei', monospace; font-size:9pt; }}"
        )
        self._cur_rows: list[int] = []
        self._hl_rows: list[int] = []

    def set_code(self, lines: list[dict], current_rows: list[int] | None = None):
        self._hl_rows = [i for i, l in enumerate(lines) if l.get("hl")]
        self._cur_rows = current_rows or self._hl_rows[:1]
        txt = "\n".join(f"{l['n']:>4}  {l['t']}" for l in lines)
        self.setPlainText(txt)
        self.viewport().update()

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self.viewport())
        fm = self.fontMetrics()
        lh = fm.lineSpacing()
        top = self.verticalScrollBar().value() * lh
        for i in self._hl_rows:
            y = i * lh - top
            if y + lh < 0 or y > self.viewport().height():
                continue
            # 极轻 background tint
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(103, 183, 255, 22))
            p.drawRect(0, y, self.viewport().width(), lh)
        for i in self._cur_rows:
            y = i * lh - top
            if y + lh < 0 or y > self.viewport().height():
                continue
            # 左侧 accent bar（细）
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(PUBLIC))
            p.drawRect(0, y, 3, lh)
            # current-line ▶ marker
            p.setPen(QPen(QColor(PUBLIC)))
            p.setBrush(QColor(PUBLIC))
            p.drawText(6, y + lh - 4, "▶")
        p.end()


class CodePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{SURFACE}; color:{TEXT};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        head = QLabel("SOURCE")
        head.setStyleSheet(f"color:{PUBLIC}; font:bold 11px 'Consolas';")
        lay.addWidget(head)

        self.file_lbl = QLabel("-")
        self.file_lbl.setStyleSheet(f"color:{MUTED}; font:10px 'Consolas';")
        lay.addWidget(self.file_lbl)

        self.src = SourceView()
        lay.addWidget(self.src, 3)

        vhead = QLabel("VARIABLES")
        vhead.setStyleSheet(f"color:{PUBLIC}; font:bold 11px 'Consolas';")
        lay.addWidget(vhead)

        self.tbl = QTableWidget(0, 2)
        self.tbl.setHorizontalHeaderLabels(["name", "value"])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tbl.setShowGrid(False)
        self.tbl.setFont(QFont("Consolas", 9))
        self.tbl.setStyleSheet(
            f"QTableWidget {{ background:{SURFACE2}; color:{TEXT}; border:1px solid {BORDER}; }}"
            f"QHeaderView::section {{ background:{SURFACE2}; color:{MUTED};"
            f" border:none; padding:3px; font:9px 'Consolas'; }}"
        )
        lay.addWidget(self.tbl, 2)

    def set_code(self, lines: list[dict], file_label: str, current_rows=None):
        self.file_lbl.setText(file_label)
        self.src.set_code(lines, current_rows)

    def set_variables(self, pairs: list[tuple[str, str]]):
        self.tbl.setRowCount(len(pairs))
        for r, (k, v) in enumerate(pairs):
            for c, txt in enumerate((k, v)):
                it = QTableWidgetItem(txt)
                it.setForeground(QColor(TEXT if c else MUTED))
                self.tbl.setItem(r, c, it)
