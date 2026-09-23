"""Run the SM2 + SM4 PySide6 workbench."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .window import WorkbenchWindow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sm2-sm4-workbench")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.home() / ".sm2-sm4-workbench",
        help="directory for generated test keys, staging payloads and packages",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = WorkbenchWindow(workspace=args.workspace)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
