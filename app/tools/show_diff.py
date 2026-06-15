"""查看差异工具实现。"""

from __future__ import annotations

from app.runtime.git_workspace import diff_since_initial
from app.tools.common import resolve_repo_path


def show_diff(repo_path: str, original_repo_path: str | None = None) -> dict:
    # Git-backed workspace 以 initial tag 作为原始基线；original_repo_path 保留为兼容旧调用。
    try:
        resolved_repo_path = resolve_repo_path(repo_path)
        diff_text, changed_files = diff_since_initial(resolved_repo_path)

        return {
            "ok": True,
            "tool_name": "show_diff",
            "summary": f"共检测到 {len(changed_files)} 个变更文件。",
            "data": {
                "repo_path": str(resolved_repo_path),
                "original_repo_path": original_repo_path,
                "diff_text": diff_text,
                "changed_files": changed_files,
            },
            "error": None,
        }
    except Exception as error:
        return {
            "ok": False,
            "tool_name": "show_diff",
            "summary": "生成差异时发生异常。",
            "data": {"repo_path": repo_path, "original_repo_path": original_repo_path, "diff_text": ""},
            "error": {"type": "unknown_error", "message": str(error)},
        }
