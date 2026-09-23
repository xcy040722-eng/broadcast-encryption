"""SM2 + SM4 multi-recipient hybrid encryption backend."""

from .gmssl_backend import GmsslBackend
from .package import inspect_package
from .service import (
    decrypt_media,
    encrypt_media,
    force_try_wrapped_key,
    generate_encryption_material,
    generate_user_keys,
    unwrap_content_key,
    wrap_content_key,
)
from .types import DecryptResult, DecryptStatus, EncryptResult

__all__ = [
    "GmsslBackend",
    "DecryptResult",
    "DecryptStatus",
    "EncryptResult",
    "generate_user_keys",
    "generate_encryption_material",
    "wrap_content_key",
    "unwrap_content_key",
    "encrypt_media",
    "decrypt_media",
    "force_try_wrapped_key",
    "inspect_package",
]
