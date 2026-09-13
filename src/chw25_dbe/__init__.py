"""CHW25 Construction 6.4 — Distributed Broadcast Encryption（教学实现）。

忠实保留论文的代数正确性结构（密钥关系、密文、解密、阈值判定）；
以 pedagogical substitution 取代正式格 trapdoor 与高斯采样（见 docs/chw25-dbe-implementation-spec.md）。

hybrid 层：CHW25 DBE → AES-256 session key → AES-GCM 文件。
"""

from .types import (
    Ciphertext,
    DecryptResult,
    FileResult,
    Params,
    PublicKey,
    PublicParams,
    SecretKey,
    SessionKeyResult,
)
from .construction import (
    decrypt,
    derive_rerandomization,
    encrypt,
    is_valid,
    keygen,
    setup,
)
from .trace import decrypt_with_trace
from .hybrid import (
    ALGORITHM,
    BIT_LEN,
    KEY_LEN,
    VERSION,
    KeysetMismatchError,
    bits_to_bytes,
    bytes_to_bits,
    build_package,
    decrypt_bit,
    decrypt_file_for_user,
    decrypt_session_key,
    deserialize_package,
    deserialize_wrapped_key,
    encrypt_file_for_set,
    encrypt_session_key,
    keyset_id,
    package_aad,
    params_id,
    serialize_package,
    serialize_wrapped_key,
)

__all__ = [
    # types
    "Params", "PublicParams", "PublicKey", "SecretKey", "Ciphertext",
    "DecryptResult", "SessionKeyResult", "FileResult",
    # 核心五算法
    "setup", "keygen", "is_valid", "encrypt", "decrypt",
    "derive_rerandomization", "decrypt_with_trace",
    # hybrid
    "VERSION", "ALGORITHM", "KEY_LEN", "BIT_LEN", "KeysetMismatchError",
    "bytes_to_bits", "bits_to_bytes", "params_id", "keyset_id",
    "decrypt_bit", "encrypt_session_key", "decrypt_session_key",
    "serialize_wrapped_key", "deserialize_wrapped_key",
    "serialize_package", "deserialize_package", "package_aad", "build_package",
    "encrypt_file_for_set", "decrypt_file_for_user",
]
