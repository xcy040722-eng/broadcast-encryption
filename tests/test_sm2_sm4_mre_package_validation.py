from __future__ import annotations

import json

import pytest

from src.sm2_sm4_mre.errors import InvalidPackageError
from src.sm2_sm4_mre.package import build_manifest, canonical_manifest_bytes, parse_manifest_bytes


def test_manifest_canonicalization_is_stable():
    manifest = build_manifest(
        package_id=b"p" * 16,
        recipient_ids=["u4", "u2"],
        filename="测试.png",
        plaintext_size=123,
        mime="image/png",
        iv=b"i" * 12,
        tag_size=16,
    )
    a = canonical_manifest_bytes(manifest)
    b = canonical_manifest_bytes(parse_manifest_bytes(a))
    assert a == b
    assert [r.user_id for r in manifest.recipients] == ["u2", "u4"]


def test_manifest_rejects_path_traversal_wrapped_key_entry():
    manifest = build_manifest(
        package_id=b"p" * 16,
        recipient_ids=["u2"],
        filename="x.bin",
        plaintext_size=1,
        mime="application/octet-stream",
        iv=b"i" * 12,
        tag_size=16,
    ).to_dict()
    manifest["recipients"][0]["wrapped_key_entry"] = "../evil.bin"
    data = json.dumps(manifest).encode()
    with pytest.raises(InvalidPackageError):
        parse_manifest_bytes(data)
