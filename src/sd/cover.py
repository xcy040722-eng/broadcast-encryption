"""SD Cover 算法 —— NNL01 §3.2（迭代法 Step 1-3）。

返回 cover = [(i, j), ...]，每个 (i, j) 表示 S_{ij} = (v_i 子树) \\ (v_j 子树)。
j = None 表示整棵树（「无撤销」特殊 subset）。
"""

from __future__ import annotations

from .tree import SubsetDifferenceTree


def sd_cover(tree: SubsetDifferenceTree, revoked_user_ids: set[int]) -> list[tuple[int, int | None]]:
    if len(revoked_user_ids) == 0:
        # R=∅：整棵树（特殊 subset，j=None）
        return [(tree.root, None)]

    # 1) ST(R)：每个撤销叶子到根的路径并集
    st: set[int] = set()
    for uid in revoked_user_ids:
        leaf = tree.leaf_of_user(uid)
        st.update(tree.ancestors(leaf))

    T: set[int] = set(st)
    cover: list[tuple[int, int | None]] = []

    # 2) 迭代直到 T 只剩一个节点
    while len(T) > 1:
        leaves = [n for n in T if not any(c in T for c in tree.children(n))]

        if len(leaves) == 1:
            # 原文 step 1 括号的特殊分支：单叶子
            v_leaf = leaves[0]
            cover.append((tree.root, v_leaf))
            T = {tree.root}
            break

        # 选两个叶子，其 LCA 的子树内无其他 T 叶子
        v_i, v_j, v = _find_pair(tree, T, leaves)
        c1, c2 = tree.children(v)
        # 原文 step 1：v_l 是 v_i 的祖先侧，v_k 是 v_j 的祖先侧
        if tree.is_ancestor(c1, v_i):
            v_l, v_k = c1, c2
        else:
            v_l, v_k = c2, c1

        # 原文 step 2
        if v_l != v_i:
            cover.append((v_l, v_i))
        if v_k != v_j:
            cover.append((v_k, v_j))

        # 原文 step 3：删除 v 的所有后代
        T.difference_update(_descendants(tree, v))

    return cover


def _find_pair(
    tree: SubsetDifferenceTree, T: set[int], leaves: list[int]
) -> tuple[int, int, int]:
    """找两个叶子 (v_i, v_j)，其 LCA v 的子树内恰好 2 个 T 叶子。返回 (v_i, v_j, v)。"""
    best: tuple[int, int, int] | None = None
    for idx in range(len(leaves)):
        for jdx in range(idx + 1, len(leaves)):
            a, b = leaves[idx], leaves[jdx]
            v = tree.lca(a, b)
            sub = [l for l in leaves if tree.is_ancestor(v, l)]
            if len(sub) == 2:
                if best is None or tree.depth(v) > tree.depth(best[2]):
                    best = (a, b, v)
    if best is None:
        raise ValueError("无法找到叶子对")
    return best


def _descendants(tree: SubsetDifferenceTree, v: int) -> set[int]:
    """v 的所有后代（不含 v 本身）。"""
    result: set[int] = set()
    stack = [v]
    while stack:
        node = stack.pop()
        for c in tree.children(node):
            result.add(c)
            stack.append(c)
    return result
