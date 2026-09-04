"""Subset Difference (SD) 广播加密 —— NNL01 §3.2 实现。

与 src/cs/（Complete Subtree）保持独立。仅实现会话密钥的广播加密，
不实现文件 body 加密。
"""

from .tree import SubsetDifferenceTree
from .prg import G_L, G_R, G_M, random_label
from .keys import setup, keygen, derive_label
from .cover import sd_cover
from .encrypt import (
    subset_key,
    encrypt_session_key,
    decrypt_session_key,
    derive_user_subset_key,
)
from .serialization import (
    VERSION,
    InvalidHeaderError,
    serialize_header,
    deserialize_header,
)

__all__ = [
    "SubsetDifferenceTree",
    "G_L",
    "G_R",
    "G_M",
    "random_label",
    "setup",
    "keygen",
    "derive_label",
    "sd_cover",
    "subset_key",
    "encrypt_session_key",
    "decrypt_session_key",
    "derive_user_subset_key",
    "VERSION",
    "InvalidHeaderError",
    "serialize_header",
    "deserialize_header",
]
