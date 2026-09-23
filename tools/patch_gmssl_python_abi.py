#!/usr/bin/env python3
"""Apply/verify the GmSSL-Python 2.2.2 ctypes ABI compatibility patch.

Why this exists
---------------
The course backend uses the official ``gmssl-python`` ctypes binding together
with a recent GmSSL native shared library.  With gmssl-python 2.2.2, two ctypes
structures used by this project are smaller than their native C counterparts:

* ``Sm2Key``: Python 96 bytes vs native 128 bytes
* ``Sm4Gcm``: Python 288 bytes vs native 296 bytes

Passing those undersized objects by reference lets native code write past the
Python object, causing delayed segmentation faults.  This script patches only
those two layouts, keeps a backup, is idempotent, and verifies the resulting
sizes in a fresh Python process before reporting success.

Supported project profile
-------------------------
* gmssl-python == 2.2.2
* 64-bit Linux/WSL
* native GmSSL commit pinned by ``scripts/bootstrap_gmssl_wsl.sh``

This is a project-local compatibility shim, not an upstream replacement.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

EXPECTED_BINDING_VERSION = "2.2.2"
EXPECTED_SM2KEY_SIZE = 128
EXPECTED_SM4GCM_SIZE = 296


class PatchError(RuntimeError):
    pass


def _gmssl_source_path() -> Path:
    spec = importlib.util.find_spec("gmssl")
    if spec is None or not spec.origin:
        raise PatchError(
            "Python module 'gmssl' is not installed. Install requirements-sm2-sm4.txt first."
        )
    path = Path(spec.origin).resolve()
    if path.name != "gmssl.py":
        raise PatchError(f"Unexpected gmssl module layout: {path}")
    return path


def _check_binding_version(source: str) -> None:
    m = re.search(r'GMSSL_PYTHON_VERSION\s*=\s*["\']([^"\']+)["\']', source)
    if not m:
        raise PatchError("Could not determine GMSSL_PYTHON_VERSION from gmssl.py")
    if m.group(1) != EXPECTED_BINDING_VERSION:
        raise PatchError(
            f"This patch targets gmssl-python {EXPECTED_BINDING_VERSION}, got {m.group(1)}. "
            "Do not apply it blindly to another version."
        )


def _patch_sm4_gcm(source: str) -> tuple[str, bool]:
    # Already fixed/upstream-compatible.
    block = re.search(
        r"class\s+Sm4Gcm\(Structure\):(?P<body>.*?)(?=\nclass\s+|\nSM2_DEFAULT_ID\s*=)",
        source,
        re.S,
    )
    if not block:
        raise PatchError("Could not locate class Sm4Gcm in gmssl.py")
    if re.search(r'\("encedlen"\s*,\s*c_uint64\)', block.group("body")):
        return source, False

    pattern = r'(\("maclen"\s*,\s*c_size_t\)\s*,?)'
    body = block.group("body")
    m = re.search(pattern, body)
    if not m:
        raise PatchError("Could not locate Sm4Gcm.maclen field")

    replacement = m.group(1)
    if not replacement.rstrip().endswith(","):
        replacement = replacement.rstrip() + ","
    replacement += '\n\t\t("encedlen", c_uint64)'
    new_body = body[: m.start()] + replacement + body[m.end() :]
    return source[: block.start("body")] + new_body + source[block.end("body") :], True


def _patch_sm2_key(source: str) -> tuple[str, bool]:
    key_block = re.search(
        r"class\s+Sm2Key\(Structure\):(?P<body>.*?)(?=\nclass\s+|\Z)",
        source,
        re.S,
    )
    if not key_block:
        raise PatchError("Could not locate class Sm2Key in gmssl.py")

    body = key_block.group("body")
    if re.search(r'\("public_key"\s*,\s*Sm2Z256Point\)', body):
        if "class Sm2Z256Point(Structure):" not in source:
            raise PatchError("Sm2Key references Sm2Z256Point but the class is missing")
        return source, False

    if not re.search(r'\("public_key"\s*,\s*Sm2Point\)', body):
        raise PatchError("Unexpected Sm2Key.public_key field; refusing a blind patch")

    if "class Sm2Z256Point(Structure):" not in source:
        insert_at = key_block.start()
        z256 = (
            "class Sm2Z256Point(Structure):\n"
            "\t_fields_ = [\n"
            "\t\t(\"X\", c_uint64 * 4),\n"
            "\t\t(\"Y\", c_uint64 * 4),\n"
            "\t\t(\"Z\", c_uint64 * 4)\n"
            "\t]\n\n\n"
        )
        source = source[:insert_at] + z256 + source[insert_at:]

    source, count = re.subn(
        r'\("public_key"\s*,\s*Sm2Point\)',
        '("public_key", Sm2Z256Point)',
        source,
        count=1,
    )
    if count != 1:
        raise PatchError("Failed to replace Sm2Key.public_key field")
    return source, True


def _fresh_process_check() -> tuple[bool, str]:
    code = f"""
import ctypes, gmssl, sys
pyver = getattr(gmssl, 'GMSSL_PYTHON_VERSION', '<missing>')
libver = getattr(gmssl, 'GMSSL_LIBRARY_VERSION', '<missing>')
s2 = ctypes.sizeof(gmssl.Sm2Key)
s4 = ctypes.sizeof(gmssl.Sm4Gcm)
print(f'gmssl-python={{pyver}} native={{libver}} Sm2Key={{s2}} Sm4Gcm={{s4}}')
if pyver != {EXPECTED_BINDING_VERSION!r} or s2 != {EXPECTED_SM2KEY_SIZE} or s4 != {EXPECTED_SM4GCM_SIZE}:
    sys.exit(3)
"""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=os.environ.copy(),
    )
    return proc.returncode == 0, proc.stdout.strip()


def check() -> int:
    path = _gmssl_source_path()
    source = path.read_text(encoding="utf-8")
    _check_binding_version(source)
    ok, output = _fresh_process_check()
    print(f"gmssl.py: {path}")
    print(output)
    if not ok:
        print("ABI CHECK: FAIL")
        return 1
    print("ABI CHECK: PASS")
    return 0


def apply() -> int:
    path = _gmssl_source_path()
    source = path.read_text(encoding="utf-8")
    _check_binding_version(source)

    backup = path.with_name(path.name + ".orig-2.2.2")
    if not backup.exists():
        shutil.copy2(path, backup)
        print(f"backup: {backup}")

    patched, changed_sm4 = _patch_sm4_gcm(source)
    patched, changed_sm2 = _patch_sm2_key(patched)

    if changed_sm4 or changed_sm2:
        path.write_text(patched, encoding="utf-8")
        print(
            "patched:",
            "Sm4Gcm" if changed_sm4 else "",
            "Sm2Key" if changed_sm2 else "",
        )
    else:
        print("patch already present; no source changes needed")

    ok, output = _fresh_process_check()
    print(output)
    if not ok:
        print("Fresh-process ABI verification failed; restoring backup.", file=sys.stderr)
        if backup.exists():
            shutil.copy2(backup, path)
        return 2

    print("ABI PATCH: PASS")
    return 0


def restore() -> int:
    path = _gmssl_source_path()
    backup = path.with_name(path.name + ".orig-2.2.2")
    if not backup.exists():
        raise PatchError(f"Backup does not exist: {backup}")
    shutil.copy2(backup, path)
    print(f"restored {path} from {backup}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="verify ABI only")
    group.add_argument("--restore", action="store_true", help="restore backup")
    args = parser.parse_args(argv)

    try:
        if args.check:
            return check()
        if args.restore:
            return restore()
        return apply()
    except PatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
