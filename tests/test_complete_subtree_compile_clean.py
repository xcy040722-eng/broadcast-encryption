from __future__ import annotations

from pathlib import Path
import warnings


def test_complete_subtree_sources_compile_without_syntaxwarning():
    root = Path(__file__).resolve().parents[1]
    targets = (
        root / "src" / "complete_subtree_mre" / "cover.py",
        root / "src" / "complete_subtree_mre" / "service.py",
    )
    for path in targets:
        source = path.read_text(encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("error", SyntaxWarning)
            compile(source, str(path), "exec")
