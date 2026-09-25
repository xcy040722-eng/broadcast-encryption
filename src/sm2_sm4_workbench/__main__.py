"""Run the SM2 + SM4 PySide6 workbench."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .defense_workbench import DefenseWorkbenchWindow
from .i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sm2-sm4-workbench")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.home() / ".sm2-sm4-workbench",
        help="directory for generated test keys, staging payloads and packages",
    )
    parser.add_argument(
        "--lang",
        choices=SUPPORTED_LANGUAGES,
        default=DEFAULT_LANGUAGE,
        help="UI language; use en_US if the desktop has no usable Chinese font",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = DefenseWorkbenchWindow(workspace=args.workspace, language=args.lang)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
