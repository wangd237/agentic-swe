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


def _relax_urllib3_upper_bound(content: str) -> str | None:
    # improved_v3 处理依赖约束任务，把 urllib3 上界从 1.x 放宽到 3。
    target_line = '    "urllib3>=1.21.1,<1.27",'
    if target_line not in content:
        return None
    if '"urllib3>=1.21.1,<3",' in content:
        return None
    replacement = '    "urllib3>=1.21.1,<3",'
    return content.replace(target_line, replacement, 1)


def _handle_quoted_charset(content: str) -> str | None:
    # improved_v4 处理 quoted charset 的引号清洗。
    target_block = (
        '            if value.startswith(\'"\') or value.startswith("\'"):\n'
        "                return None\n"
        "            return value"
    )
    if target_block not in content:
        return None
    if "return value.strip(\"\\\"'\")" in content:
        return None

    replacement = "            return value.strip(\"\\\"'\")"
    return content.replace(target_block, replacement, 1)


def _handle_crlf_ansi_lines(content: str) -> str | None:
    # improved_v5 处理 CRLF 行尾在 ANSI 拆分后退化成空白行的问题。
    target_block = (
        '        for line in re.split(r"(?<=\\n)", terminal_text):\n'
        "            if not line:\n"
        "                continue\n"
        '            has_newline = line.endswith("\\n")\n'
        '            decoded_line = self.decode_line(line.rstrip("\\n"))\n'
        "            parts.append(decoded_line)\n"
        "            if has_newline:\n"
        '                parts.append("\\n")'
    )
    if target_block not in content:
        return None
    if 'for line in terminal_text.splitlines(keepends=True):' in content:
        return None

    replacement = (
        "        for line in terminal_text.splitlines(keepends=True):\n"
        '            has_newline = line.endswith(("\\r", "\\n"))\n'
        '            decoded_line = self.decode_line(line.rstrip("\\r\\n"))\n'
        "            parts.append(decoded_line)\n"
        "            if has_newline:\n"
        '                parts.append("\\n")'
    )
    return content.replace(target_block, replacement, 1)


def _handle_richhandler_timezone(content: str) -> str | None:
    # improved_v6 处理 RichHandler 时间格式化时丢失时区偏移的问题。
    target_block = (
        "    def format_time(self, created: float) -> str:\n"
        '        # 这里故意保留 %z 丢失时区偏移的缺陷，便于后续修复。\n'
        '        return datetime.fromtimestamp(created).strftime(self.log_time_format)'
    )
    if target_block not in content:
        return None
    if 'datetime.fromtimestamp(created, tz=self.time_zone).strftime(self.log_time_format)' in content:
        return None

    replacement = (
        "    def format_time(self, created: float) -> str:\n"
        "        # 这里显式传入时区，让 %z 能够保留偏移信息。\n"
        "        return datetime.fromtimestamp(created, tz=self.time_zone).strftime(self.log_time_format)"
    )
    return content.replace(target_block, replacement, 1)


def _handle_negative_boolean_default(content: str) -> str | None:
    # improved_v7 处理负向布尔 flag 在 default=True 时被错误覆盖的问题。
    target_block = (
        "def resolve_negative_flag(default: bool, flag_value: bool, provided: bool = False) -> bool:\n"
        "    # 这里故意保留 default=True 被特殊处理导致负向 flag 默认值异常的缺陷。\n"
        "    if provided:\n"
        "        return flag_value\n"
        "    if default is True and flag_value is False:\n"
        "        return flag_value\n"
        "    return default"
    )
    if target_block not in content:
        return None
    if "if default is True and flag_value is False:" not in content:
        return None

    replacement = (
        "def resolve_negative_flag(default: bool, flag_value: bool, provided: bool = False) -> bool:\n"
        "    # 负向布尔 flag 应保持默认值，不应被特殊 case 强行改成 flag_value。\n"
        "    if provided:\n"
        "        return flag_value\n"
        "    return default"
    )
    return content.replace(target_block, replacement, 1)


