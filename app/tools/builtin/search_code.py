"""Literal code search with bounded, scoped and symbol-aware results."""

from __future__ import annotations

from app.codebase.symbol_context import annotate_python_matches
from app.tools.builtin.common import (
    is_likely_text_file,
    matches_search_glob,
    normalize_search_prefix,
    resolve_repo_path,
    should_skip_path,
)


def search_code(
    repo_path: str,
    query: str,
    glob: str | None = None,
    max_results: int = 50,
    path_prefix: str | None = None,
) -> dict:
    try:
        root = resolve_repo_path(repo_path)
        normalized_query = query.strip()
        if not normalized_query:
            return {
                "ok": False,
                "tool_name": "search_code",
                "summary": "搜索词为空，无法执行搜索代码。",
                "data": {"repo_path": str(root), "query": query},
                "error": {"type": "invalid_query", "message": "query 不能为空。"},
            }

        normalized_prefix = normalize_search_prefix(path_prefix)
        search_root = root / normalized_prefix if normalized_prefix else root
        if not search_root.resolve().is_relative_to(root):
            raise ValueError("path_prefix resolves outside the repository")
        candidates = sorted(search_root.rglob("*")) if search_root.is_dir() else [search_root]
        max_results = max(1, int(max_results))
        matches: list[dict] = []
        total_match_count = 0

        for path in candidates:
            if not path.is_file() or not path.resolve().is_relative_to(root):
                continue
            relative_path = path.relative_to(root)
            normalized_path = relative_path.as_posix()
            if (
                should_skip_path(relative_path)
                or not is_likely_text_file(path)
                or not matches_search_glob(normalized_path, glob)
            ):
                continue

            try:
                source = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            first_match_index = len(matches)
            for line_number, line_text in enumerate(source.splitlines(), start=1):
                if normalized_query not in line_text:
                    continue
                total_match_count += 1
                if len(matches) >= max_results:
                    continue
                matches.append({
                    "relative_path": normalized_path,
                    "line_number": line_number,
                    "line_text": line_text.strip(),
                })
            if path.suffix == ".py" and len(matches) > first_match_index:
                annotate_python_matches(source, matches[first_match_index:])

        match_files = sorted({match["relative_path"] for match in matches})
        return {
            "ok": True,
            "tool_name": "search_code",
            "summary": (
                f"搜索词 `{normalized_query}` 命中 {total_match_count} 处，"
                f"返回 {len(matches)} 处，涉及 {len(match_files)} 个文件。"
            ),
            "data": {
                "repo_path": str(root),
                "query": normalized_query,
                "glob": glob,
                "path_prefix": normalized_prefix,
                "matches": matches,
                "match_count": total_match_count,
                "returned_match_count": len(matches),
                "match_files": match_files,
                "truncated": total_match_count > len(matches),
            },
            "error": None,
        }
    except ValueError as error:
        return {
            "ok": False, "tool_name": "search_code", "summary": "搜索范围无效。",
            "data": {"query": query, "path_prefix": path_prefix},
            "error": {"type": "invalid_scope", "message": str(error)},
        }
    except (FileNotFoundError, NotADirectoryError) as error:
        return {
            "ok": False, "tool_name": "search_code", "summary": "仓库路径无效。",
            "data": {"repo_path": repo_path, "query": query},
            "error": {"type": "invalid_path", "message": str(error)},
        }
    except Exception as error:
        return {
            "ok": False, "tool_name": "search_code", "summary": "搜索代码时发生异常。",
            "data": {"repo_path": repo_path, "query": query},
            "error": {"type": "unknown_error", "message": str(error)},
        }
