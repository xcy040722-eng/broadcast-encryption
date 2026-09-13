"""CHW25 Hybrid 层测试：DBE → AES-256 session key → AES-GCM 文件。"""

import json
import os
import secrets

import pytest

from src.chw25_dbe import (
    BIT_LEN,
    KEY_LEN,
    KeysetMismatchError,
    Params,
    PublicKey,
    bits_to_bytes,
    bytes_to_bits,
    decrypt_file_for_user,
    decrypt_session_key,
    deserialize_package,
    encrypt_file_for_set,
    encrypt_session_key,
    keygen,
    keyset_id,
    serialize_package,
    setup,
)
from src.file_crypto.format import DecryptionError
from demo.media_data import PNG_BYTES

P = Params()


@pytest.fixture(scope="module")
def system():
    pp = setup(P)
    pks, sks = {}, {}
    for i in range(1, P.N + 1):
        pk, sk = keygen(pp, i)
        pks[i], sks[i] = pk, sk
    return pp, pks, sks


# ---- 1. bit ordering 可逆 ----


def test_bit_ordering_roundtrip():
    for _ in range(20):
        data = secrets.token_bytes(32)
        assert bits_to_bytes(bytes_to_bits(data)) == data
    assert bits_to_bytes(bytes_to_bits(b"\x00" * 32)) == b"\x00" * 32
    assert bits_to_bytes(bytes_to_bits(b"\xff" * 32)) == b"\xff" * 32


def test_bit_ordering_definite():
    """固定 bit ordering（MSB-first）：0x80 → 首 bit=1，0x01 → 末 bit=1。"""
    bits = bytes_to_bits(bytes([0x80]) + b"\x00" * 31)
    assert bits[0] == 1 and bits[1] == 0
    bits2 = bytes_to_bits(b"\x00" * 31 + bytes([0x01]))
    assert bits2[-1] == 1 and bits2[-2] == 0


# ---- 2. session key round-trip（含边界 pattern）----


@pytest.mark.parametrize(
    "key",
    [
        b"\x00" * 32,                                        # 全 0
        b"\xff" * 32,                                        # 全 1
        bytes([0x80] + [0] * 31),                            # 首 bit = 1
        bytes([0] * 31 + [0x01]),                            # 末 bit = 1
        bytes([0x80] + [0] * 30 + [0x01]),                   # 首尾 bit = 1
        bytes(range(32)),                                     # 递增
    ],
)
def test_session_key_roundtrip_patterns(system, key):
    pp, pks, sks = system
    S = {2, 4}
    wrapped = encrypt_session_key(pp, pks, S, key)
    assert len(wrapped) == BIT_LEN
    r = decrypt_session_key(pp, pks, S, wrapped, 2, sks[2])
    assert r.authorized and r.key == key
    r4 = decrypt_session_key(pp, pks, S, wrapped, 4, sks[4])
    assert r4.key == key


def test_session_key_random(system):
    pp, pks, sks = system
    S = {1, 2, 3}
    for _ in range(3):
        key = secrets.token_bytes(KEY_LEN)
        wrapped = encrypt_session_key(pp, pks, S, key)
        assert decrypt_session_key(pp, pks, S, wrapped, 3, sks[3]).key == key


# ---- 3. N=4, S={2,4}: u2/u4 恢复同一 K；u1/u3 → NotRecipient ----


def test_n4_s24_session_key(system):
    pp, pks, sks = system
    S = {2, 4}
    key = secrets.token_bytes(KEY_LEN)
    wrapped = encrypt_session_key(pp, pks, S, key)

    assert decrypt_session_key(pp, pks, S, wrapped, 2, sks[2]).key == key
    assert decrypt_session_key(pp, pks, S, wrapped, 4, sks[4]).key == key

    for i in (1, 3):
        r = decrypt_session_key(pp, pks, S, wrapped, i, sks[i])
        assert r.authorized is False and r.key is None


