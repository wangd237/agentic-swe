"""文件写入工具实现。"""

import shutil

from app.tools.common import resolve_repo_relative_path, resolve_repo_path


def _remove_parent_pycache_dirs(resolved_repo_path, target_path) -> int:
    removed_count = 0
    current_dir = target_path.parent
    while current_dir.is_relative_to(resolved_repo_path):
        pycache_dir = current_dir / "__pycache__"
        if pycache_dir.exists():
            shutil.rmtree(pycache_dir, ignore_errors=True)
            removed_count += 1
        if current_dir == resolved_repo_path:
            break
        current_dir = current_dir.parent
    return removed_count


def write_file(repo_path: str, relative_path: str, content: str) -> dict:
    # 当前实现只允许写入给定 repo 目录内部，后续 patch 闭环会复用它。
    try:
        resolved_repo_path = resolve_repo_path(repo_path)
        target_path = resolve_repo_relative_path(resolved_repo_path, relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        removed_pycache_count = _remove_parent_pycache_dirs(resolved_repo_path, target_path)
        return {
            "ok": True,
            "tool_name": "write_file",
            "summary": f"已写入文件 {relative_path}。",
            "data": {
                "repo_path": str(resolved_repo_path),
                "relative_path": str(relative_path).replace("\\", "/"),
                "content_length": len(content),
                "removed_pycache_count": removed_pycache_count,
            },
            "error": None,
        }
    except FileNotFoundError as error:
        return {
            "ok": False,
            "tool_name": "write_file",
            "summary": "仓库路径不存在，无法写入文件。",
            "data": {"repo_path": repo_path, "relative_path": relative_path, "content_length": len(content)},
            "error": {"type": "not_found", "message": str(error)},
        }
    except NotADirectoryError as error:
        return {
            "ok": False,
            "tool_name": "write_file",
            "summary": "给定路径不是仓库目录。",
            "data": {"repo_path": repo_path, "relative_path": relative_path, "content_length": len(content)},
            "error": {"type": "invalid_path", "message": str(error)},
        }
    except ValueError as error:
        return {
            "ok": False,
            "tool_name": "write_file",
            "summary": "目标文件路径超出仓库边界。",
            "data": {"repo_path": repo_path, "relative_path": relative_path, "content_length": len(content)},
            "error": {"type": "path_escape", "message": str(error)},
        }
    except Exception as error:
        return {
            "ok": False,
            "tool_name": "write_file",
            "summary": "写入文件时发生异常。",
            "data": {"repo_path": repo_path, "relative_path": relative_path, "content_length": len(content)},
            "error": {"type": "unknown_error", "message": str(error)},
        }
