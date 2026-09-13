"""CHW25 Desktop POC 入口（PySide6 + Qt Quick/QML）。

用法：
    python desktop/main.py                  # 交互模式（只手动推进）
    python desktop/main.py --auto-advance 4  # 仅供录制：每 4 秒自动推进

数据：由 src/chw25_dbe 后端实时生成（不硬编码）。
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PySide6.QtCore import QTimer, QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtQuickControls2 import QQuickStyle  # noqa: E402

from desktop.presentation_controller import PresentationController  # noqa: E402

# 使用 Basic 样式，允许自定义 Button 的 background/contentItem（原生样式不允许）
QQuickStyle.setStyle("Basic")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--auto-advance", type=float, default=0.0,
        help="仅供录制：每 N 秒自动推进一步（默认 0 = 纯手动，符合 POC 要求）",
    )
    ap.add_argument("--record", type=str, default="", help="录制到 mp4（Qt 抓帧 + ffmpeg 合成）")
    ap.add_argument("--record-seconds", type=float, default=40.0)
    ap.add_argument("--fps", type=int, default=20)
    args = ap.parse_args()

    app = QGuiApplication(sys.argv)
    ctrl = PresentationController()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("ctrl", ctrl)
    qml = os.path.join(os.path.dirname(__file__), "qml", "Main.qml")
    engine.load(QUrl.fromLocalFile(qml))
    if not engine.rootObjects():
        print("QML 加载失败：", qml)
        return 1
    win = engine.rootObjects()[0]

    # 录制模式内建自动推进（仅用于录屏；交互模式仍为纯手动）
    advance_s = args.auto_advance if args.auto_advance > 0 else (5.0 if args.record else 0.0)
    if advance_s > 0:
        t = QTimer()

        def _tick():
            if ctrl.step >= ctrl.stepCount - 1:
                ctrl.reset()
            else:
                ctrl.next()

        t.timeout.connect(_tick)
        t.start(int(advance_s * 1000))
        print(f"[录制模式] 每 {advance_s}s 自动推进（POC 默认是纯手动）")

    if args.record:
        _start_recording(app, win, args.record, args.record_seconds, args.fps)

    return app.exec()


def _start_recording(app, win, out_path: str, seconds: float, fps: int) -> None:
    """用 QQuickWindow.grabWindow() 抓帧，管道给 ffmpeg 合成 mp4。"""
    import subprocess

    import imageio_ffmpeg
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QTimer

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    w, h = win.width(), win.height()
    out_path = os.path.abspath(out_path)

    proc = subprocess.Popen(
        [
            ff, "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
            "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "20",
            out_path,
        ],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    state = {"n": 0, "max": int(seconds * fps)}

    def grab():
        if state["n"] >= state["max"]:
            timer.stop()
            try:
                proc.stdin.close()
            except Exception:
                pass
            proc.wait(timeout=60)
            print(f"录制完成: {out_path}  ({state['n']} 帧)")
            app.quit()
            return
        img = win.grabWindow()
        img = img.convertToFormat(img.Format.Format_RGB888)
        buf = QBuffer()
        ba = QByteArray()
        buf.setBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buf, "PNG")
        buf.close()
        # PNG 编码后交给 ffmpeg 解码代价高，这里直接用原始字节
        ptr = img.constBits()
        nbytes = img.sizeInBytes()
        data = ptr.tobytes()[: nbytes]
        # 去掉行对齐填充
        stride = img.bytesPerLine()
        if stride != w * 3:
            rows = []
            for y in range(h):
                rows.append(data[y * stride: y * stride + w * 3])
            data = b"".join(rows)
        try:
            proc.stdin.write(data)
        except Exception:
            pass
        state["n"] += 1

    timer = QTimer()
    timer.timeout.connect(grab)
    timer.start(int(1000 / fps))
    print(f"开始录制 {seconds}s @ {fps}fps → {out_path}")


if __name__ == "__main__":
    raise SystemExit(main())
