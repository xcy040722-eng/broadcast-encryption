"""渲染 CHW25 Manim 经典场景（N=4, S={2,4}, u2, μ=1）。

用法：
    python visualization/manim/render_demo.py            # 1920x1080 @ 30fps
    python visualization/manim/render_demo.py --fast     # 低质量快速预览
    python visualization/manim/render_demo.py --fps 60
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MANIM_DIR = os.path.join(ROOT, "visualization", "manim")
OUT_DIR = os.path.join(MANIM_DIR, "output")
MEDIA_DIR = os.path.join(MANIM_DIR, "media")


def _ffmpeg_exe() -> str | None:
    """优先用 imageio-ffmpeg 自带的 ffmpeg；否则用系统 PATH 上的。"""
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def build_env() -> dict:
    env = dict(os.environ)
    ff = _ffmpeg_exe()
    if ff:
        env["FFMPEG_BINARY"] = ff
        env["PATH"] = os.path.dirname(ff) + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
    return env


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="低质量快速预览 (-ql)")
    ap.add_argument("--fps", type=int, default=30, help="帧率（默认 30）")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    args = ap.parse_args()

    env = build_env()
    os.makedirs(OUT_DIR, exist_ok=True)

    cmd = [sys.executable, "-m", "manim"]
    if args.fast:
        cmd += ["-ql"]
    else:
        cmd += ["-r", f"{args.width},{args.height}", "--fps", str(args.fps)]
    cmd += [
        os.path.join(MANIM_DIR, "chw25_scene.py"),
        "CHW25Scene",
        "--media_dir", MEDIA_DIR,
        "-o", "chw25_classic",
        "--disable_caching",
    ]

    print("运行:", " ".join(cmd))
    print("FFMPEG_BINARY:", env.get("FFMPEG_BINARY"))
    rc = subprocess.call(cmd, env=env, cwd=ROOT)
    if rc != 0:
        print(f"渲染失败，退出码 {rc}")
        return rc

    # 找到**合成**产物（排除 partial_movie_files 分片）并复制到 output/
    candidates = []
    for dirpath, dirnames, filenames in os.walk(MEDIA_DIR):
        if "partial_movie_files" in dirpath:
            continue
        for fn in filenames:
            if fn.endswith(".mp4"):
                candidates.append(os.path.join(dirpath, fn))
    # 取修改时间最新的合成产物
    found = max(candidates, key=os.path.getmtime) if candidates else None
    if found:
        dst = os.path.join(OUT_DIR, "chw25_classic.mp4")
        shutil.copy2(found, dst)
        size_mb = os.path.getsize(dst) / (1024 * 1024)
        print(f"\n产物: {dst}  ({size_mb:.1f} MB)")
        print(f"源:   {found}")
    else:
        print("未找到合成 mp4 产物")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
