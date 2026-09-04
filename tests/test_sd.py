"""Subset Difference (SD) 测试 —— NNL01 §3.2。"""

import base64
import json
import secrets

import pytest

from src.sd import (
    G_L,
    G_M,
    G_R,
    InvalidHeaderError,
    SubsetDifferenceTree,
    decrypt_session_key,
    derive_user_subset_key,
    deserialize_header,
    encrypt_session_key,
    keygen,
    random_label,
    sd_cover,
    serialize_header,
    setup,
    subset_key,
)


def _random_subset(n):
    return {u for u in range(1, n + 1) if secrets.randbits(1)}


def _subset_users(tree, i, j):
    if j is None:
        return set(tree.subtree_users(i))
    return set(tree.subtree_users(i)) - set(tree.subtree_users(j))


def _covered_users(tree, cover):
    covered = set()
    for (i, j) in cover:
        covered.update(_subset_users(tree, i, j))
    return covered


# ---- 1/2. tree 结构 + LCA ----


def test_tree_basic():
    t = SubsetDifferenceTree(8)
    assert t.N == 8
    assert t.h == 3
    assert t.node_count == 15
    assert t.root == 1
    assert t.parent(4) == 2
    assert t.left_child(2) == 4
    assert t.right_child(2) == 5
    assert t.is_leaf(8) and t.is_leaf(15)
    assert t.is_internal(1) and t.is_internal(4)
    assert not t.is_internal(8)


def test_tree_ids_distinct():
    t = SubsetDifferenceTree(8)
    # user_id(1-based) -> leaf_id -> node_id 三者区分
    assert t.leaf_of_user(1) == 8
    assert t.leaf_of_user(8) == 15
    assert t.user_of_leaf(8) == 1
    assert t.subtree_users(1) == list(range(1, 9))
    assert t.subtree_users(4) == [1, 2]
    with pytest.raises(ValueError):
        t.leaf_of_user(0)
    with pytest.raises(ValueError):
        t.leaf_of_user(9)


def test_lca():
    t = SubsetDifferenceTree(8)
    assert t.lca(8, 9) == 4
    assert t.lca(8, 10) == 2
    assert t.lca(8, 12) == 1
    assert t.lca(10, 11) == 5
    assert t.lca(8, 8) == 8


# ---- 3. G_L/G_R/G_M 派生 ----


def test_prg_derivation():
    s = random_label()
    assert len(G_L(s)) == 32
    assert len(G_R(s)) == 32
    assert len(G_M(s)) == 32
    # 确定性
    assert G_L(s) == G_L(s)
    # 不同 domain 不同输出
    assert G_L(s) != G_R(s)
    assert G_R(s) != G_M(s)
    # 不同 seed 不同输出
    s2 = random_label()
    assert G_L(s) != G_L(s2)


# ---- 4/5. Setup / KeyGen ----


def test_setup_labels():
    tree, labels = setup(8)
    assert set(labels.keys()) == set(range(1, 8))  # 内部节点 1..7
    for lab in labels.values():
        assert len(lab) == 32


def test_keygen_u3_seven_material():
    tree, labels = setup(8)
    mat = keygen(tree, labels, 3)
    # u3 应获得 6 个 label
    assert len(mat["labels"]) == 6
    assert set(mat["labels"].keys()) == {(1, 3), (1, 4), (1, 11), (2, 4), (2, 11), (5, 11)}
    # 全树 key = G_M(LABEL_root)
    assert mat["full_tree_key"] == G_M(labels[1])
    # 总计 7 个 material
    assert len(mat["labels"]) + 1 == 7


def test_keygen_labels_are_derived():
    tree, labels = setup(8)
    mat = keygen(tree, labels, 3)
    # 每个 label 都应是子树根的派生
    from src.sd import derive_label

    for (si, sh), lab in mat["labels"].items():
        assert lab == derive_label(tree, labels, si, sh)


# ---- 6/7/8/9. Cover 基本场景 ----


def test_cover_r_u3():
    tree, _ = setup(8)
    cover = sd_cover(tree, {3})
    assert len(cover) == 1
    assert cover == [(1, 10)]
    assert _covered_users(tree, cover) == set(range(1, 9)) - {3}


def test_cover_r_u3_u5():
    tree, _ = setup(8)
    cover = sd_cover(tree, {3, 5})
    assert len(cover) == 2
    assert _covered_users(tree, cover) == {1, 2, 4, 6, 7, 8}


def test_cover_empty():
    tree, _ = setup(8)
    cover = sd_cover(tree, set())
    assert cover == [(1, None)]
    assert _covered_users(tree, cover) == set(range(1, 9))


