"""文件级混合广播加密（NNL01-CS + AES-256-GCM）。

在已冻结的 CS Baseline 之上提供 encrypt_file / decrypt_file，
形成完整的文件加密闭环。不修改 src/cs/ 核心算法。
"""

from .crypto import encrypt_body, decrypt_body
from .format import (
    ALGORITHM,
    VERSION,
    DecryptionError,
    InvalidPackageError,
    build_aad,
    build_package,
    deserialize_package,
    serialize_package,
)
from .encrypt_file import encrypt_file
from .decrypt_file import decrypt_file

__all__ = [
    "encrypt_file",
    "decrypt_file",
    "encrypt_body",
    "decrypt_body",
    "ALGORITHM",
    "VERSION",
    "DecryptionError",
    "InvalidPackageError",
    "build_aad",
    "build_package",
    "deserialize_package",
    "serialize_package",
]
