"""Integration test against the real GmSSL shared library.

Skipped automatically only when GmSSL-Python/native libgmssl cannot be imported.
An ABI layout mismatch is a hard failure (not a skip) because an undersized
ctypes structure can otherwise corrupt memory and cause delayed segfaults.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.sm2_sm4_mre.gmssl_backend import GmsslBackend
from src.sm2_sm4_mre.service import decrypt_media, encrypt_media, generate_user_keys
from src.sm2_sm4_mre.types import DecryptStatus


pytestmark = pytest.mark.skipif(
    not GmsslBackend.is_available(),
    reason="GmSSL-Python/native libgmssl is not installed",
)


def test_real_gmssl_sm2_sm4_roundtrip(tmp_path: Path):
    issues = GmsslBackend.abi_issues()
    assert not issues, (
        "Unsafe GmSSL ctypes ABI layout: "
        + "; ".join(issues)
        + ". Run `python tools/patch_gmssl_python_abi.py` before native tests."
    )

    backend = GmsslBackend()
    u2 = generate_user_keys("u2", "test-password", tmp_path / "keys", backend=backend)
    src = tmp_path / "sample.bin"
    src.write_bytes((b"real gmssl integration\n" * 1024) + bytes(range(64)))
    package = tmp_path / "sample.smre"
    encrypt_media(src, {"u2": u2.public_key}, package, backend=backend, chunk_size=1024)

    out = tmp_path / "out.bin"
    dec = decrypt_media(
        package,
        "u2",
        u2.private_key,
        "test-password",
        out,
        backend=backend,
        chunk_size=777,
    )
    assert dec.status == DecryptStatus.SUCCESS
    assert out.read_bytes() == src.read_bytes()