def test_cover_all():
    tree, _ = setup(8)
    cover = sd_cover(tree, set(range(1, 9)))
    assert cover == []
    assert _covered_users(tree, cover) == set()


# ---- 10-13. 随机 + 不重叠 + 不包含撤销 + union ----


def test_random_cover_many():
    for N in [1, 2, 4, 8, 16, 32]:
        tree, _ = setup(N)
        for _ in range(30):
            R = _random_subset(N)
            cover = sd_cover(tree, R)
            covered = _covered_users(tree, cover)
            # union == N\R
            assert covered == set(range(1, N + 1)) - R
            # 不重叠（子树差 disjoint，用户数之和 == 非撤销用户数）
            total = sum(len(_subset_users(tree, i, j)) for (i, j) in cover)
            assert total == N - len(R)
            # 上界（非空 R）
            if R:
                assert len(cover) <= 2 * len(R) - 1


def test_cover_disjoint_and_no_revoked():
    for N in [1, 2, 4, 8]:
        tree, _ = setup(N)
        for r in range(N + 1):
            import itertools

            for R in itertools.combinations(range(1, N + 1), r):
                R = set(R)
                cover = sd_cover(tree, R)
                covered = _covered_users(tree, cover)
                assert covered == set(range(1, N + 1)) - R
                assert covered.isdisjoint(R)  # 不包含撤销用户


# ---- 14/15/16. 加解密 + K 恢复 + 明文不泄露 ----


def test_encrypt_decrypt_recovery():
    for N in [1, 2, 4, 8, 16]:
        tree, labels = setup(N)
        for _ in range(20):
            R = _random_subset(N)
            cover = sd_cover(tree, R)
            K = random_label()
            header = encrypt_session_key(labels, tree, cover, K)
            for u in range(1, N + 1):
                mat = keygen(tree, labels, u)
                recovered = decrypt_session_key(mat, tree, header)
                if u in R:
                    assert recovered is None
                else:
                    assert recovered == K


def test_header_no_plaintext_K():
    tree, labels = setup(8)
    cover = sd_cover(tree, {3, 5})
    K = random_label()
    header = encrypt_session_key(labels, tree, cover, K)
    for (i, j, blob) in header:
        assert K not in blob
        assert blob != K


def test_derive_user_subset_key():
    tree, labels = setup(8)
    mat = keygen(tree, labels, 1)  # u1
    # u1 ∈ S_{1,10}，能派生 L_{1,10}
    assert derive_user_subset_key(mat, tree, 1, 10) == subset_key(labels, tree, 1, 10)
    # u1 ∉ S_{3,12}（u1 不在 v3 子树），返回 None
    assert derive_user_subset_key(mat, tree, 3, 12) is None
    # 整棵树 key
    assert derive_user_subset_key(mat, tree, 1, None) == mat["full_tree_key"]


# ---- 17/18. 序列化 + 篡改 ----


def test_serialization_roundtrip():
    tree, labels = setup(8)
    cover = sd_cover(tree, {3, 5})
    K = random_label()
    header = encrypt_session_key(labels, tree, cover, K)
    data = serialize_header(header)
    assert isinstance(data, bytes)
    restored = deserialize_header(data)
    assert restored == header


def test_header_tamper():
    tree, labels = setup(8)
    cover = sd_cover(tree, {3, 5})
    K = random_label()
    header = encrypt_session_key(labels, tree, cover, K)

    # 篡改一个 blob（翻转最后字节）
    i0, j0, blob0 = header[0]
    tampered_blob = bytearray(blob0)
    tampered_blob[-1] ^= 0xFF
    tampered = [(i0, j0, bytes(tampered_blob))] + header[1:]

    # 命中的用户无法恢复（认证失败返回 None）
    mat = keygen(tree, labels, 1)
    assert decrypt_session_key(mat, tree, tampered) is None


def test_invalid_header_formats():
    with pytest.raises(InvalidHeaderError):
        deserialize_header(b"not json {{{")
    with pytest.raises(InvalidHeaderError):
        deserialize_header(json.dumps({"version": 999}).encode())
    with pytest.raises(InvalidHeaderError):
        deserialize_header(json.dumps({"version": 1, "subsets": "bad"}).encode())
    with pytest.raises(InvalidHeaderError):
        d = {"version": 1, "subsets": [{"i": 1, "j": 2, "encrypted": "!!!bad!!!"}]}
        deserialize_header(json.dumps(d).encode())


def test_subset_key_full_tree():
    tree, labels = setup(8)
    assert subset_key(labels, tree, 1, None) == G_M(labels[1])
