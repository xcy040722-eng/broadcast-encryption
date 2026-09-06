"""绘图：从 summary 数据生成 6 张核心图。"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")  # 无显示环境
import matplotlib.pyplot as plt


def _series(summary, algorithm, x_key, y_key):
    """从 summary 提取某算法的 (x, y) 序列（按 x 排序）。"""
    pts = sorted(
        (r[x_key], r[y_key]) for r in summary if r["algorithm"] == algorithm
    )
    return [p[0] for p in pts], [p[1] for p in pts]


def generate_figures(summary: list[dict], output_dir: str) -> list[str]:
    """生成 6 张图，返回文件路径列表。"""
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    # 过滤 zero/single 之外的固定 ratio（用于 ratio 对比）
    # 这里只按 N 聚合（对同一 N 取 median across ratios 不直观），
    # 简化为：对每个 ratio 单独画 Cover vs N。

    paths.append(_fig_cover_vs_n(summary, output_dir))
    paths.append(_fig_cover_vs_r(summary, output_dir))
    paths.append(_fig_header_entries_vs_n(summary, output_dir))
    paths.append(_fig_header_bytes_vs_n(summary, output_dir))
    paths.append(_fig_cover_time_vs_n(summary, output_dir))
    paths.append(_fig_key_material_vs_n(summary, output_dir))

    return paths


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _fig_cover_vs_n(summary, out):
    fig, ax = plt.subplots()
    for algo in ("CS", "SD"):
        xs, ys = _series(summary, algo, "N", "cover_count_median")
        ax.plot(xs, ys, marker="o", label=algo)
    ax.set_xlabel("N")
    ax.set_ylabel("|Cover|")
    ax.set_title("Cover Count vs N")
    ax.legend()
    p = os.path.join(out, "fig1_cover_vs_n.png")
    _save(fig, p)
    return p


def _fig_cover_vs_r(summary, out):
    fig, ax = plt.subplots()
    for N in (256, 1024):
        for algo in ("CS", "SD"):
            rows = [r for r in summary if r["N"] == N and r["algorithm"] == algo]
            if not rows:
                continue
            xs = sorted(r["r"] for r in rows)
            ys = [r["cover_count_median"] for r in sorted(rows, key=lambda x: x["r"])]
            ax.plot(xs, ys, marker="o", label=f"{algo} N={N}")
    ax.set_xlabel("r")
    ax.set_ylabel("|Cover|")
    ax.set_title("Cover Count vs r")
    ax.legend()
    p = os.path.join(out, "fig2_cover_vs_r.png")
    _save(fig, p)
    return p


def _fig_header_entries_vs_n(summary, out):
    fig, ax = plt.subplots()
    for algo in ("CS", "SD"):
        xs, ys = _series(summary, algo, "N", "cover_count_median")
        ax.plot(xs, ys, marker="o", label=algo)
    ax.set_xlabel("N")
    ax.set_ylabel("logical header entries")
    ax.set_title("Header (logical entries) vs N")
    ax.legend()
    p = os.path.join(out, "fig3_header_entries_vs_n.png")
    _save(fig, p)
    return p


def _fig_header_bytes_vs_n(summary, out):
    fig, ax = plt.subplots()
    for algo in ("CS", "SD"):
        xs, ys = _series(summary, algo, "N", "header_bytes_median")
        ax.plot(xs, ys, marker="o", label=algo)
    ax.set_xlabel("N")
    ax.set_ylabel("bytes")
    ax.set_title("Serialized Header Size vs N")
    ax.legend()
    p = os.path.join(out, "fig4_header_bytes_vs_n.png")
    _save(fig, p)
    return p


def _fig_cover_time_vs_n(summary, out):
    fig, ax = plt.subplots()
    for algo in ("CS", "SD"):
        xs, ys = _series(summary, algo, "N", "cover_ns_median")
        # ns -> us
        ys = [y / 1000.0 for y in ys]
        ax.plot(xs, ys, marker="o", label=algo)
    ax.set_xlabel("N")
    ax.set_ylabel("μs")
    ax.set_title("Cover Generation Time vs N")
    ax.legend()
    p = os.path.join(out, "fig5_cover_time_vs_n.png")
    _save(fig, p)
    return p


def _fig_key_material_vs_n(summary, out):
    fig, ax = plt.subplots()
    for algo in ("CS", "SD"):
        xs, ys = _series(summary, algo, "N", "key_material_mean_mean")
        ax.plot(xs, ys, marker="o", label=f"{algo} mean")
        xs, ys = _series(summary, algo, "N", "key_material_max_mean")
        ax.plot(xs, ys, marker="^", linestyle="--", label=f"{algo} max")
    ax.set_xlabel("N")
    ax.set_ylabel("keys / labels per user")
    ax.set_title("User Key Material vs N")
    ax.legend()
    p = os.path.join(out, "fig6_key_material_vs_n.png")
    _save(fig, p)
    return p
