"""树结构测试。"""

import pytest

from src.cs.tree import CompleteSubtreeTree


def test_construction_n8():
    t = CompleteSubtreeTree(8)
    assert t.N == 8
    assert t.h == 3
    assert t.node_count == 15
    assert t.root == 1


@pytest.mark.parametrize("bad", [0, -1, 3, 5, 6, 7, 10])
def test_invalid_n(bad):
    with pytest.raises(ValueError):
        CompleteSubtreeTree(bad)


def test_leaf_and_internal():
    t = CompleteSubtreeTree(8)
    assert t.is_leaf(8)
    assert t.is_leaf(15)
    assert not t.is_leaf(1)
    assert not t.is_leaf(4)
    assert t.is_node(1)
    assert t.is_node(15)
    assert not t.is_node(16)


def test_parent_child():
    t = CompleteSubtreeTree(8)
    assert t.left(1) == 2
    assert t.right(1) == 3
    assert t.parent(4) == 2
    assert t.parent(5) == 2
    assert t.parent(15) == 7
    assert t.children(1) == [2, 3]
    assert t.children(8) == []  # 叶子无孩子


def test_leaf_user_mapping():
    t = CompleteSubtreeTree(8)
    assert t.leaf_of_user(1) == 8
    assert t.leaf_of_user(8) == 15
    assert t.user_of_leaf(8) == 1
    assert t.user_of_leaf(15) == 8
    with pytest.raises(ValueError):
        t.leaf_of_user(0)
    with pytest.raises(ValueError):
        t.leaf_of_user(9)
    with pytest.raises(ValueError):
        t.user_of_leaf(4)


def test_ancestors():
    t = CompleteSubtreeTree(8)
    assert t.ancestors(11) == [11, 5, 2, 1]
    assert t.ancestors(1) == [1]


def test_is_ancestor():
    t = CompleteSubtreeTree(8)
    assert t.is_ancestor(1, 11)
    assert t.is_ancestor(2, 11)
    assert t.is_ancestor(5, 11)
    assert t.is_ancestor(11, 11)  # 自身
    assert not t.is_ancestor(3, 11)
    assert not t.is_ancestor(11, 5)


def test_users_in_subtree():
    t = CompleteSubtreeTree(8)
    assert t.users_in_subtree(1) == list(range(1, 9))
    assert t.users_in_subtree(3) == [5, 6, 7, 8]
    assert t.users_in_subtree(4) == [1, 2]
    assert t.users_in_subtree(10) == [3]
    assert t.users_in_subtree(8) == [1]
