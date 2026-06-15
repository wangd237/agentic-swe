"""精确文件编辑工具实现。"""

from __future__ import annotations

from app.tools.common import resolve_repo_relative_path, resolve_repo_path
from app.tools.write_file import _remove_parent_pycache_dirs


def _line_number_for_index(content: str, index: int) -> int:
    return content.count("\n", 0, index) + 1


def _context_for_line(lines: list[str], line_number: int, *, radius: int = 2) -> str:
    start = max(line_number - radius, 1)
    end = min(line_number + radius, len(lines))
    return "\n".join(
        f"{current_line}: {lines[current_line - 1]}"
        for current_line in range(start, end + 1)
    )


def _match_contexts(content: str, old_string: str) -> list[dict]:
    lines = content.splitlines()
    contexts: list[dict] = []
    start_index = 0
    while True:
        match_index = content.find(old_string, start_index)
        if match_index == -1:
            break
        line_number = _line_number_for_index(content, match_index)
        contexts.append(
            {
                "line_number": line_number,
                "context": _context_for_line(lines, line_number),
            }
        )
        start_index = match_index + max(len(old_string), 1)
    return contexts


def edit_file(repo_path: str, relative_path: str, old_string: str, new_string: str) -> dict:
    try:
        resolved_repo_path = resolve_repo_path(repo_path)
        target_path = resolve_repo_relative_path(resolved_repo_path, relative_path)
        if not target_path.exists():
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        if not target_path.is_file():
            raise IsADirectoryError(f"目标不是文件: {relative_path}")
        if old_string == "":
            return {
                "ok": False,
                "tool_name": "edit_file",
                "summary": "old_string 不能为空。",
                "data": {
                    "repo_path": str(resolved_repo_path),
                    "relative_path": str(relative_path).replace("\\", "/"),
                    "old_length": 0,
                    "new_length": len(new_string),
                },
                "error": {
                    "type": "empty_old_string",
                    "message": "old_string 不能为空。",
                },
            }

        content = target_path.read_text(encoding="utf-8")
        replacement_count = content.count(old_string)
        normalized_relative_path = str(relative_path).replace("\\", "/")
        if replacement_count == 0:
            return {
                "ok": False,
                "tool_name": "edit_file",
                "summary": f"未在 {relative_path} 中找到 old_string。",
                "data": {
                    "repo_path": str(resolved_repo_path),
                    "relative_path": normalized_relative_path,
                    "old_length": len(old_string),
                    "new_length": len(new_string),
                    "replacement_count": 0,
                },
                "error": {
                    "type": "old_string_not_found",
                    "message": "old_string 不存在，请读取文件后提供精确原文。",
                },
            }
        if replacement_count > 1:
            contexts = _match_contexts(content, old_string)
            return {
                "ok": False,
                "tool_name": "edit_file",
                "summary": f"old_string 在 {relative_path} 中匹配 {replacement_count} 次，请提供更精确上下文。",
                "data": {
                    "repo_path": str(resolved_repo_path),
                    "relative_path": normalized_relative_path,
                    "old_length": len(old_string),
                    "new_length": len(new_string),
                    "replacement_count": replacement_count,
                    "matches": contexts,
                },
                "error": {
                    "type": "old_string_not_unique",
                    "message": "old_string 不唯一，请包含更多上下文后重试。",
                },
            }

        match_index = content.index(old_string)
        line_number = _line_number_for_index(content, match_index)
        updated_content = content.replace(old_string, new_string, 1)
        target_path.write_text(updated_content, encoding="utf-8")
        removed_pycache_count = _remove_parent_pycache_dirs(resolved_repo_path, target_path)
        return {
            "ok": True,
            "tool_name": "edit_file",
            "summary": f"已编辑文件 {relative_path} 第 {line_number} 行附近。",
            "data": {
                "repo_path": str(resolved_repo_path),
                "relative_path": normalized_relative_path,
                "line_number": line_number,
                "replacement_count": 1,
                "old_length": len(old_string),
                "new_length": len(new_string),
                "removed_pycache_count": removed_pycache_count,
            },
            "error": None,
        }
    except FileNotFoundError as error:
        return {
            "ok": False,
            "tool_name": "edit_file",
            "summary": "文件或仓库路径不存在，无法编辑文件。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "not_found", "message": str(error)},
        }
    except IsADirectoryError as error:
        return {
            "ok": False,
            "tool_name": "edit_file",
            "summary": "目标不是文件。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "invalid_path", "message": str(error)},
        }
    except NotADirectoryError as error:
        return {
            "ok": False,
            "tool_name": "edit_file",
            "summary": "给定路径不是仓库目录。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "invalid_path", "message": str(error)},
        }
    except ValueError as error:
        return {
            "ok": False,
            "tool_name": "edit_file",
            "summary": "目标文件路径超出仓库边界。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "path_escape", "message": str(error)},
        }
    except UnicodeDecodeError as error:
        return {
            "ok": False,
            "tool_name": "edit_file",
            "summary": "目标文件不是 UTF-8 文本，无法安全编辑。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "decode_error", "message": str(error)},
        }
    except Exception as error:
        return {
            "ok": False,
            "tool_name": "edit_file",
            "summary": "编辑文件时发生异常。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "unknown_error", "message": str(error)},
        }