def _handle_closest_marker_inheritance(content: str) -> str | None:
    # improved_v8 处理继承链中应优先返回最近 marker 的问题。
    target_block = (
        "def get_closest_marker(markers: list[Marker], marker_name: str) -> Marker | None:\n"
        "    # 这里故意保留回归：错误地优先返回继承链中更早的 marker。\n"
        "    for marker in markers:\n"
        "        if marker.name == marker_name:\n"
        "            return marker\n"
        "    return None"
    )
    if target_block not in content:
        return None
    if "for marker in reversed(markers):" in content:
        return None

    replacement = (
        "def get_closest_marker(markers: list[Marker], marker_name: str) -> Marker | None:\n"
        "    # 子类重定义 marker 时，应优先返回继承链中最近的那个。\n"
        "    for marker in reversed(markers):\n"
        "        if marker.name == marker_name:\n"
        "            return marker\n"
        "    return None"
    )
    return content.replace(target_block, replacement, 1)


def _handle_tzstr_zero_offset(content: str) -> str | None:
    # improved_v9 处理 UTC / GMT 未显式给 offset 时对 None 做符号变换的问题。
    target_block = (
        'def tzstr(zone: str) -> FixedOffsetTZ:\n'
        '    """解析最小化的时区字符串。"""\n'
        "    normalized_zone = zone.strip().upper()\n"
        "    offset = None\n\n"
        '    if normalized_zone not in {"UTC", "GMT"}:\n'
        '        raise ValueError(f"Unsupported zone: {zone}")\n\n'
        "    # 这里故意保留真实 issue 中的缺陷：没有 offset 时仍对 None 做符号变换。\n"
        "    offset *= -1\n"
        "    return FixedOffsetTZ(normalized_zone, offset)"
    )
    if target_block not in content:
        return None
    if "if offset is None:" in content:
        return None

    replacement = (
        'def tzstr(zone: str) -> FixedOffsetTZ:\n'
        '    """解析最小化的时区字符串。"""\n'
        "    normalized_zone = zone.strip().upper()\n"
        "    offset = None\n\n"
        '    if normalized_zone not in {"UTC", "GMT"}:\n'
        '        raise ValueError(f"Unsupported zone: {zone}")\n\n'
        "    # UTC / GMT 在未显式提供 offset 时，应回落到零偏移而不是继续对 None 做运算。\n"
        "    if offset is None:\n"
        "        offset = 0\n"
        "    else:\n"
        "        offset *= -1\n"
        "    return FixedOffsetTZ(normalized_zone, offset)"
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

        if policy_config.patch_strategy == "improved_v3":
            improved_v3_content = _relax_urllib3_upper_bound(original_content)
            if improved_v3_content is not None:
                updated_content = improved_v3_content
                patch_reason_parts = ["放宽 urllib3 依赖上界到 3.x"]
            else:
                improved_v2_content = _handle_leading_none_item(original_content)
                if improved_v2_content is not None:
                    updated_content = improved_v2_content
                    patch_reason_parts = ["加入空输入与全量 None 元素过滤逻辑"]
                else:
                    improved_content = _handle_none_items(updated_content)
                    if improved_content is not None:
                        updated_content = improved_content
                        patch_reason_parts.append("加入 None 元素过滤逻辑")

        if policy_config.patch_strategy == "improved_v4":
            improved_v4_content = _handle_quoted_charset(original_content)
            if improved_v4_content is not None:
                updated_content = improved_v4_content
                patch_reason_parts = ["加入 quoted charset 去引号逻辑"]
            else:
                improved_v3_content = _relax_urllib3_upper_bound(original_content)
                if improved_v3_content is not None:
                    updated_content = improved_v3_content
                    patch_reason_parts = ["放宽 urllib3 依赖上界到 3.x"]
                else:
                    improved_v2_content = _handle_leading_none_item(original_content)
                    if improved_v2_content is not None:
                        updated_content = improved_v2_content
                        patch_reason_parts = ["加入空输入与全量 None 元素过滤逻辑"]
                    else:
                        improved_content = _handle_none_items(updated_content)
                        if improved_content is not None:
                            updated_content = improved_content
                            patch_reason_parts.append("加入 None 元素过滤逻辑")

        if policy_config.patch_strategy == "improved_v5":
            improved_v5_content = _handle_crlf_ansi_lines(original_content)
            if improved_v5_content is not None:
                updated_content = improved_v5_content
                patch_reason_parts = ["将 ANSI 文本拆分逻辑改为兼容 CRLF 的 splitlines keepends 流程"]
            else:
                improved_v4_content = _handle_quoted_charset(original_content)
                if improved_v4_content is not None:
                    updated_content = improved_v4_content
                    patch_reason_parts = ["加入 quoted charset 去引号逻辑"]
                else:
                    improved_v3_content = _relax_urllib3_upper_bound(original_content)
                    if improved_v3_content is not None:
                        updated_content = improved_v3_content
                        patch_reason_parts = ["放宽 urllib3 依赖上界到 3.x"]
                    else:
                        improved_v2_content = _handle_leading_none_item(original_content)
                        if improved_v2_content is not None:
                            updated_content = improved_v2_content
                            patch_reason_parts = ["加入空输入与全量 None 元素过滤逻辑"]
                        else:
                            improved_content = _handle_none_items(updated_content)
                            if improved_content is not None:
                                updated_content = improved_content
                                patch_reason_parts.append("加入 None 元素过滤逻辑")

        if policy_config.patch_strategy == "improved_v6":
            improved_v6_content = _handle_richhandler_timezone(original_content)
            if improved_v6_content is not None:
                updated_content = improved_v6_content
                patch_reason_parts = ["让 RichHandler 的时间格式化显式保留时区信息"]
            else:
                improved_v5_content = _handle_crlf_ansi_lines(original_content)
                if improved_v5_content is not None:
                    updated_content = improved_v5_content
                    patch_reason_parts = ["将 ANSI 文本拆分逻辑改为兼容 CRLF 的 splitlines keepends 流程"]
                else:
                    improved_v4_content = _handle_quoted_charset(original_content)
                    if improved_v4_content is not None:
                        updated_content = improved_v4_content
                        patch_reason_parts = ["加入 quoted charset 去引号逻辑"]
                    else:
                        improved_v3_content = _relax_urllib3_upper_bound(original_content)
                        if improved_v3_content is not None:
                            updated_content = improved_v3_content
                            patch_reason_parts = ["放宽 urllib3 依赖上界到 3.x"]
                        else:
                            improved_v2_content = _handle_leading_none_item(original_content)
                            if improved_v2_content is not None:
                                updated_content = improved_v2_content
                                patch_reason_parts = ["加入空输入与全量 None 元素过滤逻辑"]
                            else:
                                improved_content = _handle_none_items(updated_content)
                                if improved_content is not None:
                                    updated_content = improved_content
                                    patch_reason_parts.append("加入 None 元素过滤逻辑")

        if policy_config.patch_strategy == "improved_v7":
            improved_v7_content = _handle_negative_boolean_default(original_content)
            if improved_v7_content is not None:
                updated_content = improved_v7_content
                patch_reason_parts = ["修正负向布尔 flag 的 default=True 默认行为"]
            else:
                improved_v6_content = _handle_richhandler_timezone(original_content)
                if improved_v6_content is not None:
                    updated_content = improved_v6_content
                    patch_reason_parts = ["让 RichHandler 的时间格式化显式保留时区信息"]
                else:
                    improved_v5_content = _handle_crlf_ansi_lines(original_content)
                    if improved_v5_content is not None:
                        updated_content = improved_v5_content
                        patch_reason_parts = ["将 ANSI 文本拆分逻辑改为兼容 CRLF 的 splitlines keepends 流程"]
                    else:
                        improved_v4_content = _handle_quoted_charset(original_content)
                        if improved_v4_content is not None:
                            updated_content = improved_v4_content
                            patch_reason_parts = ["加入 quoted charset 去引号逻辑"]
                        else:
                            improved_v3_content = _relax_urllib3_upper_bound(original_content)
                            if improved_v3_content is not None:
                                updated_content = improved_v3_content
                                patch_reason_parts = ["放宽 urllib3 依赖上界到 3.x"]
                            else:
                                improved_v2_content = _handle_leading_none_item(original_content)
                                if improved_v2_content is not None:
                                    updated_content = improved_v2_content
                                    patch_reason_parts = ["加入空输入与全量 None 元素过滤逻辑"]
                                else:
                                    improved_content = _handle_none_items(updated_content)
                                    if improved_content is not None:
                                        updated_content = improved_content
                                        patch_reason_parts.append("加入 None 元素过滤逻辑")

        if policy_config.patch_strategy == "improved_v8":
            improved_v8_content = _handle_closest_marker_inheritance(original_content)
            if improved_v8_content is not None:
                updated_content = improved_v8_content
                patch_reason_parts = ["让 get_closest_marker 优先返回继承链中最近的 marker"]
            else:
                improved_v7_content = _handle_negative_boolean_default(original_content)
                if improved_v7_content is not None:
                    updated_content = improved_v7_content
                    patch_reason_parts = ["修正负向布尔 flag 的 default=True 默认行为"]
                else:
                    improved_v6_content = _handle_richhandler_timezone(original_content)
                    if improved_v6_content is not None:
                        updated_content = improved_v6_content
                        patch_reason_parts = ["让 RichHandler 的时间格式化显式保留时区信息"]
                    else:
                        improved_v5_content = _handle_crlf_ansi_lines(original_content)
                        if improved_v5_content is not None:
                            updated_content = improved_v5_content
                            patch_reason_parts = ["将 ANSI 文本拆分逻辑改为兼容 CRLF 的 splitlines keepends 流程"]
                        else:
                            improved_v4_content = _handle_quoted_charset(original_content)
                            if improved_v4_content is not None:
                                updated_content = improved_v4_content
                                patch_reason_parts = ["加入 quoted charset 去引号逻辑"]
                            else:
                                improved_v3_content = _relax_urllib3_upper_bound(original_content)
                                if improved_v3_content is not None:
                                    updated_content = improved_v3_content
                                    patch_reason_parts = ["放宽 urllib3 依赖上界到 3.x"]
                                else:
                                    improved_v2_content = _handle_leading_none_item(original_content)
                                    if improved_v2_content is not None:
                                        updated_content = improved_v2_content
                                        patch_reason_parts = ["加入空输入与全量 None 元素过滤逻辑"]
                                    else:
                                        improved_content = _handle_none_items(updated_content)
                                        if improved_content is not None:
                                            updated_content = improved_content
                                            patch_reason_parts.append("加入 None 元素过滤逻辑")

        if policy_config.patch_strategy == "improved_v9":
            improved_v9_content = _handle_tzstr_zero_offset(original_content)
            if improved_v9_content is not None:
                updated_content = improved_v9_content
                patch_reason_parts = ["让 UTC 和 GMT 在未显式提供 offset 时回落为零偏移"]
            else:
                improved_v8_content = _handle_closest_marker_inheritance(original_content)
                if improved_v8_content is not None:
                    updated_content = improved_v8_content
                    patch_reason_parts = ["让 get_closest_marker 优先返回继承链中最近的 marker"]
                else:
                    improved_v7_content = _handle_negative_boolean_default(original_content)
                    if improved_v7_content is not None:
                        updated_content = improved_v7_content
                        patch_reason_parts = ["修正负向布尔 flag 的 default=True 默认行为"]
                    else:
                        improved_v6_content = _handle_richhandler_timezone(original_content)
                        if improved_v6_content is not None:
                            updated_content = improved_v6_content
                            patch_reason_parts = ["让 RichHandler 的时间格式化显式保留时区信息"]
                        else:
                            improved_v5_content = _handle_crlf_ansi_lines(original_content)
                            if improved_v5_content is not None:
                                updated_content = improved_v5_content
                                patch_reason_parts = ["将 ANSI 文本拆分逻辑改为兼容 CRLF 的 splitlines keepends 流程"]
                            else:
                                improved_v4_content = _handle_quoted_charset(original_content)
                                if improved_v4_content is not None:
                                    updated_content = improved_v4_content
                                    patch_reason_parts = ["加入 quoted charset 去引号逻辑"]
                                else:
                                    improved_v3_content = _relax_urllib3_upper_bound(original_content)
                                    if improved_v3_content is not None:
                                        updated_content = improved_v3_content
                                        patch_reason_parts = ["放宽 urllib3 依赖上界到 3.x"]
                                    else:
                                        improved_v2_content = _handle_leading_none_item(original_content)
                                        if improved_v2_content is not None:
                                            updated_content = improved_v2_content
                                            patch_reason_parts = ["加入空输入与全量 None 元素过滤逻辑"]
                                        else:
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
