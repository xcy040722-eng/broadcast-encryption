"""Run the unified Complete Subtree PySide6 workbench."""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from .i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from .window import CompleteSubtreeWorkbenchWindow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="complete-subtree-workbench")
    parser.add_argument("--n", type=int, default=8, help="number of users; must be a power of two")
    parser.add_argument(
        "--lang",
        choices=SUPPORTED_LANGUAGES,
        default=DEFAULT_LANGUAGE,
        help="UI language",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = CompleteSubtreeWorkbenchWindow(n=args.n, language=args.lang)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
