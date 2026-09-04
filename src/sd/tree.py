"""SD 满二叉树结构（1-based heap 编号）—— NNL01 §3.2。

与论文一致：接收者作为满二叉树的叶子，N = 2^h。
明确区分三类 ID：
- user_id：对外用户编号，1-based（u1..uN）
- leaf_id：叶子节点编号，heap 编号 v_N..v_{2N-1}
- node_id：树中任意节点编号，v_1..v_{2N-1}（根 v_1）
"""

from __future__ import annotations


class SubsetDifferenceTree:
    def __init__(self, n: int):
        if n < 1 or (n & (n - 1)) != 0:
            raise ValueError(f"N 必须是 2 的幂，得到 {n}")
        self.N = n
        self.h = n.bit_length() - 1  # log2(N)
        self.node_count = 2 * n - 1

    @property
    def root(self) -> int:
        return 1

    def is_node(self, i: int) -> bool:
        return 1 <= i <= self.node_count

    def is_leaf(self, i: int) -> bool:
        return self.N <= i <= self.node_count

    def is_internal(self, i: int) -> bool:
        return 1 <= i < self.N

    def parent(self, i: int) -> int:
        return i // 2

    def left_child(self, i: int) -> int:
        return 2 * i

    def right_child(self, i: int) -> int:
        return 2 * i + 1

    def children(self, i: int) -> list[int]:
        return [c for c in (2 * i, 2 * i + 1) if self.is_node(c)]

    def leaf_of_user(self, user_id: int) -> int:
        """用户 user_id（1-based，1..N）对应的叶子节点编号。"""
        if not 1 <= user_id <= self.N:
            raise ValueError(f"用户 id 越界：{user_id}（范围 1..{self.N}）")
        return self.N + user_id - 1

    def user_of_leaf(self, leaf: int) -> int:
        """叶子节点对应的用户 id（1-based）。"""
        if not self.is_leaf(leaf):
            raise ValueError(f"{leaf} 不是叶子节点")
        return leaf - self.N + 1

    def ancestors(self, node: int) -> list[int]:
        """从 node 到根（含两端）的祖先链。"""
        if not self.is_node(node):
            raise ValueError(f"节点越界：{node}")
        path = []
        i = node
        while i >= 1:
            path.append(i)
            if i == 1:
                break
            i //= 2
        return path

    def is_ancestor(self, a: int, b: int) -> bool:
        """v_a 是否为 v_b 的祖先（含自身）。"""
        while b >= a:
            if b == a:
                return True
            b //= 2
        return False

    def depth(self, node: int) -> int:
        return node.bit_length() - 1

    def subtree_leaf_range(self, node: int) -> tuple[int, int]:
        """以 node 为根的子树的叶子编号区间 [left, right]（含）。"""
        left = node
        while left < self.N:
            left = 2 * left
        right = node
        while right < self.N:
            right = 2 * right + 1
        return left, right

    def subtree_leaves(self, node: int) -> list[int]:
        """以 node 为根的子树的全部叶子节点编号。"""
        left, right = self.subtree_leaf_range(node)
        return list(range(left, right + 1))

    def subtree_users(self, node: int) -> list[int]:
        """以 node 为根的子树的全部用户 id（1-based）。"""
        left, right = self.subtree_leaf_range(node)
        return list(range(left - self.N + 1, right - self.N + 2))

    def lca(self, a: int, b: int) -> int:
        """最低公共祖先（LCA）。"""
        a_ancestors = set(self.ancestors(a))
        node = b
        while node >= 1:
            if node in a_ancestors:
                return node
            node = self.parent(node)
        return self.root
