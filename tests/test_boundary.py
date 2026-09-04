"""边界情况与序列化测试。"""

import pytest

from src.cs.cover import cover
from src.cs.crypto import random_key
from src.cs.encrypt import decrypt_session_key, encrypt_session_key
from src.cs.keys import keygen, setup
from src.cs.serialization import deserialize_header, serialize_header


def test_single_user_n1():
    tree, node_keys = setup(1)
    assert tree.node_count == 1
    # 单用户，无撤销
    K = random_key()
    header = encrypt_session_key(node_keys, cover(tree, set()), K)
    assert decrypt_session_key(keygen(tree, node_keys, 1), header) == K
    # 撤销唯一用户
    header2 = encrypt_session_key(node_keys, cover(tree, {1}), K)
    assert header2["indices"] == []
    assert decrypt_session_key(keygen(tree, node_keys, 1), header2) is None


def test_serialization_roundtrip():
    tree, node_keys = setup(8)
    K = random_key()
    header = encrypt_session_key(node_keys, cover(tree, {3}), K)
    data = serialize_header(header)
    assert isinstance(data, bytes)
    restored = deserialize_header(data)
    assert restored["indices"] == header["indices"]
    assert restored["encrypted"] == header["encrypted"]
    # 反序列化后仍可正确解密
    u1 = keygen(tree, node_keys, 1)
    assert decrypt_session_key(u1, restored) == K


def test_tampered_header_fails():
    """篡改 header 密文 → GCM 认证失败 → 解密返回 None（不静默产出坏结果）。"""
    tree, node_keys = setup(1)
    K = random_key()
    header = encrypt_session_key(node_keys, cover(tree, set()), K)

    blob = bytearray(header["encrypted"][0])
    blob[-1] ^= 0xFF
    tampered = {"indices": header["indices"], "encrypted": [bytes(blob)]}

    assert decrypt_session_key(keygen(tree, node_keys, 1), tampered) is None


def test_revoked_returns_none_not_exception():
    tree, node_keys = setup(8)
    header = encrypt_session_key(node_keys, cover(tree, {3}), random_key())
    u3 = keygen(tree, node_keys, 3)
    # 撤销用户：无命中，返回 None 而非抛异常
    assert decrypt_session_key(u3, header) is None


def test_header_length_mismatch_raises():
    """L5：header 字段长度不一致时应抛异常，而非 zip 静默截断。"""
    tree, node_keys = setup(8)
    bad_header = {"indices": [3, 4], "encrypted": [b"only_one"]}
    with pytest.raises(ValueError):
        decrypt_session_key(keygen(tree, node_keys, 1), bad_header)
