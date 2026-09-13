"""UI 可视化辅助（web/cs_visualize.py 纯函数）的 smoke test。"""

from src.cs import cover, setup
from web.cs_visualize import (
    descendants,
    fingerprint,
    hidden_key,
    tree_to_dot,
    verify_cover,
)


def test_fingerprint_and_hidden_key():
    k = b"x" * 32
    assert len(fingerprint(k)) == 8
    hidden = hidden_key(k)
    assert "[HIDDEN]" in hidden
    # 明文绝不出现
    assert "xxxx" not in hidden


def test_tree_to_dot_contains_all_nodes():
    tree, _ = setup(8)
    dot = tree_to_dot(tree)
    for node in range(1, tree.node_count + 1):
        assert f"{node} [" in dot, f"节点 {node} 不在 DOT 中"
    # 叶子标签含用户编号
    assert "u1" in dot and "u8" in dot


def test_tree_to_dot_highlights_cover_and_revoked():
    tree, _ = setup(8)
    cover_roots = cover(tree, {3, 5})
    assert cover_roots == [4, 7, 11, 13]
    dot = tree_to_dot(tree, revoked_users={3, 5}, cover_roots=cover_roots)
    assert "#4CAF50" in dot  # cover root 深绿
    assert "#EF9A9A" in dot  # 撤销用户红


def test_tree_to_dot_highlight_path():
    tree, _ = setup(8)
    leaf = tree.leaf_of_user(3)
    path = set(tree.ancestors(leaf))
    dot = tree_to_dot(tree, path_nodes=path)
    assert "#90CAF9" in dot  # KeyGen 路径蓝


def test_verify_cover_correctness():
    tree, _ = setup(8)
    for R in [{3}, {3, 5}, set(), set(range(1, 9))]:
        roots = cover(tree, R)
        result = verify_cover(tree, roots, R)
        assert result["all_ok"], f"R={R} 验证失败: {result}"
        assert result["cover_count"] == len(roots)
        assert result["union_ok"] and result["no_revoked_ok"] and result["disjoint_ok"]


def test_descendants():
    tree, _ = setup(8)
    d = descendants(tree, 2)
    assert 4 in d and 5 in d and 8 in d and 11 in d
    assert 2 not in d and 3 not in d
