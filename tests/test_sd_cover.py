"""SD cover 优化（chain 方法）的正确性测试。"""

import itertools

from src.sd import setup, sd_cover
from src.sd.cover import _sd_cover_bruteforce


def _subset_users(tree, i, j):
    if j is None:
        return set(tree.subtree_users(i))
    return set(tree.subtree_users(i)) - set(tree.subtree_users(j))


def _covered_users(tree, cover):
    covered = set()
    for (i, j) in cover:
        covered.update(_subset_users(tree, i, j))
    return covered


def test_chain_matches_bruteforce_exhaustive():
    """differential test：N=1..16 全撤销子集，chain 方法与暴力迭代法一致。"""
    for N in [1, 2, 4, 8, 16]:
        tree, _ = setup(N)
        for r in range(N + 1):
            for R in itertools.combinations(range(1, N + 1), r):
                R = set(R)
                assert sorted(sd_cover(tree, R)) == sorted(_sd_cover_bruteforce(tree, R))


def test_known_case_r_u3():
    tree, _ = setup(8)
    assert sd_cover(tree, {3}) == [(1, 10)]


def test_known_case_r_u3_u5():
    tree, _ = setup(8)
    cover = sd_cover(tree, {3, 5})
    assert len(cover) == 2
    assert _covered_users(tree, cover) == {1, 2, 4, 6, 7, 8}


def test_symmetric_left_right_halves():
    """左半撤销 vs 右半撤销：cover 结构对称（S_{1,2} vs S_{1,3}）。"""
    tree, _ = setup(8)
    left = sd_cover(tree, set(range(1, 5)))     # 撤销左半 u1..u4
    right = sd_cover(tree, set(range(5, 9)))    # 撤销右半 u5..u8
    assert left == [(1, 2)]
    assert right == [(1, 3)]
    assert _covered_users(tree, left) == set(range(5, 9))
    assert _covered_users(tree, right) == set(range(1, 5))


def test_various_remaining_leaves():
    """不同 r 的 cover 都满足：union==N\\R、不含 R、两两不重叠、上界。"""
    for N in [8, 16, 32]:
        tree, _ = setup(N)
        for r in [0, 1, 2, 3, N // 4, N // 2, N - 1]:
            R = set(range(1, r + 1))
            cover = sd_cover(tree, R)
            covered = _covered_users(tree, cover)
            assert covered == set(range(1, N + 1)) - R
            assert covered.isdisjoint(R)
            total = sum(len(_subset_users(tree, i, j)) for (i, j) in cover)
            assert total == N - len(R)
            if R:
                assert len(cover) <= 2 * len(R) - 1
