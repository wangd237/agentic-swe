"""最小 patch 生成与应用逻辑。

历史说明：本模块曾承载 68 个 improved_v* 策略版本（约 4700 行），
2026-08-31 瘦身为保留代表性基线：baseline 链（空输入保护）与
improved_v70/v71/v72（anyio 并发与 rich Windows 分支）。
完整演进历史见 git log（`git log --follow -- app/agent/patcher.py`）。
"""

from __future__ import annotations

from app.agent.policy import PolicyConfig
from app.schemas.task_schema import Task
from app.tools.common import resolve_repo_relative_path
from app.tools.write_file import write_file


def _insert_empty_input_guard(content: str) -> str | None:
    # 这是当前基准任务的最小规则：在 items[0] 之前插入空输入保护。
    target_line = "    first_item = items[0]"
    if target_line not in content:
        return None
    if "if not items:" in content:
        return None

    replacement = "    if not items:\n        return []\n    first_item = items[0]"
    return content.replace(target_line, replacement, 1)


def _handle_none_items(content: str) -> str | None:
    # improved 策略额外增加 None 过滤逻辑。
    target_loop = "    for item in items[1:]:\n        normalized_items.append(item.strip().lower())"
    if target_loop not in content:
        return None
    if "if item is None:" in content:
        return None

    replacement = (
        "    for item in items[1:]:\n"
        "        if item is None:\n"
        "            continue\n"
        "        normalized_items.append(item.strip().lower())"
    )
    return content.replace(target_loop, replacement, 1)


def _handle_leading_none_item(content: str) -> str | None:
    # improved_v2 额外把首元素为 None 的情况改成统一过滤后再归一化。
    original_block = (
        "    first_item = items[0]\n"
        "    normalized_items = [first_item.strip().lower()]\n\n"
        "    for item in items[1:]:\n"
        "        normalized_items.append(item.strip().lower())"
    )
    if original_block not in content:
        return None
    if "cleaned_items = [item for item in items if item is not None]" in content:
        return None

    replacement = (
        "    cleaned_items = [item for item in items if item is not None]\n"
        "    if not cleaned_items:\n"
        "        return []\n"
        "    first_item = cleaned_items[0]\n"
        "    normalized_items = [first_item.strip().lower()]\n\n"
        "    for item in cleaned_items[1:]:\n"
        "        normalized_items.append(item.strip().lower())"
    )
    return content.replace(original_block, replacement, 1)


def _handle_anyio_parent_task_cancel_guard(content: str) -> str | None:
    # improved_v70 处理 asyncio backend 下父任务被额外取消的问题。
    target_block = (
        'def _run_inner_flow(backend_name: str, state: ParentTaskState) -> None:\n'
        '    """故意保留 asyncio backend 会把父任务一并取消的 bug。"""\n\n'
        "    _child_task_fails()\n"
        '    if backend_name == "asyncio":\n'
        '        raise ParentTaskCancelledError("parent task spuriously cancelled")\n\n'
        "    # trio / curio 对照路径：子任务失败不会让父任务清理流程被额外取消。\n"
        "    state.completed = True"
    )
    if target_block not in content:
        return None

    replacement = (
        'def _run_inner_flow(backend_name: str, state: ParentTaskState) -> None:\n'
        '    """子任务失败后，各 backend 都应允许父任务完成清理。"""\n\n'
        "    _child_task_fails()\n"
        "    if backend_name not in {\"asyncio\", \"trio\", \"curio\"}:\n"
        '        raise ValueError(f"unsupported backend: {backend_name}")\n\n'
        "    # asyncio 不应把父任务额外取消；父任务应像其它 backend 一样完成清理。\n"
        "    state.completed = True"
    )
    return content.replace(target_block, replacement, 1)


def _handle_anyio_nested_cancelled_error_leak_guard(content: str) -> str | None:
    # improved_v71 处理 asyncio / curio backend 在嵌套 task group 中泄漏取消异常的问题。
    target_block = (
        'def _run_nested_failure_flow(backend_name: str, state: RunState) -> None:\n'
        '    """故意保留 asyncio / curio backend 会泄漏取消异常的 bug。"""\n\n'
        "    _child_task_fails()\n"
        '    if backend_name in {"asyncio", "curio"}:\n'
        '        raise CancelledErrorLeak("cancelled error leaked from nested task groups")\n\n'
        "    # trio 对照路径：父流程应看到原始业务错误，而不是额外取消。\n"
        '    raise NestedTaskGroupError("nested task group surfaced the child failure")'
    )
    if target_block not in content:
        return None

    replacement = (
        'def _run_nested_failure_flow(backend_name: str, state: RunState) -> None:\n'
        '    """所有 backend 都应把原始嵌套失败语义交还给父流程。"""\n\n'
        "    _child_task_fails()\n"
        "    if backend_name not in {\"asyncio\", \"curio\", \"trio\"}:\n"
        '        raise ValueError(f"unsupported backend: {backend_name}")\n\n'
        "    # asyncio / curio 不应额外泄漏取消异常；父流程应统一看到原始业务错误。\n"
        '    raise NestedTaskGroupError("nested task group surfaced the child failure")'
    )
    return content.replace(target_block, replacement, 1)


