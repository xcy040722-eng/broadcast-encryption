"""绘图：从 summary 数据生成 6 张核心图。

每张图固定筛选条件，保证每个 (x, y) 点统计口径唯一：
- 图 1/3/4/5/6（vs N）：固定 case=random + 固定 ratio。
- 图 2（vs r）：固定 case=random + 固定 N。
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")  # 无显示环境
import matplotlib.pyplot as plt

# 代表性撤销比例（用于 vs N 的图）
REPRESENTATIVE_RATIOS = ("0.05", "0.25")
# 代表性 N（用于 vs r 的图）
REPRESENTATIVE_NS = (256, 1024)


def _extract(summary, algorithm, case, ratio, x_key, y_key):
    """提取某 (algorithm, case, ratio) 下的 (x, y) 序列（按 x 排序、去重）。"""
    pts = sorted(
        (r[x_key], r[y_key])
        for r in summary
        if r["algorithm"] == algorithm and r["case"] == case and r["ratio"] == ratio
    )
    # 同一 x 可能有多个点（理论上不会，因为固定了 case/ratio），取第一个
    dedup = {}
    for x, y in pts:
        dedup.setdefault(x, y)
    xs = sorted(dedup)
    return xs, [dedup[x] for x in xs]


def generate_figures(summary: list[dict], output_dir: str) -> list[str]:
    """生成 6 张图（数据缺失的图自动跳过），返回文件路径列表。"""
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    paths.append(_fig_cover_vs_n(summary, output_dir))
    paths.append(_fig_cover_vs_r(summary, output_dir))
    paths.append(_fig_header_entries_vs_n(summary, output_dir))
    paths.append(_fig_header_bytes_vs_n(summary, output_dir))
    paths.append(_fig_cover_time_vs_n(summary, output_dir))
    paths.append(_fig_key_material_vs_n(summary, output_dir))

    return [p for p in paths if p is not None]


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _fig_cover_vs_n(summary, out):
    fig, ax = plt.subplots()
    any_data = False
    for ratio in REPRESENTATIVE_RATIOS:
        for algo in ("CS", "SD"):
            xs, ys = _extract(summary, algo, "random", ratio, "N", "cover_count_median")
            if not xs:
                continue
            any_data = True
            ax.plot(xs, ys, marker="o", label=f"{algo} ρ={ratio}")
    if not any_data:
        plt.close(fig)
        return None
    ax.set_xlabel("N")
    ax.set_ylabel("|Cover|")
    ax.set_title("Cover Count vs N (case=random)")
    ax.legend()
    p = os.path.join(out, "fig1_cover_vs_n.png")
    _save(fig, p)
    return p


def _fig_cover_vs_r(summary, out):
    fig, ax = plt.subplots()
    any_data = False
    for N in REPRESENTATIVE_NS:
        for algo in ("CS", "SD"):
            rows = sorted(
                (r for r in summary if r["N"] == N and r["algorithm"] == algo and r["case"] == "random"),
                key=lambda r: r["r"],
            )
            if not rows:
                continue
            any_data = True
            xs = [r["r"] for r in rows]
            ys = [r["cover_count_median"] for r in rows]
            ax.plot(xs, ys, marker="o", label=f"{algo} N={N}")
    if not any_data:
        plt.close(fig)
        return None
    ax.set_xlabel("r")
    ax.set_ylabel("|Cover|")
    ax.set_title("Cover Count vs r (case=random)")
    ax.legend()
    p = os.path.join(out, "fig2_cover_vs_r.png")
    _save(fig, p)
    return p


def _fig_header_entries_vs_n(summary, out):
    return _single_metric_vs_n(summary, out, "fig3_header_entries_vs_n.png",
                               "logical header entries", "Header (logical entries) vs N",
                               "cover_count_median")


def _fig_header_bytes_vs_n(summary, out):
    return _single_metric_vs_n(summary, out, "fig4_header_bytes_vs_n.png",
                               "bytes", "Serialized Header Size vs N",
                               "header_bytes_median")


def _fig_cover_time_vs_n(summary, out):
    p = _single_metric_vs_n(summary, out, "fig5_cover_time_vs_n.png",
                            "μs", "Cover Generation Time vs N",
                            "cover_ns_median", scale=1e-3)
    return p


def _fig_key_material_vs_n(summary, out):
    fig, ax = plt.subplots()
    any_data = False
    ratio = "0.25"
    for algo in ("CS", "SD"):
        xs, ys = _extract(summary, algo, "random", ratio, "N", "key_material_mean_mean")
        if xs:
            any_data = True
            ax.plot(xs, ys, marker="o", label=f"{algo} mean")
        xs, ys = _extract(summary, algo, "random", ratio, "N", "key_material_max_mean")
        if xs:
            any_data = True
            ax.plot(xs, ys, marker="^", linestyle="--", label=f"{algo} max")
    if not any_data:
        plt.close(fig)
        return None
    ax.set_xlabel("N")
    ax.set_ylabel("keys / labels per user")
    ax.set_title("User Key Material vs N (case=random, ρ=0.25)")
    ax.legend()
    p = os.path.join(out, "fig6_key_material_vs_n.png")
    _save(fig, p)
    return p


def _single_metric_vs_n(summary, out, filename, ylabel, title, metric, scale=1.0):
    """固定 case=random + ρ=0.25，画某 metric vs N（CS/SD）。"""
    fig, ax = plt.subplots()
    any_data = False
    ratio = "0.25"
    for algo in ("CS", "SD"):
        xs, ys = _extract(summary, algo, "random", ratio, "N", metric)
        if not xs:
            continue
        any_data = True
        ys = [y * scale for y in ys]
        ax.plot(xs, ys, marker="o", label=algo)
    if not any_data:
        plt.close(fig)
        return None
    ax.set_xlabel("N")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title} (case=random, ρ=0.25)")
    ax.legend()
    p = os.path.join(out, filename)
    _save(fig, p)
    return p
