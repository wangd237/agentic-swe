"""代码搜索工具实现。"""

from app.tools.common import is_likely_text_file, resolve_repo_path, should_skip_path


def search_code(repo_path: str, query: str) -> dict:
    # 第一版只做简单文本搜索，返回命中文件、行号和摘要片段。
    try:
        resolved_repo_path = resolve_repo_path(repo_path)
        normalized_query = query.strip()
        if not normalized_query:
            return {
                "ok": False,
                "tool_name": "search_code",
                "summary": "搜索词为空，无法执行搜索。",
                "data": {"repo_path": str(resolved_repo_path), "query": query},
                "error": {"type": "invalid_query", "message": "query 不能为空。"},
            }

        matches: list[dict] = []
        for path in resolved_repo_path.rglob("*"):
            if not path.is_file():
                continue
            relative_path = path.relative_to(resolved_repo_path)
            if should_skip_path(relative_path) or not is_likely_text_file(path):
                continue

            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue

            for line_number, line_text in enumerate(lines, start=1):
                if normalized_query in line_text:
                    matches.append(
                        {
                            "relative_path": str(relative_path).replace("\\", "/"),
                            "line_number": line_number,
                            "line_text": line_text.strip(),
                        }
                    )

        match_files = sorted({match["relative_path"] for match in matches})
        return {
            "ok": True,
            "tool_name": "search_code",
            "summary": f"搜索词 `{normalized_query}` 命中 {len(matches)} 处，涉及 {len(match_files)} 个文件。",
            "data": {
                "repo_path": str(resolved_repo_path),
                "query": normalized_query,
                "matches": matches,
                "match_count": len(matches),
                "match_files": match_files,
            },
            "error": None,
        }
    except FileNotFoundError as error:
        return {
            "ok": False,
            "tool_name": "search_code",
            "summary": "仓库路径不存在，无法搜索代码。",
            "data": {"repo_path": repo_path, "query": query},
            "error": {"type": "not_found", "message": str(error)},
        }
    except NotADirectoryError as error:
        return {
            "ok": False,
            "tool_name": "search_code",
            "summary": "给定路径不是仓库目录。",
            "data": {"repo_path": repo_path, "query": query},
            "error": {"type": "invalid_path", "message": str(error)},
        }
    except Exception as error:
        return {
            "ok": False,
            "tool_name": "search_code",
            "summary": "搜索代码时发生异常。",
            "data": {"repo_path": repo_path, "query": query},
            "error": {"type": "unknown_error", "message": str(error)},
        }
