"""Command-line smoke-test interface for the backend."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .gmssl_backend import GmsslBackend
from .package import inspect_package
from .service import (
    decrypt_media,
    encrypt_media,
    force_try_wrapped_key,
    generate_user_keys,
)


def _parse_recipient(text: str) -> tuple[str, Path]:
    if "=" not in text:
        raise argparse.ArgumentTypeError("recipient must be USER_ID=PUBLIC_KEY_PEM")
    user_id, path = text.split("=", 1)
    if not user_id or not path:
        raise argparse.ArgumentTypeError("recipient must be USER_ID=PUBLIC_KEY_PEM")
    return user_id, Path(path)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sm2-sm4-mre")
    sub = p.add_subparsers(dest="command", required=True)

    keygen = sub.add_parser("keygen", help="generate one password-protected SM2 key pair")
    keygen.add_argument("--user", required=True)
    keygen.add_argument("--password", required=True)
    keygen.add_argument("--key-root", type=Path, default=Path("keys"))

    enc = sub.add_parser("encrypt", help="create one .smre package")
    enc.add_argument("--input", type=Path, required=True)
    enc.add_argument("--output", type=Path, required=True)
    enc.add_argument(
        "--recipient",
        action="append",
        type=_parse_recipient,
        required=True,
        help="repeatable USER_ID=PUBLIC_KEY_PEM",
    )

    dec = sub.add_parser("decrypt", help="decrypt as one recipient")
    dec.add_argument("--package", type=Path, required=True)
    dec.add_argument("--user", required=True)
    dec.add_argument("--private-key", type=Path, required=True)
    dec.add_argument("--password", required=True)
    dec.add_argument("--output", type=Path, required=True)

    inspect = sub.add_parser("inspect", help="show public package metadata")
    inspect.add_argument("--package", type=Path, required=True)

    force = sub.add_parser("force-try", help="try another recipient's wrapped key with the attacker's private key")
    force.add_argument("--package", type=Path, required=True)
    force.add_argument("--attacker-user", required=True)
    force.add_argument("--attacker-private-key", type=Path, required=True)
    force.add_argument("--password", required=True)
    force.add_argument("--target-recipient", required=True)
    force.add_argument("--output", type=Path, required=True)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    backend = GmsslBackend()

    if args.command == "keygen":
        result = generate_user_keys(
            args.user, args.password, args.key_root, backend=backend
        )
        print(json.dumps({
            "user_id": result.user_id,
            "public_key": str(result.public_key),
            "private_key": str(result.private_key),
        }, ensure_ascii=False, indent=2))
        return 0

    if args.command == "encrypt":
        recipients = dict(args.recipient)
        result = encrypt_media(args.input, recipients, args.output, backend=backend)
        print(json.dumps(result.trace.to_dict(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "decrypt":
        result = decrypt_media(
            args.package,
            args.user,
            args.private_key,
            args.password,
            args.output,
            backend=backend,
        )
        print(json.dumps({
            "status": result.status.value,
            "message": result.message,
            "output_path": str(result.output_path) if result.output_path else None,
            "trace": result.trace.to_dict(),
        }, ensure_ascii=False, indent=2))
        return 0 if result.status.value == "SUCCESS" else 2

    if args.command == "inspect":
        manifest = inspect_package(args.package)
        print(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "force-try":
        result = force_try_wrapped_key(
            args.package,
            attacker_user_id=args.attacker_user,
            attacker_private_key_path=args.attacker_private_key,
            password=args.password,
            target_recipient_id=args.target_recipient,
            output_path=args.output,
            backend=backend,
        )
        print(json.dumps({
            "status": result.status.value,
            "message": result.message,
            "trace": result.trace.to_dict(),
        }, ensure_ascii=False, indent=2))
        return 0 if result.status.value == "SUCCESS" else 2

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
