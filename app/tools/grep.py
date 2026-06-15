"""正则代码搜索工具实现。"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from app.tools.common import is_likely_text_file, resolve_repo_path, should_skip_path


def _matches_glob(relative_path: str, glob_pattern: str | None) -> bool:
    if not glob_pattern:
        return True
    return fnmatch.fnmatch(relative_path, glob_pattern) or fnmatch.fnmatch(Path(relative_path).name, glob_pattern)


def grep(repo_path: str, pattern: str, glob: str | None = None, max_results: int = 20) -> dict:
    # 使用 Python re 实现跨平台正则搜索，避免依赖 GNU grep 或 ripgrep。
    try:
        resolved_repo_path = resolve_repo_path(repo_path)
        normalized_pattern = pattern.strip()
        if not normalized_pattern:
            return {
                "ok": False,
                "tool_name": "grep",
                "summary": "正则表达式为空，无法执行搜索。",
                "data": {"repo_path": str(resolved_repo_path), "pattern": pattern, "glob": glob},
                "error": {"type": "invalid_pattern", "message": "pattern 不能为空。"},
            }
        try:
            compiled_pattern = re.compile(normalized_pattern)
        except re.error as error:
            return {
                "ok": False,
                "tool_name": "grep",
                "summary": "正则表达式无效，无法执行搜索。",
                "data": {"repo_path": str(resolved_repo_path), "pattern": pattern, "glob": glob},
                "error": {"type": "invalid_pattern", "message": str(error)},
            }

        max_results = max(int(max_results), 1)
        matches: list[dict] = []
        total_match_count = 0
        for path in sorted(resolved_repo_path.rglob("*")):
            if not path.is_file():
                continue
            relative_path = path.relative_to(resolved_repo_path)
            normalized_relative_path = str(relative_path).replace("\\", "/")
            if (
                should_skip_path(relative_path)
                or not is_likely_text_file(path)
                or not _matches_glob(normalized_relative_path, glob)
            ):
                continue

            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue

            for line_number, line_text in enumerate(lines, start=1):
                if not compiled_pattern.search(line_text):
                    continue
                total_match_count += 1
                if len(matches) >= max_results:
                    continue
                matches.append(
                    {
                        "relative_path": normalized_relative_path,
                        "line_number": line_number,
                        "line_text": line_text.strip(),
                    }
                )

        match_files = sorted({match["relative_path"] for match in matches})
        truncated = total_match_count > len(matches)
        return {
            "ok": True,
            "tool_name": "grep",
            "summary": (
                f"正则 `{normalized_pattern}` 命中 {total_match_count} 处，"
                f"返回 {len(matches)} 处，涉及 {len(match_files)} 个文件。"
            ),
            "data": {
                "repo_path": str(resolved_repo_path),
                "pattern": normalized_pattern,
                "glob": glob,
                "matches": matches,
                "match_count": total_match_count,
                "returned_match_count": len(matches),
                "match_files": match_files,
                "truncated": truncated,
            },
            "error": None,
        }
    except FileNotFoundError as error:
        return {
            "ok": False,
            "tool_name": "grep",
            "summary": "仓库路径不存在，无法搜索代码。",
            "data": {"repo_path": repo_path, "pattern": pattern, "glob": glob},
            "error": {"type": "not_found", "message": str(error)},
        }
    except NotADirectoryError as error:
        return {
            "ok": False,
            "tool_name": "grep",
            "summary": "给定路径不是仓库目录。",
            "data": {"repo_path": repo_path, "pattern": pattern, "glob": glob},
            "error": {"type": "invalid_path", "message": str(error)},
        }
    except Exception as error:
        return {
            "ok": False,
            "tool_name": "grep",
            "summary": "正则搜索时发生异常。",
            "data": {"repo_path": repo_path, "pattern": pattern, "glob": glob},
            "error": {"type": "unknown_error", "message": str(error)},
        }
