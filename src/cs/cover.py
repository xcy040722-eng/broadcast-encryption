"""ST(R) 与 Cover —— NNL01 Section 3.1 的覆盖算法。"""

from __future__ import annotations

from .tree import CompleteSubtreeTree


def steiner_tree(tree: CompleteSubtreeTree, revoked_user_ids: set[int]) -> set[int]:
    """ST(R)：连接 R 中叶子与根的最小子树的节点集合。"""
    st: set[int] = set()
    for uid in revoked_user_ids:
        leaf = tree.leaf_of_user(uid)
        st.update(tree.ancestors(leaf))
    return st


def cover(tree: CompleteSubtreeTree, revoked_user_ids: set[int]) -> list[int]:
    """返回覆盖 N\\R 的子树根索引列表（升序）。

    revoked_user_ids 为 1-based（1..N）。
    对应原文「all subtrees of the original tree that hang off ST(R)」：
    对 ST(R) 中出度为 1 的节点，其「不在 ST(R) 中」的孩子即悬挂子树根。
    """
    if len(revoked_user_ids) == 0:
        return [tree.root]  # R=∅：整个树覆盖所有用户

    st = steiner_tree(tree, revoked_user_ids)
    roots: list[int] = []
    for node in sorted(st):
        in_st_children = [c for c in tree.children(node) if c in st]
        if len(in_st_children) == 1:
            # 出度 1：唯一「不在 ST」的孩子是悬挂子树根
            for c in tree.children(node):
                if c not in st:
                    roots.append(c)
    return sorted(roots)
