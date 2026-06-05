"""最小 patch 生成与应用逻辑。"""

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