# ---- 4. 文件闭环（授权成功 / 非接收者拒绝）----


def test_file_roundtrip_binary(system, tmp_path):
    pp, pks, sks = system
    S = {2, 4}
    payload = secrets.token_bytes(4096)
    src = tmp_path / "in.bin"
    src.write_bytes(payload)
    enc = tmp_path / "out.enc"

    encrypt_file_for_set(pp, pks, S, str(src), str(enc))
    out = tmp_path / "dec.bin"
    res = decrypt_file_for_user(
        pp, pks, S, enc.read_bytes(), 2, sks[2], str(out)
    )
    assert res.authorized and out.read_bytes() == payload


def test_file_roundtrip_png(system, tmp_path):
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.png"
    src.write_bytes(PNG_BYTES)
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    out = tmp_path / "dec.png"
    res = decrypt_file_for_user(pp, pks, S, enc.read_bytes(), 4, sks[4], str(out))
    assert res.authorized
    assert out.read_bytes() == PNG_BYTES


def test_file_non_recipient(system, tmp_path):
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"secret")
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    out = tmp_path / "nope.bin"
    res = decrypt_file_for_user(pp, pks, S, enc.read_bytes(), 1, sks[1], str(out))
    assert res.authorized is False and res.output_path is None
    assert not out.exists()


# ---- 5. 篡改 wrapped-key → 最终失败 ----


def test_tamper_wrapped_key(system, tmp_path):
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    pkg = deserialize_package(enc.read_bytes())
    pkg["wrapped_key"][0]["c1"][0] = (int(pkg["wrapped_key"][0]["c1"][0]) + 1) % P.q  # 翻转 1 bit 密文
    bad = serialize_package(pkg)
    out = tmp_path / "bad.bin"
    with pytest.raises(DecryptionError):
        decrypt_file_for_user(pp, pks, S, bad, 2, sks[2], str(out))
    assert not out.exists()


# ---- 6. 篡改 body nonce / ciphertext / header → AES-GCM 认证失败 ----


def test_tamper_body_ciphertext(system, tmp_path):
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    pkg = deserialize_package(enc.read_bytes())
    raw = bytearray(__import__("base64").b64decode(pkg["body"]["ciphertext"]))
    raw[0] ^= 0x01
    pkg["body"]["ciphertext"] = __import__("base64").b64encode(bytes(raw)).decode()
    with pytest.raises(DecryptionError):
        decrypt_file_for_user(pp, pks, S, serialize_package(pkg), 2, sks[2], str(tmp_path / "x"))


def test_tamper_body_nonce(system, tmp_path):
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    pkg = deserialize_package(enc.read_bytes())
    raw = bytearray(__import__("base64").b64decode(pkg["body"]["nonce"]))
    raw[0] ^= 0x01
    pkg["body"]["nonce"] = __import__("base64").b64encode(bytes(raw)).decode()
    with pytest.raises(DecryptionError):
        decrypt_file_for_user(pp, pks, S, serialize_package(pkg), 2, sks[2], str(tmp_path / "x"))


def test_tamper_header_recipient_ids(system, tmp_path):
    """篡改 recipient_ids → 作为 AAD 被认证 → 失败。"""
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    pkg = deserialize_package(enc.read_bytes())
    pkg["recipient_ids"] = [1, 2, 4]  # 篡改元数据
    with pytest.raises(DecryptionError):
        decrypt_file_for_user(pp, pks, S, serialize_package(pkg), 2, sks[2], str(tmp_path / "x"))


def test_tamper_header_params_id(system, tmp_path):
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    pkg = deserialize_package(enc.read_bytes())
    pkg["params_id"] = "n8-m16-q999983-N8"
    with pytest.raises(DecryptionError):
        decrypt_file_for_user(pp, pks, S, serialize_package(pkg), 2, sks[2], str(tmp_path / "x"))


# ---- 6b. keyset_id hardening ----


