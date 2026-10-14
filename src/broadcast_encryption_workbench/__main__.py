"""Run the unified broadcast-encryption course workbench."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .launcher import BroadcastEncryptionLauncher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="broadcast-encryption-workbench")
    parser.add_argument(
        "--lang",
        choices=("zh_CN", "en_US"),
        default="zh_CN",
        help="UI language",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.home() / ".broadcast-encryption-workbench" / "sm2-sm4",
        help="SM2+SM4 workspace for generated demo keys, payloads, and packages",
    )
    parser.add_argument(
        "--cs-users",
        type=int,
        default=8,
        help="Complete Subtree user count; must be a power of two",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    launcher = BroadcastEncryptionLauncher(
        language=args.lang,
        workspace=args.workspace,
        cs_users=args.cs_users,
    )
    launcher.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
