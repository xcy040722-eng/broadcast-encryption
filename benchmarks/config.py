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

# timing 参数
WARMUP = 10
MEASUREMENT = 100

# 会话密钥长度（字节）
SESSION_KEY_LEN = 32


def compute_r(n: int, ratio) -> int:
    """由 (N, ρ) 计算整数 r，满足 1 <= r < N（r=0 单独处理）。"""
    if ratio is None:  # single revoke
        return 1 if n > 1 else 0
    if ratio == 0.0:  # zero
        return 0
    r = round(ratio * n)
    return max(1, min(r, n - 1))
