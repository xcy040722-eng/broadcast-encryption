"""Benchmark 配置（实验矩阵、seed、timing 参数）。"""

# 第一阶段用户规模 N = 2^3 ... 2^10
N_LIST = [8, 16, 32, 64, 128, 256, 512, 1024]

# 撤销比例 ρ（label, ratio）。ratio=None 表示 r=1（单用户撤销）。
REVOCATION_RATIOS = [
    ("zero", 0.0),      # r = 0（无撤销）
    ("single", None),   # r = 1（单用户撤销）
    ("0.01", 0.01),
    ("0.05", 0.05),
    ("0.10", 0.10),
    ("0.25", 0.25),
    ("0.50", 0.50),
]

# 固定随机种子（可复现）
BASE_SEED = 20260904

# trial 数
RANDOM_TRIALS = 20
STRUCTURED_TRIALS = 10

# v1.2：measurement budget 分档（基于 pilot 实测 SD KeyGen 成本）。
# 原则：单次操作成本随 N 增长（SD KeyGen 尤其昂贵，N=1024 时 ~0.88s/次），
#       因此 measurement 次数随 N 反比降低，使每个 N 的测量阶段总耗时可控。
# 每档为 (warmup, measurement)；raw.csv 记录实际 measurement。
# 小 N（≤128）保持 measurement=100 的高精度；大 N 降低重复次数。
TIMING_PROFILE = {
    8: (5, 100),
    16: (5, 100),
    32: (5, 100),
    64: (5, 100),
    128: (5, 100),
    256: (5, 30),
    512: (3, 10),
    1024: (2, 3),
}

# 会话密钥长度（字节）
SESSION_KEY_LEN = 32


def timing_for(n: int) -> tuple[int, int]:
    """返回 N 对应的 (warmup, measurement)。未列出的 N 回退到最近 2 的幂档位。"""
    if n in TIMING_PROFILE:
        return TIMING_PROFILE[n]
    nearest = 1 << (n.bit_length() - 1)
    return TIMING_PROFILE.get(nearest, (5, 100))


def compute_r(n: int, ratio) -> int:
    """由 (N, ρ) 计算整数 r，满足 1 <= r < N（r=0 单独处理）。"""
    if ratio is None:  # single revoke
        return 1 if n > 1 else 0
    if ratio == 0.0:  # zero
        return 0
    r = round(ratio * n)
    return max(1, min(r, n - 1))
