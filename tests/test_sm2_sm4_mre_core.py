from __future__ import annotations

import hashlib
import hmac
import itertools
from pathlib import Path

import pytest

from src.sm2_sm4_mre.envelope import decode_envelope, encode_envelope
from src.sm2_sm4_mre.errors import CryptoOperationError, InvalidEnvelopeError
from src.sm2_sm4_mre.package import inspect_package
from src.sm2_sm4_mre.service import (
    decrypt_media,
    encrypt_media,
    force_try_wrapped_key,
    generate_encryption_material,
    generate_user_keys,
    unwrap_content_key,
    wrap_content_key,
)
from src.sm2_sm4_mre.types import (
    CONTENT_KEY_SIZE,
    PACKAGE_ID_SIZE,
    DecryptStatus,
    KeyEnvelope,
)


class FakeBackend:
    """Test-only backend; production code uses GmsslBackend."""

    sm4_key_size = 16
    sm4_gcm_iv_size = 12
    sm4_gcm_tag_size = 16

    def __init__(self):
        self._counter = itertools.count(1)

    def random_bytes(self, size: int) -> bytes:
        n = next(self._counter)
        out = bytearray()
        block = 0
        while len(out) < size:
            out.extend(hashlib.sha256(f"rng:{n}:{block}".encode()).digest())
            block += 1
        return bytes(out[:size])

    def sm3(self, data: bytes) -> bytes:
        return hashlib.sha256(b"fake-sm3:" + data).digest()

    def generate_sm2_keypair(self, private_key_path: Path, public_key_path: Path, password: str) -> None:
        user = private_key_path.parent.name
        secret = hashlib.sha256(("sm2:" + user).encode()).hexdigest()
        private_key_path.write_text(f"{password}:{secret}", encoding="utf-8")
        public_key_path.write_text(secret, encoding="utf-8")

    def load_sm2_public_key(self, path: Path):
        return Path(path).read_text(encoding="utf-8")

    def load_sm2_private_key(self, path: Path, password: str):
        raw = Path(path).read_text(encoding="utf-8")
        stored_password, secret = raw.split(":", 1)
        if stored_password != password:
            raise CryptoOperationError("bad password")
        return secret

    @staticmethod
    def _xor(data: bytes, stream: bytes) -> bytes:
        return bytes(a ^ b for a, b in zip(data, stream))

    @staticmethod
    def _keystream(secret: str, size: int) -> bytes:
        key = bytes.fromhex(secret)
        out = bytearray()
        counter = 0
        while len(out) < size:
            out.extend(hashlib.sha256(key + counter.to_bytes(4, "big")).digest())
            counter += 1
        return bytes(out[:size])

    def sm2_encrypt(self, public_key, plaintext: bytes) -> bytes:
        secret = public_key
        stream = self._keystream(secret, len(plaintext))
        body = self._xor(plaintext, stream)
        tag = hmac.new(bytes.fromhex(secret), plaintext, hashlib.sha256).digest()[:16]
        return b"F2" + tag + body

    def sm2_decrypt(self, private_key, ciphertext: bytes) -> bytes:
        if len(ciphertext) < 18 or ciphertext[:2] != b"F2":
            raise CryptoOperationError("invalid fake SM2 ciphertext")
        secret = private_key
        tag, body = ciphertext[2:18], ciphertext[18:]
        stream = self._keystream(secret, len(body))
        plain = self._xor(body, stream)
        expected = hmac.new(bytes.fromhex(secret), plain, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(tag, expected):
            raise CryptoOperationError("wrong private key or tampered SM2 ciphertext")
        return plain

    @staticmethod
    def _stream_block(key: bytes, iv: bytes, counter: int) -> bytes:
        return hashlib.sha256(key + iv + counter.to_bytes(8, "big")).digest()

    def _xor_stream(self, key: bytes, iv: bytes, data: bytes, offset: int) -> bytes:
        result = bytearray()
        while len(result) < len(data):
            absolute = offset + len(result)
            block_index = absolute // 32
            block_offset = absolute % 32
            block = self._stream_block(key, iv, block_index)
            take = min(len(data) - len(result), 32 - block_offset)
            chunk = data[len(result): len(result) + take]
            result.extend(bytes(a ^ b for a, b in zip(chunk, block[block_offset:block_offset + take])))
        return bytes(result)

    def sm4_gcm_encrypt_stream(self, key, iv, aad, source, sink, *, chunk_size):
        offset = 0
        cipher_acc = bytearray()
        while True:
            chunk = source.read(chunk_size)
            if not chunk:
                break
            out = self._xor_stream(key, iv, chunk, offset)
            sink.write(out)
            cipher_acc.extend(out)
            offset += len(chunk)
        tag = hmac.new(key, aad + bytes(cipher_acc), hashlib.sha256).digest()[: self.sm4_gcm_tag_size]
        sink.write(tag)
        return len(cipher_acc) + len(tag)

    def sm4_gcm_decrypt_stream(self, key, iv, aad, source, sink, *, chunk_size):
        all_data = source.read()
        if len(all_data) < self.sm4_gcm_tag_size:
            raise CryptoOperationError("truncated fake GCM ciphertext")
        body = all_data[:-self.sm4_gcm_tag_size]
        tag = all_data[-self.sm4_gcm_tag_size:]
        expected = hmac.new(key, aad + body, hashlib.sha256).digest()[: self.sm4_gcm_tag_size]
        if not hmac.compare_digest(tag, expected):
            raise CryptoOperationError("fake GCM authentication failed")
        plain = self._xor_stream(key, iv, body, 0)
        sink.write(plain)
        return len(plain)


def _keyset(tmp_path: Path, backend: FakeBackend):
    keys = {}
    for user in ("u1", "u2", "u3", "u4"):
        keys[user] = generate_user_keys(user, f"pw-{user}", tmp_path / "keys", backend=backend)
    return keys


def test_envelope_roundtrip_and_binding():
    env = KeyEnvelope(b"p" * PACKAGE_ID_SIZE, "u2", b"k" * CONTENT_KEY_SIZE)
    encoded = encode_envelope(env)
    assert decode_envelope(encoded) == env
    with pytest.raises(InvalidEnvelopeError):
        decode_envelope(encoded[:-1])


def test_material_is_fresh_and_right_sizes():
    backend = FakeBackend()
    a = generate_encryption_material(backend=backend)
    b = generate_encryption_material(backend=backend)
    assert len(a.package_id) == PACKAGE_ID_SIZE
    assert len(a.content_key) == CONTENT_KEY_SIZE
    assert len(a.iv) == backend.sm4_gcm_iv_size
    assert a != b


def test_wrap_unwrap_same_user_and_wrong_user(tmp_path: Path):
    backend = FakeBackend()
    keys = _keyset(tmp_path, backend)
    material = generate_encryption_material(backend=backend)
    wrapped = wrap_content_key(
        keys["u2"].public_key,
        package_id=material.package_id,
        user_id="u2",
        content_key=material.content_key,
        backend=backend,
    )
    recovered = unwrap_content_key(
        keys["u2"].private_key,
        "pw-u2",
        wrapped,
        expected_package_id=material.package_id,
        expected_user_id="u2",
        backend=backend,
    )
    assert recovered == material.content_key

    with pytest.raises(CryptoOperationError):
        unwrap_content_key(
            keys["u1"].private_key,
            "pw-u1",
            wrapped,
            expected_package_id=material.package_id,
            expected_user_id="u1",
            backend=backend,
        )


def test_authorized_recipients_roundtrip_and_nonrecipient_denied(tmp_path: Path):
    backend = FakeBackend()
    keys = _keyset(tmp_path, backend)
    original = tmp_path / "input.bin"
    original_data = bytes(range(256)) * 128 + b"tail"
    original.write_bytes(original_data)
    package = tmp_path / "broadcast.smre"

    enc = encrypt_media(
        original,
        {"u2": keys["u2"].public_key, "u4": keys["u4"].public_key},
        package,
        backend=backend,
        chunk_size=777,
    )
    assert enc.package_path == package
    manifest = inspect_package(package)
    assert [r.user_id for r in manifest.recipients] == ["u2", "u4"]
    assert manifest.plaintext_size == len(original_data)

    for user in ("u2", "u4"):
        out = tmp_path / f"{user}-out.bin"
        dec = decrypt_media(
            package,
            user,
            keys[user].private_key,
            f"pw-{user}",
            out,
            backend=backend,
            chunk_size=511,
        )
        assert dec.status == DecryptStatus.SUCCESS
        assert out.read_bytes() == original_data
        assert dec.trace.gcm_authenticated is True

    denied = decrypt_media(
        package,
        "u1",
        keys["u1"].private_key,
        "pw-u1",
        tmp_path / "must-not-exist.bin",
        backend=backend,
    )
    assert denied.status == DecryptStatus.NOT_RECIPIENT
    assert not (tmp_path / "must-not-exist.bin").exists()


def test_force_try_wrong_private_key_fails_real_unwrap(tmp_path: Path):
    backend = FakeBackend()
    keys = _keyset(tmp_path, backend)
    original = tmp_path / "photo.png"
    original.write_bytes(b"not-a-real-png-but-fine-for-backend-test")
    package = tmp_path / "broadcast.smre"
    encrypt_media(
        original,
        {"u2": keys["u2"].public_key, "u4": keys["u4"].public_key},
        package,
        backend=backend,
    )

    forced = force_try_wrapped_key(
        package,
        attacker_user_id="u1",
        attacker_private_key_path=keys["u1"].private_key,
        password="pw-u1",
        target_recipient_id="u2",
        output_path=tmp_path / "forced.bin",
        backend=backend,
    )
    assert forced.status == DecryptStatus.SM2_UNWRAP_FAILED
    assert not (tmp_path / "forced.bin").exists()


def test_payload_tamper_is_rejected_and_plaintext_not_released(tmp_path: Path):
    import zipfile

    backend = FakeBackend()
    keys = _keyset(tmp_path, backend)
    original = tmp_path / "movie.bin"
    original.write_bytes(b"abcdef" * 1000)
    package = tmp_path / "broadcast.smre"
    encrypt_media(original, {"u2": keys["u2"].public_key}, package, backend=backend)

    tampered = tmp_path / "tampered.smre"
    with zipfile.ZipFile(package, "r") as src, zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_STORED) as dst:
        for name in src.namelist():
            data = src.read(name)
            if name == "payload.bin":
                buf = bytearray(data)
                buf[len(buf) // 2] ^= 0x01
                data = bytes(buf)
            dst.writestr(name, data)

    output = tmp_path / "tampered-out.bin"
    dec = decrypt_media(
        tampered,
        "u2",
        keys["u2"].private_key,
        "pw-u2",
        output,
        backend=backend,
    )
    assert dec.status == DecryptStatus.GCM_AUTH_FAILED
    assert dec.trace.gcm_authenticated is False
    assert not output.exists()
    assert not list(tmp_path.glob("tampered-out.bin.*.part"))


def test_same_file_encrypted_twice_produces_different_packages(tmp_path: Path):
    backend = FakeBackend()
    keys = _keyset(tmp_path, backend)
    original = tmp_path / "x.bin"
    original.write_bytes(b"same plaintext")
    p1 = tmp_path / "a.smre"
    p2 = tmp_path / "b.smre"
    e1 = encrypt_media(original, {"u2": keys["u2"].public_key}, p1, backend=backend)
    e2 = encrypt_media(original, {"u2": keys["u2"].public_key}, p2, backend=backend)
    assert e1.trace.package_id != e2.trace.package_id
    assert p1.read_bytes() != p2.read_bytes()
