"""CS 广播加密可视化辅助（纯函数，可被 pytest 测试）。

职责：
- 把 CompleteSubtreeTree + cover() 结果映射为 graphviz DOT（树 + 高亮）；
- correctness 验证（union / disjoint / 不含 R）；
- 密钥安全显示（指纹，不泄露明文）。
"""

from __future__ import annotations

import hashlib

from src.cs.tree import CompleteSubtreeTree


def fingerprint(key: bytes) -> str:
    """密钥的 SHA-256 指纹（前 8 个 hex 字符），用于安全显示。"""
    return hashlib.sha256(key).hexdigest()[:8]


def hidden_key(key: bytes) -> str:
    """密钥的安全显示：绝不显示明文，只显示 [HIDDEN] 与指纹。"""
    return f"[HIDDEN] · sha256:{fingerprint(key)}"


def descendants(tree: CompleteSubtreeTree, node: int) -> set[int]:
    """node 的所有后代（不含 node 本身）。"""
    result: set[int] = set()
    stack = [node]
    while stack:
        cur = stack.pop()
        for c in tree.children(cur):
            result.add(c)
            stack.append(c)
    return result


def tree_to_dot(
    tree: CompleteSubtreeTree,
    revoked_users: set[int] | None = None,
    path_nodes: set[int] | None = None,
    cover_roots: list[int] | None = None,
) -> str:
    """生成满二叉树的 graphviz DOT。

    高亮规则：
    - cover root：深绿（表示「这棵子树被 cover 选中」）
    - cover root 的子树内部：浅绿
    - 撤销用户叶子：红
    - KeyGen 根到叶路径：蓝
    - 其余：默认

    叶子节点显示「用户编号 u_j + 节点编号 v_i」，内部节点显示「节点编号 v_i」。
    """
    revoked_users = revoked_users or set()
    path_nodes = path_nodes or set()
    cover_roots = list(cover_roots or [])

    cover_subtree: set[int] = set()
    for root in cover_roots:
        cover_subtree.add(root)
        cover_subtree.update(descendants(tree, root))

    lines = [
        "digraph G {",
        "  rankdir=TB;",
        '  node [shape=circle, fixedsize=true, width=0.5, height=0.5, fontsize=11];',
    ]

    for node in range(1, tree.node_count + 1):
        attrs: list[str] = []
        if node in cover_roots:
            attrs += ['style=filled', 'fillcolor="#4CAF50"', 'color="#2E7D32"', "penwidth=2"]
        elif node in cover_subtree:
            attrs += ['style=filled', 'fillcolor="#C8E6C9"', 'color="#2E7D32"']
        elif tree.is_leaf(node) and tree.user_of_leaf(node) in revoked_users:
            attrs += ['style=filled', 'fillcolor="#EF9A9A"', 'color="#C62828"', "penwidth=2"]
        elif node in path_nodes:
            attrs += ['style=filled', 'fillcolor="#90CAF9"', 'color="#1565C0"']

        if tree.is_leaf(node):
            label = f"u{tree.user_of_leaf(node)}\\nv{node}"
        else:
            label = f"v{node}"
        lines.append(f'  {node} [label="{label}" {" ".join(attrs)}];')

    for node in range(1, tree.node_count + 1):
        for child in tree.children(node):
            lines.append(f"  {node} -> {child};")

    lines.append("}")
    return "\n".join(lines)


def verify_cover(
    tree: CompleteSubtreeTree, cover_roots: list[int], revoked_users: set[int]
) -> dict:
    """correctness 验证：union(Cover)=N\\R、Cover∩R=∅、pairwise disjoint。"""
    covered: set[int] = set()
    for root in cover_roots:
        covered.update(tree.users_in_subtree(root))

    all_users = set(range(1, tree.N + 1))
    union_ok = covered == all_users - revoked_users
    no_revoked_ok = covered.isdisjoint(revoked_users)
    disjoint_ok = (
        sum(len(tree.users_in_subtree(r)) for r in cover_roots) == tree.N - len(revoked_users)
    )

    return {
        "cover_count": len(cover_roots),
        "cover_roots": sorted(cover_roots),
        "covered_users": sorted(covered),
        "union_ok": union_ok,
        "no_revoked_ok": no_revoked_ok,
        "disjoint_ok": disjoint_ok,
        "all_ok": union_ok and no_revoked_ok and disjoint_ok,
    }
