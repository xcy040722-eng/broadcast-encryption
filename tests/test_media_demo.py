"""媒体加密闭环 correctness test（PNG / JPEG / MP4）。"""

import hashlib

import pytest

from src.cs.keys import keygen, setup
from src.file_crypto import DecryptionError, decrypt_file, encrypt_file
from demo.media_data import MEDIA


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@pytest.mark.parametrize("name", ["image_png", "image_jpeg", "video_mp4"])
def test_media_roundtrip_authorized_and_revoked(name, tmp_path):
    """同一密文下：授权用户恢复 K 得正确原文件，撤销用户无法恢复。"""
    data = MEDIA[name]
    tree, node_keys = setup(8)
    revoked = {3}

    src = tmp_path / "media.bin"
    src.write_bytes(data)
    enc = tmp_path / "media.enc"
    out = tmp_path / "media.out"

    encrypt_file(str(src), str(enc), tree, node_keys, revoked)

    # authorized 用户（u1）恢复
    decrypt_file(str(enc), str(out), keygen(tree, node_keys, 1))
    assert _sha256(out.read_bytes()) == _sha256(data)

    # revoked 用户（u3）无法恢复（DecryptionError）
    with pytest.raises(DecryptionError):
        decrypt_file(str(enc), str(tmp_path / "revoked.out"), keygen(tree, node_keys, 3))


def test_media_revoked_all_users_fail(tmp_path):
    """撤销全部用户时，无人能恢复。"""
    data = MEDIA["image_png"]
    tree, node_keys = setup(8)
    src = tmp_path / "m.bin"
    src.write_bytes(data)
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, set(range(1, 9)))

    for u in range(1, 9):
        with pytest.raises(DecryptionError):
            decrypt_file(str(enc), str(tmp_path / f"o{u}"), keygen(tree, node_keys, u))


def test_media_ciphertext_does_not_reveal_plaintext(tmp_path):
    """密文中不含明文媒体字节（仅 AES-GCM 密文）。"""
    data = MEDIA["image_png"]
    tree, node_keys = setup(8)
    src = tmp_path / "m.bin"
    src.write_bytes(data)
    enc = tmp_path / "m.enc"
    encrypt_file(str(src), str(enc), tree, node_keys, {3})

    raw = enc.read_bytes()
    # 原文件首 4 字节（PNG 魔数 \x89PNG）不应出现在密文包中
    assert data[:4] not in raw
