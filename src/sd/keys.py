"""Setup / KeyGen：SD 的 label 分配 —— NNL01 §3.2。

KeyGen 返回用户的结构化 key material：
{
    "labels": {(subtree_root, hang_node): label_bytes},
    "full_tree_key": bytes,   # G_M(LABEL_root)，对应「无撤销」整棵树
}
其中每个 label 是「挂在用户根到叶路径外侧」的节点在对应子树 T_{subtree_root} 中的 label。
"""

from __future__ import annotations

from .prg import G_L, G_M, G_R, random_label
from .tree import SubsetDifferenceTree


def setup(n: int) -> tuple[SubsetDifferenceTree, dict[int, bytes]]:
    """Setup(N)：为每个内部节点 v_i 生成独立随机 LABEL_i。

    【NNL01 原文】「choose for each v_i corresponding to an internal node a random
    and independent value LABEL_i」。
    返回 (tree, labels)，labels: {内部节点编号 -> label bytes}（节点 1..N-1）。
    """
    tree = SubsetDifferenceTree(n)
    # 内部节点 1..N-1；N=1 时无内部节点，但仍需根 label 作为整棵树 key 来源（退化情况）
    labels = {i: random_label() for i in range(1, max(2, tree.N))}
    return tree, labels


def derive_label(
    tree: SubsetDifferenceTree, labels: dict[int, bytes], subtree_root: int, target: int
) -> bytes:
    """从 LABEL_{subtree_root} 沿 subtree_root→target 路径派生 LABEL_{subtree_root,target}。"""
    seed = labels[subtree_root]
    return _derive_down(tree, seed, subtree_root, target)


def keygen(tree: SubsetDifferenceTree, labels: dict[int, bytes], user_id: int) -> dict:
    """KeyGen(user_id)：返回用户 key material（挂起节点 label + 全树 key）。"""
    leaf = tree.leaf_of_user(user_id)
    path = tree.ancestors(leaf)  # [leaf, ..., root]

    material_labels: dict[tuple[int, int], bytes] = {}

    for subtree_root in path:
        if subtree_root == leaf:
            continue  # leaf 无子树
        # 子树 T_{subtree_root} 的挂起节点：subtree_root→leaf 路径上每步的「非路径孩子」
        cur = subtree_root
        while cur != leaf:
            nxt = _child_on_path(tree, cur, leaf)
            hang = _other_child(tree, cur, nxt)
            material_labels[(subtree_root, hang)] = derive_label(tree, labels, subtree_root, hang)
            cur = nxt

    full_tree_key = G_M(labels[tree.root])

    return {"labels": material_labels, "full_tree_key": full_tree_key}


def _derive_down(
    tree: SubsetDifferenceTree, start_label: bytes, from_node: int, to_node: int
) -> bytes:
    """从 from_node 的 label 沿 from_node→to_node 路径派生 to_node 的 label。"""
    seed = start_label
    cur = from_node
    while cur != to_node:
        nxt = _child_on_path(tree, cur, to_node)
        if nxt == tree.left_child(cur):
            seed = G_L(seed)
        else:
            seed = G_R(seed)
        cur = nxt
    return seed


def _child_on_path(tree: SubsetDifferenceTree, cur: int, target: int) -> int:
    """cur 的孩子中，是 target 祖先的那个（即路径下一个节点）。"""
    for c in tree.children(cur):
        if tree.is_ancestor(c, target):
            return c
    raise ValueError(f"{cur} 不在 {target} 的路径上")


def _other_child(tree: SubsetDifferenceTree, cur: int, child: int) -> int:
    """cur 的另一个孩子（非 child）。"""
    for c in tree.children(cur):
        if c != child:
            return c
    raise ValueError(f"{cur} 无其他孩子")