def _handle_rich_windows_no_color_legacy_branch(content: str) -> str | None:
    # improved_v72 处理 legacy Windows + vt=False 分支忽略 no_color 的问题。
    target_block = (
        "        if self.legacy_windows and not self.features.vt:\n"
        "            # 这里故意保留 rich#2457 的缺陷：Windows 旧控制台分支忽略 no_color。\n"
        '            return f"<WIN:{style}>{text}</WIN:{style}>"\n\n'
        "        if self.no_color:\n"
        "            return text"
    )
    if target_block not in content:
        return None
    if "if self.no_color:\n            return text\n\n        if self.legacy_windows and not self.features.vt:" in content:
        return None

    replacement = (
        "        if self.no_color:\n"
        "            return text\n\n"
        "        if self.legacy_windows and not self.features.vt:\n"
        '            return f"<WIN:{style}>{text}</WIN:{style}>"'
    )
    return content.replace(target_block, replacement, 1)


def apply_rule_based_patch(
    task: Task,
    repo_path: str,
    candidate_files: list[str],
    policy_config: PolicyConfig,
) -> dict:
    # 第一版 patch 生成器优先服务最小闭环，通过 policy 决定能处理哪些缺陷模式。
    for relative_path in candidate_files:
        target_path = resolve_repo_relative_path(repo_path, relative_path)
        if not target_path.is_file():
            continue

        original_content = target_path.read_text(encoding="utf-8")
        updated_content = _insert_empty_input_guard(original_content)
        patch_reason_parts: list[str] = []
        if updated_content is not None:
            patch_reason_parts.append("加入空输入保护逻辑")
        else:
            updated_content = original_content

        if policy_config.patch_strategy == "improved":
            improved_content = _handle_none_items(updated_content)
            if improved_content is not None:
                updated_content = improved_content
                patch_reason_parts.append("加入 None 元素过滤逻辑")

        if policy_config.patch_strategy == "improved_v2":
            improved_v2_content = _handle_leading_none_item(original_content)
            if improved_v2_content is not None:
                updated_content = improved_v2_content
                patch_reason_parts = ["加入空输入与全量 None 元素过滤逻辑"]
            else:
                improved_content = _handle_none_items(updated_content)
                if improved_content is not None:
                    updated_content = improved_content
                    patch_reason_parts.append("加入 None 元素过滤逻辑")

        if policy_config.patch_strategy == "improved_v72":
            improved_v72_content = _handle_rich_windows_no_color_legacy_branch(original_content)
            if improved_v72_content is not None:
                updated_content = improved_v72_content
                patch_reason_parts = ["让 legacy Windows + vt=False 分支先遵守 no_color，再决定是否输出 Windows 样式"]
        if policy_config.patch_strategy in {"improved_v71", "improved_v72"} and updated_content == original_content:
            improved_v71_content = _handle_anyio_nested_cancelled_error_leak_guard(original_content)
            if improved_v71_content is not None:
                updated_content = improved_v71_content
                patch_reason_parts = ["让 anyio 在 asyncio 与 curio backend 下都把嵌套 task group 的原始失败语义交还给父流程，避免额外泄漏 CancelledError"]
        if policy_config.patch_strategy in {"improved_v70", "improved_v71", "improved_v72"} and updated_content == original_content:
            improved_v70_content = _handle_anyio_parent_task_cancel_guard(original_content)
            if improved_v70_content is not None:
                updated_content = improved_v70_content
                patch_reason_parts = ["让 anyio 在 asyncio backend 下也允许父任务完成清理，避免额外抛出 ParentTaskCancelledError"]

        if updated_content == original_content:
            updated_content = None
        if updated_content is None:
            continue

        write_result = write_file(repo_path, relative_path, updated_content)
        if not write_result["ok"]:
            return {
                "ok": False,
                "summary": f"已定位到候选修复文件 `{relative_path}`，但写入失败。",
                "modified_files": [],
                "patch_reason": "",
                "write_result": write_result,
            }

        return {
            "ok": True,
            "summary": f"已为 `{relative_path}` 生成规则型修复 patch：{'、'.join(patch_reason_parts)}。",
            "modified_files": [relative_path],
            "patch_reason": (
                f"当前策略 `{policy_config.policy_id}` 针对任务 `{task.task_id}` 生成修复，"
                f"在 `{relative_path}` 中执行：{'、'.join(patch_reason_parts)}。"
            ),
            "write_result": write_result,
        }

    return {
        "ok": False,
        "summary": "当前规则型 patch 生成器未找到可自动修复的位置。",
        "modified_files": [],
        "patch_reason": "",
        "write_result": None,
    }