def test_keyset_id_changes_on_public_key_change(system):
    """公钥变更 → keyset_id 不同。"""
    pp, pks, sks = system
    ks0 = keyset_id(pp, pks)
    # 复制目录并改动 u2 的 W
    pks2 = {i: PublicKey(W=pk.W.copy(), ys={j: y.copy() for j, y in pk.ys.items()})
            for i, pk in pks.items()}
    pks2[2].W[0, 0] = (int(pks2[2].W[0, 0]) + 1) % P.q
    assert keyset_id(pp, pks2) != ks0
    # 改动某个 y_{i,j}
    pks3 = {i: PublicKey(W=pk.W.copy(), ys={j: y.copy() for j, y in pk.ys.items()})
            for i, pk in pks.items()}
    j0 = next(iter(pks3[2].ys))
    pks3[2].ys[j0][0] += 1
    assert keyset_id(pp, pks3) != ks0
    # 相同目录 → 相同
    assert keyset_id(pp, pks) == ks0


def test_keyset_id_in_package(system, tmp_path):
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    pkg = encrypt_file_for_set(pp, pks, S, str(src), str(enc))
    assert pkg["keyset_id"] == keyset_id(pp, pks)


def test_wrong_keyset_rejected(system, tmp_path):
    """用错误 keyset 解密广播包 → 明确拒绝（KeysetMismatchError）。"""
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    # 构造一个「新目录」：u4 的公钥被改动
    pks_new = {i: PublicKey(W=pk.W.copy(), ys={j: y.copy() for j, y in pk.ys.items()})
               for i, pk in pks.items()}
    pks_new[4].W[0, 0] = (int(pks_new[4].W[0, 0]) + 1) % P.q

    out = tmp_path / "x.bin"
    with pytest.raises(KeysetMismatchError):
        decrypt_file_for_user(pp, pks_new, S, enc.read_bytes(), 2, sks[2], str(out))
    assert not out.exists()


def test_tamper_filename(system, tmp_path):
    """篡改 original_filename → 作为 AAD 被认证 → 失败。"""
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    pkg = deserialize_package(enc.read_bytes())
    pkg["original_filename"] = "evil.bin"
    with pytest.raises(DecryptionError):
        decrypt_file_for_user(pp, pks, S, serialize_package(pkg), 2, sks[2], str(tmp_path / "x"))


def test_tamper_original_size(system, tmp_path):
    """篡改 original_size → 作为 AAD 被认证 → 失败。"""
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    pkg = deserialize_package(enc.read_bytes())
    pkg["original_size"] = int(pkg["original_size"]) + 1
    with pytest.raises(DecryptionError):
        decrypt_file_for_user(pp, pks, S, serialize_package(pkg), 2, sks[2], str(tmp_path / "x"))


def test_tamper_keyset_id(system, tmp_path):
    """篡改 keyset_id → 拒绝。"""
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    pkg = deserialize_package(enc.read_bytes())
    pkg["keyset_id"] = "0" * 64
    with pytest.raises(KeysetMismatchError):
        decrypt_file_for_user(pp, pks, S, serialize_package(pkg), 2, sks[2], str(tmp_path / "x"))


# ---- 7. 包结构 ----


def test_package_structure(system, tmp_path):
    pp, pks, sks = system
    S = {2, 4}
    src = tmp_path / "in.bin"
    src.write_bytes(b"payload")
    enc = tmp_path / "out.enc"
    pkg = encrypt_file_for_set(pp, pks, S, str(src), str(enc))

    for key in ("version", "algorithm", "params_id", "recipient_ids",
                "wrapped_key", "body", "original_filename", "original_size"):
        assert key in pkg, f"缺少字段 {key}"
    assert pkg["recipient_ids"] == [2, 4]
    assert len(pkg["wrapped_key"]) == BIT_LEN
    assert pkg["algorithm"] == "CHW25-DBE-AES256GCM"
