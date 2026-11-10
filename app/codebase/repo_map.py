"""Compact, candidate-scoped AST outline for the first LLM request.

Only names and source locations are exposed. This is navigation context, not
proof that a candidate contains the bug.
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.codebase.locator import extract_issue_tokens
from app.core.state import LocalizationCandidate


def _outlined_symbols(path: Path, issue_tokens: set[str], limit: int) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []

    entries: list[tuple[int, int, str]] = []

    def visit(body: list[ast.stmt], prefix: str = "") -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualified = f"{prefix}.{node.name}" if prefix else node.name
                end_line = getattr(node, "end_lineno", node.lineno)
                kind = "class" if isinstance(node, ast.ClassDef) else "def"
                score = int(bool(set(qualified.lower().replace(".", "_").split("_")) & issue_tokens))
                entries.append((score, node.lineno, f"  {kind} {qualified}: L{node.lineno}-L{end_line}"))
                if isinstance(node, ast.ClassDef):
                    visit(node.body, qualified)

    visit(tree.body)
    entries.sort(key=lambda item: (-item[0], item[1]))
    return [entry[2] for entry in entries[:limit]]


def build_initial_repo_map(
    repo_path: str | Path,
    candidates: list[LocalizationCandidate],
    issue_text: str,
    *,
    max_files: int = 5,
    max_symbols_per_file: int = 8,
    max_chars: int = 2400,
) -> str:
    """Summarize ranked candidate files under an explicit prompt-size budget."""
    if not candidates or max_files <= 0 or max_chars <= 0:
        return ""

    root = Path(repo_path).resolve()
    issue_tokens = extract_issue_tokens(issue_text)
    sections: list[str] = []

    for candidate in candidates[:max_files]:
        relative_path = candidate.relative_path.replace("\\", "/")
        target = (root / relative_path).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            continue
        lines = [f"- {relative_path} (heuristic candidate, not verified)"]
        if target.suffix == ".py":
            lines.extend(_outlined_symbols(target, issue_tokens, max_symbols_per_file))
        section = "\n".join(lines)
        if len("\n".join(sections + [section])) > max_chars:
            break
        sections.append(section)

    if not sections:
        return ""
    return (
        "REPO_MAP (navigation hints only; confirm with grep/read_file/tests):\n"
        + "\n".join(sections)
    )[:max_chars]
