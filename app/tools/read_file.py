"""读取文件工具实现。"""

from app.tools.common import resolve_repo_relative_path, resolve_repo_path


class InvalidLineRangeError(ValueError):
    """Raised when a requested line range is invalid."""


def _normalize_line_range(
    *,
    start_line: int | None,
    end_line: int | None,
    total_lines: int,
) -> tuple[int, int] | None:
    if start_line is None and end_line is None:
        return None

    normalized_start = 1 if start_line is None else start_line
    normalized_end = total_lines if end_line is None else end_line
    if normalized_start < 1:
        raise InvalidLineRangeError("start_line must be >= 1")
    if normalized_end < normalized_start:
        raise InvalidLineRangeError("end_line must be >= start_line")
    return normalized_start, min(normalized_end, total_lines)


def _slice_lines(content: str, *, start_line: int, end_line: int) -> str:
    lines = content.splitlines(keepends=True)
    return "".join(lines[start_line - 1:end_line])


def read_file(
    repo_path: str,
    relative_path: str,
    max_chars: int = 6000,
    start_line: int | None = None,
    end_line: int | None = None,
) -> dict:
    # 第一版允许对长文件做截断，避免观察阶段一次读入过多内容。
    try:
        resolved_repo_path = resolve_repo_path(repo_path)
        target_path = resolve_repo_relative_path(resolved_repo_path, relative_path)
        if not target_path.exists():
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        if not target_path.is_file():
            raise IsADirectoryError(f"目标不是文件: {relative_path}")

        content = target_path.read_text(encoding="utf-8")
        total_line_count = len(content.splitlines())
        line_range = _normalize_line_range(
            start_line=start_line,
            end_line=end_line,
            total_lines=total_line_count,
        )
        readable_content = (
            _slice_lines(content, start_line=line_range[0], end_line=line_range[1])
            if line_range
            else content
        )
        truncated = len(readable_content) > max_chars
        returned_content = readable_content[:max_chars] if truncated else readable_content
        line_range_summary = (
            f" 第 {line_range[0]}-{line_range[1]} 行"
            if line_range
            else ""
        )

        return {
            "ok": True,
            "tool_name": "read_file",
            "summary": f"已读取文件 {relative_path}{line_range_summary}，共 {total_line_count} 行。",
            "data": {
                "repo_path": str(resolved_repo_path),
                "relative_path": str(relative_path).replace("\\", "/"),
                "content": returned_content,
                "line_count": total_line_count,
                "start_line": line_range[0] if line_range else None,
                "end_line": line_range[1] if line_range else None,
                "char_count": len(content),
                "returned_line_count": len(returned_content.splitlines()),
                "truncated": truncated,
                "returned_char_count": len(returned_content),
            },
            "error": None,
        }
    except FileNotFoundError as error:
        return {
            "ok": False,
            "tool_name": "read_file",
            "summary": "目标文件不存在，无法读取。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "not_found", "message": str(error)},
        }
    except IsADirectoryError as error:
        return {
            "ok": False,
            "tool_name": "read_file",
            "summary": "目标路径是目录，不是文件。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "invalid_path", "message": str(error)},
        }
    except UnicodeDecodeError as error:
        return {
            "ok": False,
            "tool_name": "read_file",
            "summary": "文件不是可按 UTF-8 读取的文本文件。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "decode_error", "message": str(error)},
        }
    except InvalidLineRangeError as error:
        return {
            "ok": False,
            "tool_name": "read_file",
            "summary": "读取范围无效。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "invalid_line_range", "message": str(error)},
        }
    except ValueError as error:
        return {
            "ok": False,
            "tool_name": "read_file",
            "summary": "文件路径超出仓库边界。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "path_escape", "message": str(error)},
        }
    except Exception as error:
        return {
            "ok": False,
            "tool_name": "read_file",
            "summary": "读取文件时发生异常。",
            "data": {"repo_path": repo_path, "relative_path": relative_path},
            "error": {"type": "unknown_error", "message": str(error)},
        }
