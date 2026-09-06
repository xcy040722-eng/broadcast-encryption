"""统计聚合：raw rows → summary。"""

from __future__ import annotations

import statistics

# 需要聚合的数值列
METRIC_COLUMNS = [
    "cover_count",
    "header_bytes",
    "key_material_mean",
    "key_material_max",
    "setup_ns",
    "keygen_ns",
    "cover_ns",
    "header_encrypt_ns",
    "authorized_recover_ns",
    "revoked_reject_ns",
]


def aggregate(rows: list[dict], group_keys: list[str]) -> list[dict]:
    """按 group_keys 分组，对 METRIC_COLUMNS 计算 mean/median/std。"""
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = tuple(row[k] for k in group_keys)
        groups.setdefault(key, []).append(row)

    summary: list[dict] = []
    for key, group in groups.items():
        entry = dict(zip(group_keys, key))
        entry["trials"] = len(group)
        for col in METRIC_COLUMNS:
            vals = [r[col] for r in group if r.get(col) is not None]
            if not vals:
                entry[f"{col}_mean"] = None
                entry[f"{col}_median"] = None
                entry[f"{col}_std"] = None
                continue
            entry[f"{col}_mean"] = statistics.mean(vals)
            entry[f"{col}_median"] = statistics.median(vals)
            entry[f"{col}_std"] = statistics.stdev(vals) if len(vals) > 1 else 0.0
        summary.append(entry)
    return summary
