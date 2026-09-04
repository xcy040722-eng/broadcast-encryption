"""Encrypt / Decrypt 正确性测试（授权可恢复 K、撤销不可恢复 K）。"""

import secrets

from src.cs.cover import cover
from src.cs.crypto import random_key
from src.cs.encrypt import decrypt_session_key, encrypt_session_key
from src.cs.keys import keygen, setup


def _random_subset(n):
    return {u for u in range(1, n + 1) if secrets.randbits(1)}


def test_n8_r_u3():
    tree, node_keys = setup(8)
    R = {3}
    K = random_key()
    header = encrypt_session_key(node_keys, cover(tree, R), K)

    for u in range(1, 9):
        recovered = decrypt_session_key(keygen(tree, node_keys, u), header)
        if u == 3:
            assert recovered is None
        else:
            assert recovered == K


def test_n8_r_u3_u5():
    tree, node_keys = setup(8)
    R = {3, 5}
    K = random_key()
    header = encrypt_session_key(node_keys, cover(tree, R), K)

    for u in range(1, 9):
        recovered = decrypt_session_key(keygen(tree, node_keys, u), header)
        if u in R:
            assert recovered is None
        else:
            assert recovered == K


def test_empty_revoked_all_recover():
    tree, node_keys = setup(8)
    K = random_key()
    header = encrypt_session_key(node_keys, cover(tree, set()), K)
    for u in range(1, 9):
        assert decrypt_session_key(keygen(tree, node_keys, u), header) == K


def test_all_revoked_none_recover():
    tree, node_keys = setup(8)
    R = set(range(1, 9))
    K = random_key()
    header = encrypt_session_key(node_keys, cover(tree, R), K)
    assert header["indices"] == []
    for u in range(1, 9):
        assert decrypt_session_key(keygen(tree, node_keys, u), header) is None


def test_randomized_many():
    """随机多个 N 与撤销集合：授权用户 decrypt(encrypt(K))==K，撤销用户无法恢复。"""
    for N in [1, 2, 4, 8, 16, 32]:
        tree, node_keys = setup(N)
        for _ in range(20):
            R = _random_subset(N)
            K = random_key()
            header = encrypt_session_key(node_keys, cover(tree, R), K)
            for u in range(1, N + 1):
                recovered = decrypt_session_key(keygen(tree, node_keys, u), header)
                if u in R:
                    assert recovered is None
                else:
                    assert recovered == K


def test_ciphertext_does_not_reveal_session_key():
    """header 中不出现明文会话密钥。"""
    tree, node_keys = setup(8)
    R = {3}
    K = random_key()
    header = encrypt_session_key(node_keys, cover(tree, R), K)
    for blob in header["encrypted"]:
        assert K not in blob
        assert blob != K
