"""列出仓库文件工具实现。"""

from pathlib import Path

from app.tools.common import resolve_repo_path, should_skip_path


def list_files(repo_path: str, recursive: bool = True) -> dict:
    # 当前实现返回相对路径列表，供观察型 Agent 快速了解仓库结构。
    try:
        resolved_repo_path = resolve_repo_path(repo_path)
        if recursive:
            candidates = [path for path in resolved_repo_path.rglob("*") if path.is_file()]
        else:
            candidates = [path for path in resolved_repo_path.iterdir() if path.is_file()]

        relative_paths = [
            str(path.relative_to(resolved_repo_path)).replace("\\", "/")
            for path in candidates
            if not should_skip_path(path.relative_to(resolved_repo_path))
        ]
        relative_paths.sort()

        return {
            "ok": True,
            "tool_name": "list_files",
            "summary": f"共找到 {len(relative_paths)} 个文件。",
            "data": {
                "repo_path": str(resolved_repo_path),
                "recursive": recursive,
                "files": relative_paths,
                "count": len(relative_paths),
            },
            "error": None,
        }
    except FileNotFoundError as error:
        return {
            "ok": False,
            "tool_name": "list_files",
            "summary": "仓库路径不存在，无法列出文件。",
            "data": {"repo_path": repo_path, "recursive": recursive},
            "error": {"type": "not_found", "message": str(error)},
        }
    except NotADirectoryError as error:
        return {
            "ok": False,
            "tool_name": "list_files",
            "summary": "给定路径不是仓库目录。",
            "data": {"repo_path": repo_path, "recursive": recursive},
            "error": {"type": "invalid_path", "message": str(error)},
        }
    except Exception as error:
        return {
            "ok": False,
            "tool_name": "list_files",
            "summary": "列出仓库文件时发生异常。",
            "data": {"repo_path": repo_path, "recursive": recursive},
            "error": {"type": "unknown_error", "message": str(error)},
        }
