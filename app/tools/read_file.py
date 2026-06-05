"""读取文件工具实现。"""

from app.tools.common import resolve_repo_relative_path, resolve_repo_path


def read_file(repo_path: str, relative_path: str, max_chars: int = 6000) -> dict:
    # 第一版允许对长文件做截断，避免观察阶段一次读入过多内容。
    try:
        resolved_repo_path = resolve_repo_path(repo_path)
        target_path = resolve_repo_relative_path(resolved_repo_path, relative_path)
        if not target_path.exists():
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        if not target_path.is_file():
            raise IsADirectoryError(f"目标不是文件: {relative_path}")

        content = target_path.read_text(encoding="utf-8")
        truncated = len(content) > max_chars
        returned_content = content[:max_chars] if truncated else content

        return {
            "ok": True,
            "tool_name": "read_file",
            "summary": f"已读取文件 {relative_path}，共 {len(content.splitlines())} 行。",
            "data": {
                "repo_path": str(resolved_repo_path),
                "relative_path": str(relative_path).replace("\\", "/"),
                "content": returned_content,
                "line_count": len(content.splitlines()),
                "char_count": len(content),
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
