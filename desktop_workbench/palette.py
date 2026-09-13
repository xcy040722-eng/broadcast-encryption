"""语义配色：颜色由**密码学语义**决定，不做"程序员调试工具"式乱配色。"""

from __future__ import annotations

# 基础层
BG = "#0B1020"
SURFACE = "#111827"
SURFACE2 = "#172033"
BORDER = "#26344A"

TEXT = "#E8EEF8"
MUTED = "#8796AD"

# 语义层（由密码学角色决定）
PUBLIC = "#67B7FF"       # W_i / A / p / y_{j,i} 交叉项 / c_i
SECRET = "#F5B94C"       # y_ii 私钥分量
AUTHORIZED = "#55D68B"   # 授权用户 / 成功
CIPHERTEXT = "#A78BFA"   # 密文分量
RERANDOM = "#A78BFA"     # 重随机化 y_0i / W0
NOISE = "#F28B82"        # 噪声 ẽ
DISABLED = "#3C475A"


def with_alpha(hex_color: str, alpha: float) -> str:
    """把 #RRGGBB 变成 rgba(...) 字符串（供 QColor 使用）。"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
