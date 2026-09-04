"""SD 会话密钥广播加密/恢复 —— NNL01 §3.2 + Section 2.2。

本阶段只实现「会话密钥 K 的广播加密」，不实现文件 body 加密。

【ENGINEERING ADAPTATION】E_L（header 加密会话密钥）用 AES-256-GCM 实例化，
独立于 src/cs/ 的实现。不声称论文规定 AES-GCM。
"""

from __future__ import annotations

import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .keys import derive_label, _derive_down
from .prg import G_M
from .tree import SubsetDifferenceTree

_NONCE_LEN = 12


def subset_key(labels: dict[int, bytes], tree: SubsetDifferenceTree, i: int, j: int | None) -> bytes:
    """S_{ij} 的密钥 L_{ij} = G_M(LABEL_{i,j})；j=None 时即整棵树 key G_M(LABEL_root)。"""
    if j is None:
        return G_M(labels[tree.root])
    return G_M(derive_label(tree, labels, i, j))


def encrypt_session_key(
    labels: dict[int, bytes],
    tree: SubsetDifferenceTree,
    cover: list[tuple[int, int | None]],
    session_key: bytes,
) -> list[tuple[int, int | None, bytes]]:
    """用每个 cover 子集密钥加密会话密钥，构成 header。

    header = [(i, j, E_{L_ij}(K)), ...]；K 只以 AES-GCM 密文形式出现，从不明文存储。
    """
    header = []
    for (i, j) in cover:
        key = subset_key(labels, tree, i, j)
        blob = _encrypt_key(key, session_key)
        header.append((i, j, blob))
    return header


def decrypt_session_key(
    user_material: dict,
    tree: SubsetDifferenceTree,
    header: list[tuple[int, int | None, bytes]],
) -> bytes | None:
    """用户从 header 恢复会话密钥；无法恢复返回 None。"""
    for (i, j, blob) in header:
        key = derive_user_subset_key(user_material, tree, i, j)
        if key is not None:
            try:
                return _decrypt_key(key, blob)
            except InvalidTag:
                return None
    return None


def derive_user_subset_key(
    user_material: dict, tree: SubsetDifferenceTree, i: int, j: int | None
) -> bytes | None:
    """用户 u 从自己的 material 派生 S_{ij} 的密钥；u ∉ S_{ij} 时返回 None。"""
    if j is None:
        return user_material["full_tree_key"]

    for (si, sh), label in user_material["labels"].items():
        if si == i and tree.is_ancestor(sh, j):
            lab_ij = _derive_down(tree, label, sh, j)
            return G_M(lab_ij)
    return None


def _encrypt_key(key: bytes, plaintext: bytes) -> bytes:
    if len(key) != 32:
        raise ValueError("密钥长度必须为 32 字节")
    nonce = secrets.token_bytes(_NONCE_LEN)
    ct = AESGCM(key).encrypt(nonce, plaintext, None)
    return nonce + ct


def _decrypt_key(key: bytes, blob: bytes) -> bytes:
    if len(key) != 32:
        raise ValueError("密钥长度必须为 32 字节")
    if len(blob) < _NONCE_LEN + 16:
        raise ValueError("密文过短")
    nonce = blob[:_NONCE_LEN]
    ct = blob[_NONCE_LEN:]
    return AESGCM(key).decrypt(nonce, ct, None)
