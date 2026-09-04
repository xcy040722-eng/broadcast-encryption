"""文件级混合加密功能测试（Prompt 06 Test 1-13）。"""

import base64
import hashlib
import json

import pytest

from src.cs.keys import keygen, setup
from src.file_crypto import DecryptionError, decrypt_file, encrypt_file


# 1x1 透明 PNG（67 字节）
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _tamper_package(path, mutator):
    d = json.loads(path.read_text(encoding="utf-8"))
    mutator(d)
    path.write_text(json.dumps(d), encoding="utf-8")


# ---- Test 1/2/3：文本 / 二进制 / 图片 闭环 ----


def test_text_roundtrip(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "original.txt"
    src.write_bytes("hello broadcast encryption\n".encode())
    enc = tmp_path / "out.enc"
    dec = tmp_path / "restored.txt"

    encrypt_file(str(src), str(enc), tree, node_keys, {3})
    decrypt_file(str(enc), str(dec), keygen(tree, node_keys, 1))

    assert dec.read_bytes() == src.read_bytes()


def test_binary_roundtrip(tmp_path):
    tree, node_keys = setup(8)
    data = bytes(range(256)) * 4  # 1 KB 二进制
    src = tmp_path / "bin.dat"
    src.write_bytes(data)
    enc = tmp_path / "out.enc"
    dec = tmp_path / "restored.dat"

    encrypt_file(str(src), str(enc), tree, node_keys, set())
    decrypt_file(str(enc), str(dec), keygen(tree, node_keys, 2))

    assert dec.read_bytes() == data


def test_image_roundtrip_hash(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "img.png"
    src.write_bytes(PNG_BYTES)
    enc = tmp_path / "img.enc"
    dec = tmp_path / "img2.png"

    encrypt_file(str(src), str(enc), tree, node_keys, {3})
    decrypt_file(str(enc), str(dec), keygen(tree, node_keys, 1))

    assert _sha256(dec.read_bytes()) == _sha256(PNG_BYTES)


# ---- Test 4/5/6/7：多用户 / 多撤销 / 全撤销 / 无撤销 ----


def test_multi_user_r3(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, {3})

    for u in range(1, 9):
        out = tmp_path / f"out_{u}.txt"
        if u == 3:
            with pytest.raises(DecryptionError):
                decrypt_file(str(enc), str(out), keygen(tree, node_keys, u))
            assert not out.exists()
        else:
            decrypt_file(str(enc), str(out), keygen(tree, node_keys, u))
            assert out.read_bytes() == b"payload"


def test_multi_revoked_r3_r5(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, {3, 5})

    for u in range(1, 9):
        out = tmp_path / f"out_{u}.txt"
        if u in {3, 5}:
            with pytest.raises(DecryptionError):
                decrypt_file(str(enc), str(out), keygen(tree, node_keys, u))
        else:
            decrypt_file(str(enc), str(out), keygen(tree, node_keys, u))
            assert out.read_bytes() == b"payload"


def test_all_revoked(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, set(range(1, 9)))

    for u in range(1, 9):
        out = tmp_path / f"out_{u}.txt"
        with pytest.raises(DecryptionError):
            decrypt_file(str(enc), str(out), keygen(tree, node_keys, u))
        assert not out.exists()


def test_no_revoked(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, set())

    for u in range(1, 9):
        out = tmp_path / f"out_{u}.txt"
        decrypt_file(str(enc), str(out), keygen(tree, node_keys, u))
        assert out.read_bytes() == b"payload"


# ---- Test 8/9/10/11：各类篡改 ----


def test_header_tamper(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, set())

    def tamper(d):
        d["cs_header"]["encrypted"][0] = base64.b64encode(b"tampered").decode()

    _tamper_package(enc, tamper)

    out = tmp_path / "out.txt"
    with pytest.raises(DecryptionError):
        decrypt_file(str(enc), str(out), keygen(tree, node_keys, 1))
    assert not out.exists()


def test_body_tamper(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, set())

    def tamper(d):
        d["body"]["ciphertext"] = base64.b64encode(b"tampered-ciphertext").decode()

    _tamper_package(enc, tamper)

    out = tmp_path / "out.txt"
    with pytest.raises(DecryptionError):
        decrypt_file(str(enc), str(out), keygen(tree, node_keys, 1))
    assert not out.exists()


def test_nonce_tamper(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, set())

    def tamper(d):
        d["body"]["nonce"] = base64.b64encode(b"\xff" * 12).decode()

    _tamper_package(enc, tamper)

    out = tmp_path / "out.txt"
    with pytest.raises(DecryptionError):
        decrypt_file(str(enc), str(out), keygen(tree, node_keys, 1))
    assert not out.exists()


def test_aad_metadata_tamper(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, set())

    def tamper(d):
        d["original_filename"] = "tampered.txt"

    _tamper_package(enc, tamper)

    out = tmp_path / "out.txt"
    with pytest.raises(DecryptionError):
        decrypt_file(str(enc), str(out), keygen(tree, node_keys, 1))
    assert not out.exists()


# ---- Test 12：Session Key 不泄露 ----


def test_session_key_not_in_package(tmp_path):
    """结构层验证：package 不含明文 session key 字段。

    注意：这是结构层面验证，非字节级 K 泄露检测。K 由 encrypt_file 内部
    secrets 随机生成且不向外暴露，测试拿不到 K 值，因此只能断言 package
    结构中不存在 session key 字段，不能做「K 字节不在序列化输出」的断言。
    """
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, {3})

    d = json.loads(enc.read_text(encoding="utf-8"))
    # 结构上不存在明文 session key 字段
    assert "session_key" not in d
    assert "key" not in d
    assert "session_key" not in d["cs_header"]
    # body 只含 nonce 与 ciphertext，不混入 K
    assert set(d["body"].keys()) == {"nonce", "ciphertext"}


# ---- Test 13：三类文件 SHA-256 一致 ----


@pytest.mark.parametrize(
    "payload",
    [b"hello world text payload", bytes(range(256)) * 4, PNG_BYTES],
    ids=["text", "binary", "image"],
)
def test_hash_roundtrip(payload, tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "src"
    src.write_bytes(payload)
    enc = tmp_path / "out.enc"
    dec = tmp_path / "dec"

    encrypt_file(str(src), str(enc), tree, node_keys, {3})
    decrypt_file(str(enc), str(dec), keygen(tree, node_keys, 1))

    assert _sha256(dec.read_bytes()) == _sha256(payload)


# ---- A/B/C：输出已存在 / overwrite / indices 篡改 ----


def test_decrypt_existing_output_file(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, set())

    out = tmp_path / "out.txt"
    out.write_bytes(b"PRE-EXISTING")

    with pytest.raises(FileExistsError):
        decrypt_file(str(enc), str(out), keygen(tree, node_keys, 1))

    assert out.read_bytes() == b"PRE-EXISTING"  # 原内容未被覆盖


def test_encrypt_existing_output_file(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    out = tmp_path / "out.enc"
    out.write_bytes(b"PRE-EXISTING")

    with pytest.raises(FileExistsError):
        encrypt_file(str(src), str(out), tree, node_keys, set())

    assert out.read_bytes() == b"PRE-EXISTING"


def test_overwrite_true(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, set())

    out = tmp_path / "out.txt"
    out.write_bytes(b"OLD-CONTENT")

    decrypt_file(str(enc), str(out), keygen(tree, node_keys, 1), overwrite=True)

    assert out.read_bytes() == b"payload"  # 覆盖后与原始明文一致


def test_header_indices_tamper(tmp_path):
    tree, node_keys = setup(8)
    src = tmp_path / "m.txt"
    src.write_bytes(b"payload")
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, {3})  # cover = [3,4,11]

    def tamper(d):
        # 保持长度不变，把最后一个合法索引 11 改成 10
        d["cs_header"]["indices"][-1] = 10

    _tamper_package(enc, tamper)

    out = tmp_path / "out.txt"
    with pytest.raises(DecryptionError):
        decrypt_file(str(enc), str(out), keygen(tree, node_keys, 1))
    assert not out.exists()
