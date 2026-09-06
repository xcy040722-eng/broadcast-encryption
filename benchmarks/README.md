# CS vs SD Benchmark Harness

对 NNL01 的 Complete Subtree（CS）与 Subset Difference（SD）两种广播加密机制做同条件对比。

## 目录结构

```
benchmarks/
├── README.md        # 本说明
├── config.py        # 实验矩阵、seed、timing 参数
├── generators.py    # 撤销集合生成（随机 + 连续/均匀/聚集）
├── runners.py       # 执行 + 计时 + correctness gate
├── statistics.py    # raw → summary 聚合
├── plots.py         # 6 张核心图
├── benchmark.py     # 主入口（环境记录 + 编排 + CSV 输出）
└── results/         # 输出（raw.csv / summary.csv / figures/）
```

## 运行

```bash
python -m benchmarks.benchmark
```

第一阶段默认 `N = 2^3 ... 2^10`（见 `config.N_LIST`）。

## 实验矩阵

- **N**：8, 16, 32, 64, 128, 256, 512, 1024
- **撤销比例 ρ**：0、1/N、0.01、0.05、0.10、0.25、0.50
- **Case A 随机**：20 trials，seed = 20260904 + trial（可复现）
- **Case B/C/D 结构化**：连续 / 均匀 / 聚集，各 10 trials（R 确定性，重复测 timing）

## Correctness Gate

每个 trial 进入统计前必须通过（否则 `assert` 失败，benchmark 中止）：

- `union(Cover) == N \ R`
- `Cover ∩ R == ∅`
- Cover entries 两两不重叠（子树大小之和 == N − r）
- SD 额外：`|Cover| <= 2r − 1`（非空 R）
- authorized 用户恢复 K == 原 K；revoked 用户恢复 == 失败

## 公平性

- CS/SD 使用**同一个 R**（不各自随机生成）
- 相同 K 长度（32 字节）、相同 AES-GCM、相同 seed、相同 trial 数
- 交错执行（偶数 trial CS→SD，奇数 SD→CS），避免顺序偏差
- 计时用 `time.perf_counter_ns()`，warm-up 10 + measurement 100

## 输出

- `raw.csv`：每个 trial 一行（含 cover_count / header_bytes / key_material / 各阶段 ns）
- `summary.csv`：按 (algorithm, N, r, ratio, case) 聚合（mean/median/std）
- `figures/`：6 张图（Cover vs N、Cover vs r、Header entries、Header bytes、Cover time、Key material）

## 边界说明

- `r=0`（ρ=0）只跑随机 case（R=∅），跳过结构化 case。
- `clustered` 要求 `r <= N/2`（集中在右半子树）；超出时该 case 会 assert 失败（第一阶段比例均 ≤ 0.50，不会触发）。
- 大 N 下 measurement 可降低（结果需记录）。

## 限制

本 harness 只比较 CS/SD 的广播加密机制本身（Cover / Header / Key material / 核心运行时间），**不测** AES-GCM 本身、JSON 序列化性能、文件加密、磁盘 I/O、并发。
