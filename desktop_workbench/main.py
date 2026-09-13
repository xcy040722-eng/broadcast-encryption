"""CHW25 Interactive Execution Workbench —— 入口。

用法：
    python desktop_workbench/main.py                 # 交互（用户自己操作对象）
    python desktop_workbench/main.py --screenshots   # 产出审核截图

不做自动播放；所有推进来自用户的拖放 / 点选 / Execute。
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PySide6.QtWidgets import QApplication  # noqa: E402

from desktop_workbench.demo_engine import TASK_BUILD_WS, TASK_CANCEL  # noqa: E402
from desktop_workbench.main_window import TASKS, MainWindow  # noqa: E402

SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")


def _grab(app: QApplication, win: MainWindow, name: str) -> str:
    win.repaint()
    app.processEvents()
    app.processEvents()
    path = os.path.join(SHOT_DIR, name)
    win.grab().save(path)
    print("  saved", path)
    return path


def capture_sequence(app: QApplication, win: MainWindow) -> None:
    """按人工审核要求，产出 6 组状态截图。"""
    os.makedirs(SHOT_DIR, exist_ok=True)
    ev = win.engine

    # --- Experiment A ---
    win.task_idx = 0
    win.refresh()
    _grab(app, win, "01_build_ws_initial.png")

    ev.add_to_ws(2)
    win.ws_scene.refresh()
    win.refresh()
    _grab(app, win, "02_w2_added.png")

    ev.add_to_ws(4)
    win.ws_scene.refresh()
    win.refresh()
    _grab(app, win, "03_w2_w4_ready_execute.png")

    # 顺带演示拒绝（不单独出图，但写入状态）
    ev.add_to_ws(1)          # 应被拒绝
    win.refresh()

    ev.execute_build_ws()
    win.ws_scene.refresh()
    win.refresh()
    _grab(app, win, "04_ws_executed.png")

    # --- Experiment B ---
    win.task_idx = 1
    ev.cancelled.clear()
    ev.selected = {"L": None, "R": None}
    ev.z_result = None
    win.cancel_scene.reset_visual()
    win.refresh()
    _grab(app, win, "05_cancellation_awaiting.png")

    # 第一组：s^T p
    ev.select_term("L", "stp")
    ev.select_term("R", "stp")
    ev.cancel_selected()
    win.cancel_scene.refresh()
    win.refresh()
    _grab(app, win, "06a_cancel_first_pair.png")

    # 第二组：s^T (W0+WS) r2
    ev.select_term("L", "w0ws")
    ev.select_term("R", "w0ws")
    ev.cancel_selected()
    win.cancel_scene.refresh()
    win.refresh()
    _grab(app, win, "06b_cancel_second_pair_done.png")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--screenshots", action="store_true", help="产出审核截图后退出")
    ap.add_argument("--task", type=int, default=0, choices=[0, 1, 2])
    args = ap.parse_args()

    app = QApplication(sys.argv)
    win = MainWindow()
    win.task_idx = args.task
    win.refresh()
    win.show()

    if args.screenshots:
        capture_sequence(app, win)
        print("截图完成 →", SHOT_DIR)
        return 0

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
