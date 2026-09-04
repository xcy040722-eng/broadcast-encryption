"""Setup / KeyGen 测试。"""

import pytest

from src.cs.keys import keygen, setup


def test_setup_creates_all_node_keys():
    tree, node_keys = setup(8)
    assert tree.node_count == 15
    assert len(node_keys) == 15
    assert set(node_keys.keys()) == set(range(1, 16))


def test_node_keys_are_32_bytes():
    _, node_keys = setup(8)
    for k in node_keys.values():
        assert len(k) == 32


def test_node_keys_independent():
    _, node_keys = setup(8)
    values = list(node_keys.values())
    assert len(set(values)) == len(values)  # 两两不同（独立随机）


def test_keygen_returns_path_keys():
    tree, node_keys = setup(8)
    u1 = keygen(tree, node_keys, 1)  # 叶子 v8，路径 8,4,2,1
    assert set(u1.keys()) == {8, 4, 2, 1}
    assert len(u1) == tree.h + 1 == 4


def test_keygen_values_match_node_keys():
    tree, node_keys = setup(8)
    u4 = keygen(tree, node_keys, 4)  # 叶子 v11，路径 11,5,2,1
    for node, k in u4.items():
        assert node_keys[node] == k


def test_different_users_different_paths():
    tree, node_keys = setup(8)
    u1 = keygen(tree, node_keys, 1)
    u4 = keygen(tree, node_keys, 4)
    u8 = keygen(tree, node_keys, 8)
    assert set(u1.keys()) != set(u4.keys())
    assert set(u1.keys()) != set(u8.keys())
    # 所有用户共享根密钥 L1
    assert 1 in u1 and 1 in u4 and 1 in u8


def test_keygen_rejects_invalid_user():
    tree, node_keys = setup(8)
    with pytest.raises(ValueError):
        keygen(tree, node_keys, 0)
    with pytest.raises(ValueError):
        keygen(tree, node_keys, 9)
