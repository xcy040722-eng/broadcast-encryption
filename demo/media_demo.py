"""媒体文件加密/解密闭环 Demo。

演示 PNG / JPEG / MP4 三个媒体文件的完整闭环：
  文件 → AES-GCM 加密 → CS 广播加密文件密钥 → 授权恢复 → 文件解密

并验证：
  - authorized 用户能恢复 K 并得到正确原文件；
  - revoked 用户无法恢复 K（DecryptionError）。
"""

from __future__ import annotations

import hashlib
import os
import tempfile

from src.cs.keys import keygen, setup
from src.file_crypto import DecryptionError, decrypt_file, encrypt_file
from demo.media_data import MEDIA


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def run_demo(tree, node_keys, revoked_users: set[int]) -> dict:
    """跑一次媒体加密闭环，返回每个媒体的结果。"""
    results = {}
    tmp = tempfile.mkdtemp()
    for name, data in MEDIA.items():
        src = os.path.join(tmp, f"{name}.bin")
        enc = os.path.join(tmp, f"{name}.enc")
        with open(src, "wb") as f:
            f.write(data)

        # 加密
        encrypt_file(src, enc, tree, node_keys, revoked_users)

        # 授权用户（取第一个非撤销用户）解密
        u_auth = next(u for u in range(1, tree.N + 1) if u not in revoked_users)
        out = os.path.join(tmp, f"{name}.out")
        decrypt_file(enc, out, keygen(tree, node_keys, u_auth))
        with open(out, "rb") as f:
            decrypted = f.read()

        # revoked 用户解密应失败
        revoked_failed = False
        if revoked_users:
            u_rev = sorted(revoked_users)[0]
            try:
                decrypt_file(enc, os.path.join(tmp, f"{name}.revoked"), keygen(tree, node_keys, u_rev))
            except DecryptionError:
                revoked_failed = True

        results[name] = {
            "size": len(data),
            "encrypted_size": os.path.getsize(enc),
            "authorized_ok": sha256(decrypted) == sha256(data),
            "revoked_rejected": revoked_failed,
        }
    return results


def main() -> None:
    tree, node_keys = setup(8)
    revoked = {3}

    print("=== 媒体加密闭环 Demo（N=8, 撤销 u3）===\n")
    results = run_demo(tree, node_keys, revoked)
    for name, r in results.items():
        print(f"  {name}:")
        print(f"    原文件 {r['size']} B -> 密文 {r['encrypted_size']} B")
        print(f"    authorized 恢复: {'OK' if r['authorized_ok'] else 'FAIL'}")
        print(f"    revoked 拒绝:   {'OK' if r['revoked_rejected'] else 'FAIL'}")
        print()

    all_ok = all(r["authorized_ok"] and r["revoked_rejected"] for r in results.values())
    print(f"=== Demo 完成：{'全部通过' if all_ok else '存在失败'} ===")


if __name__ == "__main__":
    main()
