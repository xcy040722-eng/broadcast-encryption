"""CS vs SD Benchmark 主入口。

编排完整 benchmark：环境记录 → 实验矩阵 → 交错执行 → correctness gate →
raw.csv / summary.csv / 图。

运行方式：
    python -m benchmarks.benchmark
"""

from __future__ import annotations

import csv
import os
import platform
import subprocess
import sys

import cryptography

from . import config, generators, plots, runners, statistics

RAW_COLUMNS = [
    "algorithm", "N", "r", "ratio", "case", "trial", "seed", "measurement", "correct",
    "cover_count", "header_bytes", "key_material_mean", "key_material_max",
    "setup_ns", "keygen_ns", "cover_ns", "header_encrypt_ns",
    "authorized_recover_ns", "revoked_reject_ns",
]

SUMMARY_COLUMNS = [
    "algorithm", "N", "r", "ratio", "case", "trials",
    "cover_count_mean", "cover_count_median", "cover_count_std",
    "header_bytes_mean", "header_bytes_median", "header_bytes_std",
    "key_material_mean_mean", "key_material_max_mean",
    "setup_ns_mean", "setup_ns_median",
    "keygen_ns_mean", "keygen_ns_median",
    "cover_ns_mean", "cover_ns_median",
    "header_encrypt_ns_mean", "header_encrypt_ns_median",
    "authorized_recover_ns_mean", "authorized_recover_ns_median",
    "revoked_reject_ns_mean", "revoked_reject_ns_median",
]


def record_environment() -> dict:
    """记录实验环境（OS/Python/cryptography/CPU/RAM/commit SHA）。"""
    env = {
        "os": f"{platform.system()} {platform.release()}",
        "python": sys.version.split()[0],
        "cryptography": cryptography.__version__,
        "cpu_count": os.cpu_count(),
        "commit_sha": _git_sha(),
    }
    try:
        import psutil

        vm = psutil.virtual_memory()
        env["ram_total_gb"] = round(vm.total / (1024 ** 3), 1)
    except ImportError:
        env["ram_total_gb"] = "unknown"
    return env


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def _write_raw_csv(rows: list[dict], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "raw.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ("" if row.get(k) is None else row.get(k)) for k in RAW_COLUMNS})
    return path


def _write_summary_csv(summary: list[dict], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "summary.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        for row in summary:
            writer.writerow({k: ("" if row.get(k) is None else row.get(k)) for k in SUMMARY_COLUMNS})
    return path


def run_benchmark(
    output_dir: str = "benchmarks/results",
    n_list: list[int] | None = None,
    warmup_override: int | None = None,
    measurement_override: int | None = None,
) -> dict:
    """执行完整 benchmark，返回 {"env", "rows", "summary", "figures"}。"""
    n_list = n_list or config.N_LIST

    env = record_environment()
    rows: list[dict] = []
    order = ["CS", "SD"]  # 交错执行：偶数 trial CS→SD，奇数 SD→CS

    for N in n_list:
        # v1.2：每 N 用分档 (warmup, measurement)；override 可强制覆盖
        warmup, measurement = config.timing_for(N)
        if warmup_override is not None:
            warmup = warmup_override
        if measurement_override is not None:
            measurement = measurement_override

        for ratio_label, ratio in config.REVOCATION_RATIOS:
            r = config.compute_r(N, ratio)

            # Case A：随机撤销（20 trials，每 trial 不同 seed）
            for trial in range(config.RANDOM_TRIALS):
                seed = config.BASE_SEED + trial
                R = generators.random_revoked(N, r, seed)
                K = os.urandom(config.SESSION_KEY_LEN)
                algo_order = order if trial % 2 == 0 else order[::-1]
                for algo in algo_order:
                    result = runners.run_trial(algo, N, R, K, warmup, measurement)
                    rows.append({
                        "algorithm": algo, "N": N, "r": r, "ratio": ratio_label,
                        "case": "random", "trial": trial, "seed": seed,
                        "measurement": measurement, **result,
                    })

            # Case B/C/D：结构化撤销（10 trials，R 确定性，重复测量 timing）
            if r == 0:
                continue  # r=0 时 R=∅，结构化无意义
            for case_name, gen in [
                ("contiguous", generators.contiguous_revoked),
                ("uniform", generators.uniform_revoked),
                ("clustered", generators.clustered_revoked),
            ]:
                R = gen(N, r)
                for trial in range(config.STRUCTURED_TRIALS):
                    K = os.urandom(config.SESSION_KEY_LEN)
                    algo_order = order if trial % 2 == 0 else order[::-1]
                    for algo in algo_order:
                        result = runners.run_trial(algo, N, R, K, warmup, measurement)
                        rows.append({
                            "algorithm": algo, "N": N, "r": r, "ratio": ratio_label,
                            "case": case_name, "trial": trial,
                            "seed": config.BASE_SEED,
                            "measurement": measurement, **result,
                        })

    raw_path = _write_raw_csv(rows, output_dir)
    summary = statistics.aggregate(rows, ["algorithm", "N", "r", "ratio", "case"])
    summary_path = _write_summary_csv(summary, output_dir)
    figures = plots.generate_figures(summary, os.path.join(output_dir, "figures"))

    return {
        "env": env,
        "rows": rows,
        "summary": summary,
        "raw_path": raw_path,
        "summary_path": summary_path,
        "figures": figures,
    }


def main() -> None:
    result = run_benchmark()
    print("=== Benchmark 环境 ===")
    for k, v in result["env"].items():
        print(f"  {k}: {v}")
    print(f"=== 结果 ===")
    print(f"  raw.csv:     {result['raw_path']} ({len(result['rows'])} rows)")
    print(f"  summary.csv: {result['summary_path']} ({len(result['summary'])} rows)")
    print(f"  figures:     {len(result['figures'])} 张")
    print("=== 完成 ===")


if __name__ == "__main__":
    main()
