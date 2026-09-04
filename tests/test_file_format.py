"""文件格式序列化/反序列化测试（Prompt 06 第 15 节）。"""

import json

import pytest

from src.file_crypto import (
    InvalidPackageError,
    build_package,
    deserialize_package,
    serialize_package,
)


def _valid_pkg() -> dict:
    cs_header = {
        "indices": [1, 2, 3],
        "encrypted": [b"\x01" * 28, b"\x02" * 28, b"\x03" * 28],
    }
    return build_package("f.txt", 100, cs_header, b"\x00" * 12, b"ciphertext")


def _serialized_dict(pkg):
    return json.loads(serialize_package(pkg).decode("utf-8"))


def test_roundtrip():
    pkg = _valid_pkg()
    restored = deserialize_package(serialize_package(pkg))
    assert restored["version"] == pkg["version"]
    assert restored["algorithm"] == pkg["algorithm"]
    assert restored["original_filename"] == "f.txt"
    assert restored["original_size"] == 100
    assert restored["cs_header"]["indices"] == [1, 2, 3]
    assert restored["cs_header"]["encrypted"] == pkg["cs_header"]["encrypted"]
    assert restored["body"]["nonce"] == b"\x00" * 12
    assert restored["body"]["ciphertext"] == b"ciphertext"


def test_missing_version():
    d = _serialized_dict(_valid_pkg())
    del d["version"]
    with pytest.raises(InvalidPackageError):
        deserialize_package(json.dumps(d).encode())


def test_wrong_version():
    d = _serialized_dict(_valid_pkg())
    d["version"] = 999
    with pytest.raises(InvalidPackageError):
        deserialize_package(json.dumps(d).encode())


def test_missing_cs_header():
    d = _serialized_dict(_valid_pkg())
    del d["cs_header"]
    with pytest.raises(InvalidPackageError):
        deserialize_package(json.dumps(d).encode())


def test_missing_nonce():
    d = _serialized_dict(_valid_pkg())
    del d["body"]["nonce"]
    with pytest.raises(InvalidPackageError):
        deserialize_package(json.dumps(d).encode())


def test_header_length_mismatch():
    d = _serialized_dict(_valid_pkg())
    d["cs_header"]["encrypted"].pop()
    with pytest.raises(InvalidPackageError):
        deserialize_package(json.dumps(d).encode())


def test_illegal_base64():
    d = _serialized_dict(_valid_pkg())
    d["body"]["ciphertext"] = "!!!not-base64!!!"
    with pytest.raises(InvalidPackageError):
        deserialize_package(json.dumps(d).encode())


def test_illegal_json():
    with pytest.raises(InvalidPackageError):
        deserialize_package(b"not json {{{")


def test_ciphertext_wrong_type():
    d = _serialized_dict(_valid_pkg())
    d["body"]["ciphertext"] = 12345
    with pytest.raises(InvalidPackageError):
        deserialize_package(json.dumps(d).encode())


def test_nonce_wrong_length():
    import base64

    d = _serialized_dict(_valid_pkg())
    d["body"]["nonce"] = base64.b64encode(b"short").decode()
    with pytest.raises(InvalidPackageError):
        deserialize_package(json.dumps(d).encode())
