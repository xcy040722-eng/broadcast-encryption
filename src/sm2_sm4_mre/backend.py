"""Cryptographic backend abstraction.

The application logic depends only on this protocol. The production backend
is GmsslBackend; tests can supply an isolated fake without duplicating the
business logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO, Protocol, runtime_checkable


@runtime_checkable
class CryptoBackend(Protocol):
    sm4_key_size: int
    sm4_gcm_iv_size: int
    sm4_gcm_tag_size: int

    def random_bytes(self, size: int) -> bytes: ...

    def sm3(self, data: bytes) -> bytes: ...

    def generate_sm2_keypair(
        self, private_key_path: Path, public_key_path: Path, password: str
    ) -> None: ...

    def load_sm2_public_key(self, path: Path) -> Any: ...

    def load_sm2_private_key(self, path: Path, password: str) -> Any: ...

    def sm2_encrypt(self, public_key: Any, plaintext: bytes) -> bytes: ...

    def sm2_decrypt(self, private_key: Any, ciphertext: bytes) -> bytes: ...

    def sm4_gcm_encrypt_stream(
        self,
        key: bytes,
        iv: bytes,
        aad: bytes,
        source: BinaryIO,
        sink: BinaryIO,
        *,
        chunk_size: int,
    ) -> int: ...

    def sm4_gcm_decrypt_stream(
        self,
        key: bytes,
        iv: bytes,
        aad: bytes,
        source: BinaryIO,
        sink: BinaryIO,
        *,
        chunk_size: int,
    ) -> int: ...
