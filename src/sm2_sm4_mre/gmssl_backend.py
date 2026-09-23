"""Production cryptographic backend backed by GmSSL-Python.

GmSSL-Python is a ctypes binding over a locally installed GmSSL shared library.
The import is intentionally lazy so the rest of the package (including package
inspection) remains importable on machines where GmSSL is not installed yet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO

from .errors import BackendUnavailableError, CryptoOperationError


class GmsslBackend:
    def __init__(self) -> None:
        try:
            import gmssl  # type: ignore
        except Exception as exc:  # pragma: no cover - environment-specific
            raise BackendUnavailableError(
                "GmSSL-Python is unavailable. Install the native GmSSL shared "
                "library first, then `pip install gmssl-python`."
            ) from exc

        self.gmssl = gmssl
        self.sm4_key_size = int(gmssl.SM4_KEY_SIZE)
        self.sm4_gcm_iv_size = int(gmssl.SM4_GCM_DEFAULT_IV_SIZE)
        self.sm4_gcm_tag_size = int(gmssl.SM4_GCM_DEFAULT_TAG_SIZE)

    @staticmethod
    def is_available() -> bool:
        try:
            import gmssl  # type: ignore

            _ = gmssl.GMSSL_PYTHON_VERSION
            _ = gmssl.GMSSL_LIBRARY_VERSION
            return True
        except Exception:
            return False

    def random_bytes(self, size: int) -> bytes:
        try:
            return bytes(self.gmssl.rand_bytes(size))
        except Exception as exc:
            raise CryptoOperationError(f"GmSSL random generation failed: {exc}") from exc

    def sm3(self, data: bytes) -> bytes:
        try:
            ctx = self.gmssl.Sm3()
            ctx.update(data)
            return bytes(ctx.digest())
        except Exception as exc:
            raise CryptoOperationError(f"SM3 failed: {exc}") from exc

    def generate_sm2_keypair(
        self, private_key_path: Path, public_key_path: Path, password: str
    ) -> None:
        private_key_path = Path(private_key_path)
        public_key_path = Path(public_key_path)
        private_key_path.parent.mkdir(parents=True, exist_ok=True)
        public_key_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            key = self.gmssl.Sm2Key()
            key.generate_key()
            key.export_encrypted_private_key_info_pem(str(private_key_path), password)
            key.export_public_key_info_pem(str(public_key_path))
        except Exception as exc:
            raise CryptoOperationError(f"SM2 key generation/export failed: {exc}") from exc

    def load_sm2_public_key(self, path: Path) -> Any:
        try:
            key = self.gmssl.Sm2Key()
            key.import_public_key_info_pem(str(Path(path)))
            return key
        except Exception as exc:
            raise CryptoOperationError(f"SM2 public key import failed: {exc}") from exc

    def load_sm2_private_key(self, path: Path, password: str) -> Any:
        try:
            key = self.gmssl.Sm2Key()
            key.import_encrypted_private_key_info_pem(str(Path(path)), password)
            return key
        except Exception as exc:
            raise CryptoOperationError(f"SM2 private key import failed: {exc}") from exc

    def sm2_encrypt(self, public_key: Any, plaintext: bytes) -> bytes:
        try:
            return bytes(public_key.encrypt(plaintext))
        except Exception as exc:
            raise CryptoOperationError(f"SM2 encryption failed: {exc}") from exc

    def sm2_decrypt(self, private_key: Any, ciphertext: bytes) -> bytes:
        try:
            return bytes(private_key.decrypt(ciphertext))
        except Exception as exc:
            raise CryptoOperationError(f"SM2 decryption failed: {exc}") from exc

    def sm4_gcm_encrypt_stream(
        self,
        key: bytes,
        iv: bytes,
        aad: bytes,
        source: BinaryIO,
        sink: BinaryIO,
        *,
        chunk_size: int,
    ) -> int:
        self._validate_gcm_inputs(key, iv, chunk_size)
        written = 0
        try:
            ctx = self.gmssl.Sm4Gcm(
                key,
                iv,
                aad,
                self.sm4_gcm_tag_size,
                self.gmssl.DO_ENCRYPT,
            )
            while True:
                chunk = source.read(chunk_size)
                if not chunk:
                    break
                out = bytes(ctx.update(chunk))
                sink.write(out)
                written += len(out)
            tail = bytes(ctx.finish())
            sink.write(tail)
            written += len(tail)
            return written
        except Exception as exc:
            raise CryptoOperationError(f"SM4-GCM encryption failed: {exc}") from exc

    def sm4_gcm_decrypt_stream(
        self,
        key: bytes,
        iv: bytes,
        aad: bytes,
        source: BinaryIO,
        sink: BinaryIO,
        *,
        chunk_size: int,
    ) -> int:
        self._validate_gcm_inputs(key, iv, chunk_size)
        written = 0
        try:
            ctx = self.gmssl.Sm4Gcm(
                key,
                iv,
                aad,
                self.sm4_gcm_tag_size,
                self.gmssl.DO_DECRYPT,
            )
            while True:
                chunk = source.read(chunk_size)
                if not chunk:
                    break
                out = bytes(ctx.update(chunk))
                sink.write(out)
                written += len(out)
            # Authentication is checked by GmSSL when finish() is called.
            tail = bytes(ctx.finish())
            sink.write(tail)
            written += len(tail)
            return written
        except Exception as exc:
            raise CryptoOperationError(
                f"SM4-GCM decryption/authentication failed: {exc}"
            ) from exc

    def _validate_gcm_inputs(self, key: bytes, iv: bytes, chunk_size: int) -> None:
        if len(key) != self.sm4_key_size:
            raise CryptoOperationError(
                f"SM4 key must be {self.sm4_key_size} bytes, got {len(key)}"
            )
        if len(iv) != self.sm4_gcm_iv_size:
            raise CryptoOperationError(
                f"SM4-GCM IV must be {self.sm4_gcm_iv_size} bytes, got {len(iv)}"
            )
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
