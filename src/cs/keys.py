"""Setup 与 KeyGen —— NNL01 Section 3.1 的密钥生成与分配。"""

from __future__ import annotations

from .crypto import random_key
from .tree import CompleteSubtreeTree


def setup(n: int) -> tuple[CompleteSubtreeTree, dict[int, bytes]]:
    """Setup(N)：构造满二叉树并为每个节点 v_i 分配独立随机密钥 L_i。

    对应原文「assign an independent and random key L_i to every node v_i」。
    返回 (tree, node_keys)，node_keys: {节点编号 -> 密钥 bytes}。
    """
    tree = CompleteSubtreeTree(n)
    node_keys = {i: random_key() for i in range(1, tree.node_count + 1)}
    return tree, node_keys


def keygen(tree: CompleteSubtreeTree, node_keys: dict[int, bytes], user_id: int) -> dict[int, bytes]:
    """KeyGen(user_id)：返回用户私钥 = 根到叶子路径上所有节点的密钥。

    user_id 为 1-based（1..N）。
    对应原文「Provide every receiver u with the log N + 1 keys associated with
    the nodes along the path from the root to leaf u」。
    返回 {节点编号 -> 密钥 bytes}，共 log2(N)+1 把。
    """
    leaf = tree.leaf_of_user(user_id)
    path_nodes = tree.ancestors(leaf)
    return {i: node_keys[i] for i in path_nodes}
