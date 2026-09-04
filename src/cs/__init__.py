"""Complete Subtree (CS) 广播加密 — NNL01 Section 3.1 的 PAPER-FAITHFUL 实现。

分层：
- tree.py          满二叉树结构（纯结构，无密码学）
- crypto.py        密码原语（secrets 随机 + AES-256-GCM，ENGINEERING ADAPTATION）
- keys.py          Setup / KeyGen（密钥生成与分配）
- cover.py         ST(R) / Cover（覆盖算法）
- encrypt.py       Encrypt / Decrypt（会话密钥的广播加密与恢复）
- serialization.py header 序列化
"""

from .tree import CompleteSubtreeTree
from .crypto import random_key
from .keys import setup, keygen
from .cover import cover, steiner_tree
from .encrypt import encrypt_session_key, decrypt_session_key
from .serialization import serialize_header, deserialize_header

__all__ = [
    "CompleteSubtreeTree",
    "random_key",
    "setup",
    "keygen",
    "cover",
    "steiner_tree",
    "encrypt_session_key",
    "decrypt_session_key",
    "serialize_header",
    "deserialize_header",
]
