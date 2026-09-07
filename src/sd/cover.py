"""SD Cover 算法 —— NNL01 §3.2。

返回 cover = [(i, j), ...]，每个 (i, j) 表示 S_{ij} = (v_i 子树) \\ (v_j 子树)。
j = None 表示整棵树（「无撤销」特殊 subset）。

实现采用论文给出的 chain 等价描述（而非迭代法 Step 1-3）：
ST(R) 中 outdegree-1 的节点连成 maximal chains，每条 chain [v_top, ..., v_bottom]
（v_top 为 outdegree-1 且其父非 outdegree-1；v_bottom 为 leaf 或 outdegree-2 节点）
贡献一个 S_{top, bottom}。这是迭代法的等价表述，复杂度 O(r·log N)。
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

    # 2) outdegree-1 节点（在 ST 中恰好一个孩子）
    outdegree1: set[int] = set()
    for node in st:
        kids = [c for c in tree.children(node) if c in st]
        if len(kids) == 1:
            outdegree1.add(node)

    # 3) 找 chains：从 chain 顶（父非 outdegree-1）沿唯一 ST 孩子走到 chain 底
    cover: list[tuple[int, int | None]] = []
    for top in sorted(outdegree1):
        parent = tree.parent(top) if top != tree.root else 0
        if parent in outdegree1:
            continue  # 不是 chain 顶

        cur = top
        while cur in outdegree1:
            kids = [c for c in tree.children(cur) if c in st]
            cur = kids[0]
        bottom = cur
        cover.append((top, bottom))

    return cover


# ---- reference（旧迭代法，仅用于 differential test）----


def _sd_cover_bruteforce(
    tree: SubsetDifferenceTree, revoked_user_ids: set[int]
) -> list[tuple[int, int | None]]:
    """迭代法 Step 1-3 的直译实现（O(r^4)，仅作 reference 对照）。"""
    if len(revoked_user_ids) == 0:
        return [(tree.root, None)]

    st: set[int] = set()
    for uid in revoked_user_ids:
        leaf = tree.leaf_of_user(uid)
        st.update(tree.ancestors(leaf))

    T: set[int] = set(st)
    cover: list[tuple[int, int | None]] = []

    while len(T) > 1:
        leaves = [n for n in T if not any(c in T for c in tree.children(n))]

        if len(leaves) == 1:
            v_leaf = leaves[0]
            cover.append((tree.root, v_leaf))
            T = {tree.root}
            break

        v_i, v_j, v = _find_pair(tree, T, leaves)
        c1, c2 = tree.children(v)
        if tree.is_ancestor(c1, v_i):
            v_l, v_k = c1, c2
        else:
            v_l, v_k = c2, c1

        if v_l != v_i:
            cover.append((v_l, v_i))
        if v_k != v_j:
            cover.append((v_k, v_j))

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
