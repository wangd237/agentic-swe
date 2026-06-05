"""查看差异工具实现。"""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path

from app.tools.common import is_likely_text_file, resolve_repo_path, should_skip_path


def _collect_text_files(repo_path: Path) -> dict[str, Path]:
    # diff 只关注文本文件，并忽略缓存目录等明显无关内容。
    collected_files: dict[str, Path] = {}
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(repo_path)
        if should_skip_path(relative_path) or not is_likely_text_file(path):
            continue
        collected_files[str(relative_path).replace("\\", "/")] = path
    return collected_files


def show_diff(repo_path: str, original_repo_path: str | None = None) -> dict:
    # 当前 diff 通过原仓库与工作副本做统一 diff，用于生成 patch.diff。
    try:
        resolved_repo_path = resolve_repo_path(repo_path)
        if original_repo_path is None:
            return {
                "ok": False,
                "tool_name": "show_diff",
                "summary": "未提供原始仓库路径，无法生成差异。",
                "data": {"repo_path": str(resolved_repo_path), "diff_text": ""},
                "error": {"type": "missing_original_repo", "message": "original_repo_path 不能为空。"},
            }

        resolved_original_repo_path = resolve_repo_path(original_repo_path)
        original_files = _collect_text_files(resolved_original_repo_path)
        updated_files = _collect_text_files(resolved_repo_path)

        all_relative_paths = sorted(set(original_files) | set(updated_files))
        diff_chunks: list[str] = []
        changed_files: list[str] = []

        for relative_path in all_relative_paths:
            original_path = original_files.get(relative_path)
            updated_path = updated_files.get(relative_path)

            original_lines = (
                original_path.read_text(encoding="utf-8").splitlines(keepends=True)
                if original_path else []
            )
            updated_lines = (
                updated_path.read_text(encoding="utf-8").splitlines(keepends=True)
                if updated_path else []
            )

            if original_lines == updated_lines:
                continue

            changed_files.append(relative_path)
            diff_chunks.extend(
                unified_diff(
                    original_lines,
                    updated_lines,
                    fromfile=f"a/{relative_path}",
                    tofile=f"b/{relative_path}",
                )
            )

        diff_text = "".join(diff_chunks)
        return {
            "ok": True,
            "tool_name": "show_diff",
            "summary": f"共检测到 {len(changed_files)} 个变更文件。",
            "data": {
                "repo_path": str(resolved_repo_path),
                "original_repo_path": str(resolved_original_repo_path),
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
