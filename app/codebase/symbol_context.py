"""Attach enclosing Python symbols to text-search hits.

Symbol names and locations are navigation hints, not semantic proof of relevance.
Invalid Python files safely fall back to ordinary line matches.
"""

from __future__ import annotations

import ast
from typing import Any


class _SymbolSpans(ast.NodeVisitor):
    def __init__(self) -> None:
        self.scope: list[str] = []
        self.spans: list[tuple[int, int, str]] = []

    def _visit_named(self, node: ast.AST) -> None:
        name = getattr(node, "name")
        self.scope.append(name)
        start = getattr(node, "lineno")
        end = getattr(node, "end_lineno", None) or start
        self.spans.append((start, end, ".".join(self.scope)))
        self.generic_visit(node)
        self.scope.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_named(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_named(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_named(node)


def annotate_python_matches(source: str, matches: list[dict[str, Any]]) -> None:
    """Annotate matches in place with the innermost enclosing class/function."""
    if not matches:
        return
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return

    visitor = _SymbolSpans()
    visitor.visit(tree)
    for match in matches:
        line = int(match["line_number"])
        containing = [
            span for span in visitor.spans if span[0] <= line <= span[1]
        ]
        if not containing:
            continue
        start, end, name = min(containing, key=lambda span: (span[1] - span[0], -span[0]))
        match["symbol"] = name
        match["symbol_range"] = [start, end]
