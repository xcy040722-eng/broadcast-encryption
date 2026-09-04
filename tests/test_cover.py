"""Cover / ST(R) 测试。"""

import itertools

from src.cs.cover import cover, steiner_tree
from src.cs.keys import setup


def covered_users(tree, cover_roots):
    covered = set()
    for root in cover_roots:
        covered.update(tree.users_in_subtree(root))
    return covered


def test_cover_r_u3():
    tree, _ = setup(8)
    # 撤销 u3（叶子 v10），对应 docs/cs-specification.md 10.3
    assert cover(tree, {3}) == [3, 4, 11]


def test_cover_r_u3_u5():
    tree, _ = setup(8)
    # 撤销 u3、u5（叶子 v10、v12），对应 10.4
    assert cover(tree, {3, 5}) == [4, 7, 11, 13]


def test_cover_empty_revoked():
    tree, _ = setup(8)
    assert cover(tree, set()) == [1]


def test_cover_all_revoked():
    tree, _ = setup(8)
    assert cover(tree, set(range(1, 9))) == []


def test_steiner_tree():
    tree, _ = setup(8)
    st = steiner_tree(tree, {3})
    assert st == {1, 2, 5, 10}


def test_cover_exactly_partitions():
    """覆盖的用户集合恰等于 N\\R，不遗漏、不重复、不含撤销用户。"""
    for N in [1, 2, 4, 8, 16]:
        tree, _ = setup(N)
        all_users = set(range(1, N + 1))
        for r in range(N + 1):
            for R in itertools.combinations(range(1, N + 1), r):
                R = set(R)
                roots = cover(tree, R)
                covered = covered_users(tree, roots)
                assert covered == all_users - R


def test_cover_subtrees_disjoint():
    """各覆盖子树叶子集合互不重叠：叶子数之和 == 非撤销用户数（M1）。"""
    for N in [1, 2, 4, 8, 16]:
        tree, _ = setup(N)
        for r in range(N + 1):
            for R in itertools.combinations(range(1, N + 1), r):
                R = set(R)
                roots = cover(tree, R)
                total = sum(len(tree.users_in_subtree(root)) for root in roots)
                assert total == N - len(R)
