"""Complete binary tree model for NNL01 Complete Subtree.

The numbering uses a 1-based heap layout:
- root = v1
- children(v_i) = v_(2i), v_(2i+1)
- N = 2^h leaves occupy [N, 2N-1]
- user u_j (1-based) maps to leaf v_(N+j-1)
"""

from __future__ import annotations


class CompleteSubtreeTree:
    """Full binary tree used by the Complete Subtree revocation method."""

    def __init__(self, n: int):
        if n < 1 or (n & (n - 1)) != 0:
            raise ValueError(f"N must be a positive power of two, got {n}")
        self.n = n
        self.height = n.bit_length() - 1
        self.node_count = 2 * n - 1

    @property
    def root(self) -> int:
        return 1

    def is_node(self, node: int) -> bool:
        return 1 <= node <= self.node_count

    def is_leaf(self, node: int) -> bool:
        return self.n <= node <= self.node_count

    def children(self, node: int) -> tuple[int, ...]:
        if not self.is_node(node):
            raise ValueError(f"node out of range: {node}")
        result = tuple(
            child
            for child in (2 * node, 2 * node + 1)
            if self.is_node(child)
        )
        return result

    def parent(self, node: int) -> int | None:
        if not self.is_node(node):
            raise ValueError(f"node out of range: {node}")
        return None if node == self.root else node // 2

    def leaf_of_user(self, user_id: int) -> int:
        if not 1 <= user_id <= self.n:
            raise ValueError(f"user id out of range: {user_id}; expected 1..{self.n}")
        return self.n + user_id - 1

    def user_of_leaf(self, leaf: int) -> int:
        if not self.is_leaf(leaf):
            raise ValueError(f"node {leaf} is not a user leaf")
        return leaf - self.n + 1

    def path_to_root(self, node: int) -> tuple[int, ...]:
        """Return node -> ... -> root, inclusive."""
        if not self.is_node(node):
            raise ValueError(f"node out of range: {node}")
        path: list[int] = []
        current = node
        while True:
            path.append(current)
            if current == self.root:
                return tuple(path)
            current //= 2

    def root_to_user_path(self, user_id: int) -> tuple[int, ...]:
        return tuple(reversed(self.path_to_root(self.leaf_of_user(user_id))))

    def subtree_leaf_range(self, node: int) -> tuple[int, int]:
        if not self.is_node(node):
            raise ValueError(f"node out of range: {node}")
        left = node
        while left < self.n:
            left *= 2
        right = node
        while right < self.n:
            right = right * 2 + 1
        return left, right

    def users_in_subtree(self, node: int) -> tuple[int, ...]:
        left, right = self.subtree_leaf_range(node)
        return tuple(range(left - self.n + 1, right - self.n + 2))
