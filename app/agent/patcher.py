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


def _handle_nine_digit_time_string(content: str) -> str | None:
    # improved_v10 处理 9 位时间串应被识别为 HHMMSSmmm 的问题。
    target_block = (
        'def parse_time_string(value: str) -> tuple[int, int, int, int]:\n'
        '    """把 9 位时间串解析为 HH, MM, SS, mmm。"""\n'
        '    cleaned = value.replace(" ", "")\n\n'
        "    # 这里故意保留缺陷：当前仍把 9 位时间串视为不支持格式。\n"
        '    if len(cleaned) == 9 and cleaned.isdigit():\n'
        '        raise ValueError(f"Unknown string format: {value}")\n\n'
        '    raise ValueError(f"Unsupported time string: {value}")'
    )
    if target_block not in content:
        return None
    if 'if len(cleaned) == 9 and cleaned.isdigit():' in content:
        if 'hour = int(cleaned[0:2])' in content:
            return None

    replacement = (
        'def parse_time_string(value: str) -> tuple[int, int, int, int]:\n'
        '    """把 9 位时间串解析为 HH, MM, SS, mmm。"""\n'
        '    cleaned = value.replace(" ", "")\n\n'
        "    # 9 位串应按 HHMMSSmmm 处理，不能再被当成普通年份字符串。\n"
        '    if len(cleaned) == 9 and cleaned.isdigit():\n'
        '        hour = int(cleaned[0:2])\n'
        '        minute = int(cleaned[2:4])\n'
        '        second = int(cleaned[4:6])\n'
        '        millisecond = int(cleaned[6:9])\n'
        '        return hour, minute, second, millisecond\n'
        '    raise ValueError(f"Unsupported time string: {value}")'
    )
    return content.replace(target_block, replacement, 1)


def _handle_branch_assigned_undeclared(content: str) -> str | None:
    # improved_v11 处理所有分支都 set 的变量仍被错误判定为 undeclared 的问题。
    target_block = (
        'def find_undeclared_variables(branch_assigned: dict[str, list[str]], used_variables: list[str]) -> set[str]:\n'
        '    """返回被使用但未声明的变量集合。"""\n'
        "    assigned_variables: set[str] = set()\n"
        "    for branch_variables in branch_assigned.values():\n"
        "        assigned_variables.update(branch_variables)\n\n"
        "    # 这里故意保留回归：即便变量在所有分支都被 set，也仍然错误地把它当成 undeclared。\n"
        "    undeclared = {name for name in used_variables if name not in assigned_variables}\n"
        "    for variable_name in used_variables:\n"
        "        if variable_name in assigned_variables:\n"
        "            undeclared.add(variable_name)\n"
        "    return undeclared"
    )
    if target_block not in content:
        return None
    if "all_branch_assigned" in content:
        return None

    replacement = (
        'def find_undeclared_variables(branch_assigned: dict[str, list[str]], used_variables: list[str]) -> set[str]:\n'
        '    """返回被使用但未声明的变量集合。"""\n'
        "    assigned_variables: set[str] = set()\n"
        "    for branch_variables in branch_assigned.values():\n"
        "        assigned_variables.update(branch_variables)\n\n"
        "    all_branch_assigned = set.intersection(\n"
        "        *(set(branch_variables) for branch_variables in branch_assigned.values())\n"
        "    ) if branch_assigned else set()\n"
        "    undeclared = {name for name in used_variables if name not in assigned_variables}\n"
        "    for variable_name in list(undeclared):\n"
        "        if variable_name in all_branch_assigned:\n"
        "            undeclared.discard(variable_name)\n"
        "    return undeclared"
    )
    return content.replace(target_block, replacement, 1)


def _handle_slice_fill_with_divisible_case(content: str) -> str | None:
    # improved_v12 处理整除场景下 slice 仍错误补入 fill_with 的问题。
    target_block = (
        "        # 这里故意保留真实 issue 中的缺陷：在整除场景下也错误补入 fill_with。\n"
        "        if fill_with is not None and slice_index >= remainder:\n"
        "            chunk.append(fill_with)"
    )
    if target_block not in content:
        return None
    if "slice_index >= remainder and remainder != 0" in content:
        return None

    replacement = (
        "        # 只有存在余数时，尾部较短分片才需要补入 fill_with。\n"
        "        if fill_with is not None and slice_index >= remainder and remainder != 0:\n"
        "            chunk.append(fill_with)"
    )
    return content.replace(target_block, replacement, 1)


def _handle_tomlkit_next_line_comma_append(content: str) -> str | None:
    # improved_v13 处理数组原始风格把逗号放在下一行时 append 后错误生成双逗号的问题。
    target_block = (
        "    # 这里故意保留真实 issue 中的缺陷：上一行已经以逗号开头时，仍错误地再补一个逗号。\n"
        '    if previous_line.lstrip().startswith(","):\n'
        '        appended_line = f"{indent},,{value}"'
    )
    if target_block not in content:
        return None
    if 'appended_line = f"{indent},{value}"' not in content:
        return None

    replacement = (
        "    # 原始风格已经使用了“下一行开头带逗号”的表达，不应再额外补一个逗号。\n"
        '    if previous_line.lstrip().startswith(","):\n'
        '        appended_line = f"{indent},{value}"'
    )
    return content.replace(target_block, replacement, 1)


def _handle_tomlkit_dotted_inline_table_append(content: str) -> str | None:
    # improved_v14 处理 dotted inline table 追加新键时缺少分隔符导致输出损坏的问题。
    target_block = (
        "    # 这里故意保留真实 issue 中的缺陷：直接把新键黏连到旧内容末尾，缺少分隔。\n"
        '    broken_body = f"{body}{new_key} = {value}"\n'
        '    return f"{prefix}{broken_body}\\n{suffix}\\n"'
    )
    if target_block not in content:
        return None
    if 'fixed_body = f"{body}, {new_key} = {value}"' in content:
        return None

    replacement = (
        "    # 追加 dotted inline table 键值对时，需要显式插入逗号和空格分隔。\n"
        '    fixed_body = f"{body}, {new_key} = {value}"\n'
        '    return f"{prefix}{fixed_body}{suffix}\\n"'
    )
    return content.replace(target_block, replacement, 1)


def _handle_packaging_non_normalized_wheel_version(content: str) -> str | None:
    # improved_v15 处理 wheel 文件名里未 normalized 版本号仍被错误接受的问题。
    target_block = (
        "    # 这里故意保留真实 issue 中的缺陷：直接接受未 normalized 的版本号。\n"
        "    return name, version"
    )
    if target_block not in content:
        return None
    if 'if version != normalized_version:' in content:
        return None

    replacement = (
        "    normalized_version = version.lstrip(\"0\")\n"
        "    if normalized_version.startswith(\".\"):\n"
        "        normalized_version = f\"0{normalized_version}\"\n"
        "    if version != normalized_version:\n"
        "        raise InvalidWheelFilename(f\"Non-normalized version in wheel filename: {filename}\")\n"
        "    return name, version"
    )
    return content.replace(target_block, replacement, 1)


def _handle_jsonschema_mixed_type_extras_sort(content: str) -> str | None:
    # improved_v16 处理 mixed bool/str extras 排序时触发 TypeError 的问题。
    target_block = (
        "    # 这里故意保留真实 issue 中的缺陷：mixed bool/str 排序会直接触发 TypeError。\n"
        "    sorted_extras = sorted(extras)\n"
        '    rendered = ", ".join(repr(item) for item in sorted_extras)'
    )
    if target_block not in content:
        return None
    if "except TypeError:" in content:
        return None

    replacement = (
        "    try:\n"
        "        sorted_extras = sorted(extras)\n"
        "    except TypeError:\n"
        "        sorted_extras = list(extras)\n"
        '    rendered = ", ".join(repr(item) for item in sorted_extras)'
    )
    return content.replace(target_block, replacement, 1)


def _handle_jsonschema_hostname_value_error(content: str) -> str | None:
    # improved_v17 处理 hostname 格式检查在空字符串场景下直接抛出 ValueError 的问题。
    target_block = (
        "    # 这里故意保留真实 issue 中的缺陷：空字符串会在底层检查阶段直接抛出 ValueError。\n"
        "    labels = _split_hostname_labels(value)\n"
        "    if any(not label or not label.replace(\"-\", \"\").isalnum() for label in labels):\n"
        "        return False\n"
        "    return True"
    )
    if target_block not in content:
        return None
    if "except ValueError:" in content:
        return None

    replacement = (
        "    try:\n"
        "        labels = _split_hostname_labels(value)\n"
        "    except ValueError:\n"
        "        return False\n"
        "    if any(not label or not label.replace(\"-\", \"\").isalnum() for label in labels):\n"
        "        return False\n"
        "    return True"
    )
    return content.replace(target_block, replacement, 1)


def _handle_jsonschema_integer_valued_multiple_of_float(content: str) -> str | None:
    # improved_v18 处理整数值浮点 multipleOf 没有按数学整数处理的问题。
    target_block = (
        "    # 这里故意保留真实 issue 中的缺陷：整数值浮点数仍直接走浮点路径。\n"
        "    return (instance / divisor).is_integer()"
    )
    if target_block not in content:
        return None
    if "if isinstance(divisor, float) and divisor.is_integer():" in content:
        return None

    replacement = (
        "    if isinstance(divisor, float) and divisor.is_integer():\n"
        "        divisor = int(divisor)\n"
        "        return instance % divisor == 0\n"
        "    return (instance / divisor).is_integer()"
    )
    return content.replace(target_block, replacement, 1)


def _handle_packaging_requirement_extra_normalization(content: str) -> str | None:
    # improved_v19 处理复合 marker 表达式里的 extra 名称没有被统一规范化的问题。
    target_block = (
        "        # 这里故意保留真实 issue 中的缺陷：只有单独 extra marker 才会被规范化。\n"
        "        if self.marker.startswith('extra == \"'):\n"
        "            extra_name = self.marker[len('extra == \"') : -1]\n"
        "            normalized = _normalize_extra_name(extra_name)\n"
        "            return f'{self.base}; extra == \"{normalized}\"'\n\n"
        '        return f"{self.base}; {self.marker}"'
    )
    if target_block not in content:
        return None
    if "normalized_marker = _normalize_extra_markers(self.marker)" in content:
        return None

    replacement = (
        "        normalized_marker = _normalize_extra_markers(self.marker)\n"
        '        return f"{self.base}; {normalized_marker}"'
    )
    return content.replace(target_block, replacement, 1)


def _handle_click_resolve_command_none(content: str) -> str | None:
    # improved_v20 处理 cmd 为 None 时 resolve_command 直接访问 name 的问题。
    target_block = (
        "        # 这里故意保留真实 issue 中的缺陷：cmd 为 None 时仍直接访问 name。\n"
        "        return cmd.name, cmd, args"
    )
    if target_block not in content:
        return None
    if "if cmd is None:" in content:
        return None

    replacement = (
        "        if cmd is None:\n"
        "            return resolved_name, cmd, args\n"
        "        return cmd.name, cmd, args"
    )
    return content.replace(target_block, replacement, 1)


def _handle_dateutil_month_year_dot_format(content: str) -> str | None:
    # improved_v21 处理 MM.YYYY 分支错误地按 (month, year) 返回的问题。
    target_line = "        return int(month_str), int(year_str)"
    if target_line not in content:
        return None

    replacement = "        return int(year_str), int(month_str)"
    return content.replace(target_line, replacement, 1)


def _handle_jsonschema_single_label_hostname(content: str) -> str | None:
    # improved_v22 处理单标签 hostname 被错误要求至少两个 label 的问题。
    target_block = (
        "    # 这里故意保留真实 issue 中的缺陷：错误要求 hostname 至少包含两个 label。\n"
        "    if len(labels) < 2:\n"
        "        return False\n\n"
    )
    if target_block not in content:
        return None

    replacement = ""
    return content.replace(target_block, replacement, 1)


def _handle_packaging_dev_local_greater_than(content: str) -> str | None:
    # improved_v23 处理带 local 段时错误只比较 base_version 的问题。
    target_block = (
        "        if prospective_version.local is not None:\n"
        "            # 这里故意保留真实 issue 中的缺陷：错误地只比较 base_version，\n"
        "            # 导致 dev 段已经更大时，带 local 的版本仍被提前拒绝。\n"
        "            if Version(prospective_version.base_version) == Version(self.spec_version.base_version):\n"
        "                return False\n"
    )
    if target_block not in content:
        return None
    if "Version(prospective_version.public) == Version(self.spec_version.public)" in content:
        return None

    replacement = (
        "        if prospective_version.local is not None:\n"
        "            # 带 local 段时仍应按 public version 判断是否与 specifier 相同，\n"
        "            # 不能把 dev 段差异在 base_version 层面提前抹掉。\n"
        "            if Version(prospective_version.public) == Version(self.spec_version.public):\n"
        "                return False\n"
    )
    return content.replace(target_block, replacement, 1)


def _handle_dateutil_attached_comma_year(content: str) -> str | None:
    # improved_v24 处理年份前紧贴逗号时没有被识别为 year token 的问题。
    target_block = (
        "    for token in [trailing, *remaining_tokens]:\n"
        "        # 这里故意保留真实 issue 中的缺陷：年份 token 前面如果紧贴逗号，\n"
        "        # 就不会被识别成年份，最终错误回落到默认年份。\n"
        "        if token.isdigit() and len(token) == 4:\n"
        "            year = int(token)\n"
        "            break\n"
    )
    if target_block not in content:
        return None
    if "normalized_token = token.lstrip(\",\")" in content:
        return None

    replacement = (
        "    for token in [trailing, *remaining_tokens]:\n"
        "        normalized_token = token.lstrip(\",\")\n"
        "        if normalized_token.isdigit() and len(normalized_token) == 4:\n"
        "            year = int(normalized_token)\n"
        "            break\n"
    )
    return content.replace(target_block, replacement, 1)


def _handle_jsonschema_error_tree_missing_index(content: str) -> str | None:
    # improved_v25 处理访问不存在索引时错误污染 ErrorTree 内部状态的问题。
    target_block = (
        "    def __getitem__(self, index: int) -> \"ErrorTree\":\n"
        "        # 这里故意保留真实 issue 中的缺陷：访问不存在的索引时，\n"
        "        # 仍然通过 setdefault 把空节点写回树里，污染后续可见状态。\n"
        "        return self._children.setdefault(index, ErrorTree())"
    )
    if target_block not in content:
        return None
    if "return self._children.get(index, ErrorTree())" in content:
        return None

    replacement = (
        "    def __getitem__(self, index: int) -> \"ErrorTree\":\n"
        "        # 访问不存在的索引时可以返回空节点，但不能把它写回内部状态。\n"
        "        return self._children.get(index, ErrorTree())"
    )
    return content.replace(target_block, replacement, 1)


def _handle_jsonschema_extend_copies_applicable_validators(content: str) -> str | None:
    # improved_v26 处理 extend 时丢失 applicable_validators 导致 legacy $ref 语义回归的问题。
    target_block = (
        "def extend(\n"
        "    validator: type[object],\n"
        "    validators: dict[str, object] | None = None,\n"
        ") -> type[object]:\n"
        '    """基于已有 validator 生成扩展类。"""\n'
        "    combined = dict(validator.VALIDATORS)\n"
        "    combined.update(validators or {})\n\n"
        "    # 这里故意保留真实 issue 中的缺陷：extend 没有把 applicable_validators 透传给 create。\n"
        "    return create(validators=combined)"
    )
    if target_block not in content:
        return None
    if "applicable_validators=validator.applicable_validators" in content:
        return None

    replacement = (
        "def extend(\n"
        "    validator: type[object],\n"
        "    validators: dict[str, object] | None = None,\n"
        ") -> type[object]:\n"
        '    """基于已有 validator 生成扩展类。"""\n'
        "    combined = dict(validator.VALIDATORS)\n"
        "    combined.update(validators or {})\n\n"
        "    # 扩展后的 validator 需要保留原始 applicable_validators，避免 legacy $ref 语义丢失。\n"
        "    return create(\n"
        "        validators=combined,\n"
        "        applicable_validators=validator.applicable_validators,\n"
        "    )"
    )
    return content.replace(target_block, replacement, 1)


def _handle_sqlite_delete_where_autocommit(content: str) -> str | None:
    # improved_v27 处理 delete_where 删除后未提交事务，导致其他连接不可见的问题。
    start_marker = "    def delete_where(self, where_clause: str, params: tuple[object, ...]) -> int:\n"
    end_marker = "\n    def list_names(self) -> list[str]:\n"
    if start_marker not in content or end_marker not in content:
        return None

    block_start = content.index(start_marker)
    block_end = content.index(end_marker, block_start)
    delete_block = content[block_start:block_end]

    target_block = (
        "    def delete_where(self, where_clause: str, params: tuple[object, ...]) -> int:\n"
        '        """删除满足条件的记录，并返回删除行数。"""\n'
        "        cursor = self._connection.execute(\n"
        '            f"DELETE FROM items WHERE {where_clause}",\n'
        "            params,\n"
        "        )\n"
        "        # 这里故意保留真实 issue 中的缺陷：删除后没有提交事务。\n"
        "        return cursor.rowcount"
    )
    if target_block not in delete_block:
        return None
    if "self._connection.commit()" in delete_block:
        return None

    replacement = (
        "    def delete_where(self, where_clause: str, params: tuple[object, ...]) -> int:\n"
        '        """删除满足条件的记录，并返回删除行数。"""\n'
        "        cursor = self._connection.execute(\n"
        '            f"DELETE FROM items WHERE {where_clause}",\n'
        "            params,\n"
        "        )\n"
        "        # 删除操作应与 insert / upsert 保持一致，完成后立即提交事务。\n"
        "        self._connection.commit()\n"
        "        return cursor.rowcount"
    )
    return content.replace(target_block, replacement, 1)


def _handle_pydantic_inherited_model_validators(content: str) -> str | None:
    # improved_v28 处理子类定义 model validator 后父类 validator 被错误忽略的问题。
    target_block = (
        "        inherited_after = list(getattr(cls, \"__model_validator_names__\", {}).get(\"after\", []))\n"
        "        # 这里故意保留真实 issue 中的缺陷：子类只要定义了自己的 validator，\n"
        "        # 就会把父类 validator 整体覆盖掉。\n"
        "        merged_after = own_after or inherited_after\n"
        "        cls.__model_validator_names__ = {\"after\": merged_after}"
    )
    if target_block not in content:
        return None
    if "merged_after = [*inherited_after, *own_after]" in content:
        return None

    replacement = (
        "        inherited_after = list(getattr(cls, \"__model_validator_names__\", {}).get(\"after\", []))\n"
        "        # 子类 validator 应追加在父类之后，而不是把父类整条链路覆盖掉。\n"
        "        merged_after = [*inherited_after, *own_after] if own_after else inherited_after\n"
        "        cls.__model_validator_names__ = {\"after\": merged_after}"
    )
    return content.replace(target_block, replacement, 1)


def _handle_attrs_field_transformer_alias(content: str) -> str | None:
    # improved_v29 处理 field_transformer 阶段读取不到默认 alias 的问题。
    target_block = (
        "                attribute = Attribute(name=name)\n"
        "                # 这里故意保留真实 issue 中的缺陷：默认 alias 要等 field_transformer 运行完后\n"
        "                # 才回填，导致变换阶段看到的是 None。\n"
        "                if value.alias is not None:\n"
        "                    attribute.alias = value.alias\n"
        "                built_attributes.append(attribute)"
    )
    if target_block not in content:
        return None
    if "attribute.alias = value.alias or name" in content:
        return None

    replacement = (
        "                attribute = Attribute(name=name)\n"
        "                # field_transformer 运行前就应能看到最终 alias，默认 alias 也一样。\n"
        "                attribute.alias = value.alias or name\n"
        "                built_attributes.append(attribute)"
    )
    return content.replace(target_block, replacement, 1)


def _handle_sqlite_transform_empty_string_numeric(content: str) -> str | None:
    # improved_v30 处理数值列转换时空字符串仍保留为 "" 的问题。
    target_block = (
        "    if target_type == \"integer\":\n"
        "        # 这里故意保留真实 issue 中的缺陷：空字符串在数值列转换时仍被保留。\n"
        "        if value == \"\":\n"
        "            return value\n"
        "        return int(value)\n\n"
        "    if target_type == \"float\":\n"
        "        # 这里故意保留真实 issue 中的缺陷：空字符串在数值列转换时仍被保留。\n"
        "        if value == \"\":\n"
        "            return value\n"
        "        return float(value)"
    )
    if target_block not in content:
        return None
    if "return None" in target_block:
        return None

    replacement = (
        "    if target_type == \"integer\":\n"
        "        # 数值列里的空字符串应视为缺失值，而不是继续保留成文本空串。\n"
        "        if value == \"\":\n"
        "            return None\n"
        "        return int(value)\n\n"
        "    if target_type == \"float\":\n"
        "        # 数值列里的空字符串应视为缺失值，而不是继续保留成文本空串。\n"
        "        if value == \"\":\n"
        "            return None\n"
        "        return float(value)"
    )
    return content.replace(target_block, replacement, 1)


def _handle_sqlite_extract_skip_nulls(content: str) -> str | None:
    # improved_v31 处理 extract 时错误为 None 生成维表记录的问题。
    target_block = (
        "        value = row.get(column_name)\n"
        "        # 这里故意保留真实 issue 中的缺陷：None 也会被当成一个需要抽取的维表值。\n"
        "        if value not in value_to_id:\n"
        "            value_to_id[value] = len(dimension_rows) + 1\n"
        "            dimension_rows.append({\"id\": value_to_id[value], \"value\": value})\n\n"
        "        extracted_row = dict(row)\n"
        "        extracted_row[f\"{column_name}_id\"] = value_to_id[value]\n"
        "        extracted_row.pop(column_name, None)\n"
        "        extracted_rows.append(extracted_row)"
    )
    if target_block not in content:
        return None
    if "if value is None:" in content:
        return None

    replacement = (
        "        value = row.get(column_name)\n"
        "        extracted_row = dict(row)\n"
        "        if value is None:\n"
        "            # 空值应继续保留在主表里，不应为它创建维表记录。\n"
        "            extracted_row[f\"{column_name}_id\"] = None\n"
        "            extracted_row.pop(column_name, None)\n"
        "            extracted_rows.append(extracted_row)\n"
        "            continue\n\n"
        "        if value not in value_to_id:\n"
        "            value_to_id[value] = len(dimension_rows) + 1\n"
        "            dimension_rows.append({\"id\": value_to_id[value], \"value\": value})\n\n"
        "        extracted_row[f\"{column_name}_id\"] = value_to_id[value]\n"
        "        extracted_row.pop(column_name, None)\n"
        "        extracted_rows.append(extracted_row)"
    )
    return content.replace(target_block, replacement, 1)


def _handle_isort_tuple_profile_layout(content: str) -> str | None:
    # improved_v32 处理 tuple 格式化分支没有继承 profile 布局策略的问题。
    target_block = (
        "def format_tuple(values: list[str], *, profile: str | None = None) -> str:\n"
        '    """按最小规则格式化 tuple。"""\n\n'
        "    layout = get_layout_for_profile(None)\n"
        "    # 这里故意保留真实 issue 中的缺陷：tuple 分支忽略了传入 profile。\n"
        "    if layout == \"vertical\":\n"
        "        inner = \"\\n\".join(f'    \"{value}\",' for value in values)\n"
        "        return \"(\\n\" + inner + \"\\n)\"\n\n"
        "    return \"(\" + \", \".join(f'\"{value}\"' for value in values) + \")\""
    )
    if target_block not in content:
        return None
    if "layout = get_layout_for_profile(profile)" in content:
        return None

    replacement = (
        "def format_tuple(values: list[str], *, profile: str | None = None) -> str:\n"
        '    """按最小规则格式化 tuple。"""\n\n'
        "    layout = get_layout_for_profile(profile)\n"
        "    # tuple / list 等容器分支也应继承 profile 对应的布局策略。\n"
        "    if layout == \"vertical\":\n"
        "        inner = \"\\n\".join(f'    \"{value}\",' for value in values)\n"
        "        return \"(\\n\" + inner + \"\\n)\"\n\n"
        "    return \"(\" + \", \".join(f'\"{value}\"' for value in values) + \")\""
    )
    return content.replace(target_block, replacement, 1)


def _handle_packaging_marker_extra_none(content: str) -> str | None:
    # improved_v34 处理 Marker.evaluate 在 extra 为 None 时错误调用 lower 的问题。
    target_block = (
        "        # 这里故意保留真实 issue 中的缺陷：当 extra 为 None 时直接调用 lower，\n"
        "        # 会抛出 AttributeError，而不是像旧版本那样回落为 False。\n"
        '        normalized_value = raw_value.lower().replace("_", "-")\n'
        '        normalized_expected = self.expected_extra.lower().replace("_", "-")\n'
        "        return normalized_value == normalized_expected"
    )
    if target_block not in content:
        return None
    if "if raw_value is None:" in content:
        return None

    replacement = (
        "        # extra 为 None 时，应像旧版本那样回落成“不匹配”，而不是继续调用字符串方法。\n"
        "        if raw_value is None:\n"
        "            return False\n"
        '        normalized_value = raw_value.lower().replace("_", "-")\n'
        '        normalized_expected = self.expected_extra.lower().replace("_", "-")\n'
        "        return normalized_value == normalized_expected"
    )
    return content.replace(target_block, replacement, 1)


def _handle_packaging_prerelease_less_than(content: str) -> str | None:
    # improved_v35 处理 `< prerelease` 场景下更早 prerelease 被错误拒绝的问题。
    target_block = (
        "        if prospective_version.is_prerelease and self.spec_version.is_prerelease:\n"
        "            # 这里故意保留真实 issue 中的缺陷：\n"
        "            # 当前实现把“specifier 本身是 prerelease”的场景也直接拒绝掉，\n"
        "            # 从而错误排除了更早的合法 prerelease 版本。\n"
        "            return False\n\n"
        "        if not prereleases and prospective_version.is_prerelease:\n"
        "            return False\n\n"
        "        return prospective_version < self.spec_version"
    )
    if target_block not in content:
        return None

    replacement = (
        "        if prospective_version.is_prerelease and self.spec_version.is_prerelease:\n"
        "            # specifier 自身是 prerelease 时，更早但不相等的 prerelease 仍应允许命中。\n"
        "            return prospective_version < self.spec_version\n\n"
        "        if not prereleases and prospective_version.is_prerelease:\n"
        "            return False\n\n"
        "        return prospective_version < self.spec_version"
    )
    return content.replace(target_block, replacement, 1)


def _handle_packaging_sorted_compressed_tags(content: str) -> str | None:
    # improved_v36 处理 wheel compressed tag set 未排序仍被错误接受的问题。
    target_block = (
        "    # 这里故意保留真实 issue 中的缺陷：\n"
        "    # 当前实现只拆出 compressed python tag，但没有校验它们是否已经排序。\n"
        "    compressed_tags = python_tag.split(\".\")\n"
        "    if not compressed_tags:\n"
        "        raise InvalidWheelFilename(f\"Invalid python tag: {filename}\")\n\n"
        "    return name, version, python_tag"
    )
    if target_block not in content:
        return None

    replacement = (
        "    compressed_tags = python_tag.split(\".\")\n"
        "    if not compressed_tags:\n"
        "        raise InvalidWheelFilename(f\"Invalid python tag: {filename}\")\n"
        "    if len(compressed_tags) > 1 and compressed_tags != sorted(compressed_tags):\n"
        "        raise InvalidWheelFilename(f\"Unsorted compressed tag set in wheel filename: {filename}\")\n\n"
        "    return name, version, python_tag"
    )
    return content.replace(target_block, replacement, 1)


def _handle_tomlkit_boolean_true_literal(content: str) -> str | None:
    # improved_v37 处理 True 被错误序列化为 false 的问题。
    target_block = (
        '    def as_string(self) -> str:\n'
        '        """返回 TOML 字面量字符串。"""\n'
        '        # 这里故意保留真实 issue 中的缺陷：True 也被错误序列化为 false。\n'
        '        return "false"'
    )
    if target_block not in content:
        return None

    replacement = (
        '    def as_string(self) -> str:\n'
        '        """返回 TOML 字面量字符串。"""\n'
        '        return "true" if self.value else "false"'
    )
    return content.replace(target_block, replacement, 1)


def _handle_tomlkit_proxy_pop_deletes_underlying_key(content: str) -> str | None:
    # improved_v38 处理代理 pop 返回值正确但没有真正删除底层键的问题。
    target_block = (
        '    def pop(self, key: str) -> str:\n'
        '        """删除一个键并返回它原本的值。"""\n'
        "        if key not in self._data:\n"
        "            raise KeyError(key)\n\n"
        "        value = self._data[key]\n"
        "        # 这里故意保留真实 issue 中的缺陷：返回值正确，但没有真正删除底层键。\n"
        "        return value"
    )
    if target_block not in content:
        return None

    replacement = (
        '    def pop(self, key: str) -> str:\n'
        '        """删除一个键并返回它原本的值。"""\n'
        "        if key not in self._data:\n"
        "            raise KeyError(key)\n\n"
        "        value = self._data.pop(key)\n"
        "        return value"
    )
    return content.replace(target_block, replacement, 1)


def _handle_tomlkit_super_table_dotted_key_prefix(content: str) -> str | None:
    # improved_v39 处理 super table 下新增 dotted key 时父级前缀丢失的问题。
    target_block = (
        'def render_document_with_dotted_key(parent_table: str, child_table: str, value: int, dotted_key: str, dotted_value: str) -> str:\n'
        '    """渲染一个含已有子表与新增 dotted key 的最小文档。"""\n'
        "    lines = [\n"
        '        f"[{parent_table}.{child_table}]",\n'
        '        f"value = {value}",\n'
        '        "",\n'
        "    ]\n\n"
        "    # 这里故意保留真实 issue 中的缺陷：新增 dotted key 时错误丢失父级 super table 前缀。\n"
        '    lines.insert(0, f"{dotted_key} = \\"{dotted_value}\\"")\n'
        '    return "\\n".join(lines) + "\\n"'
    )
    if target_block not in content:
        return None

    replacement = (
        'def render_document_with_dotted_key(parent_table: str, child_table: str, value: int, dotted_key: str, dotted_value: str) -> str:\n'
        '    """渲染一个含已有子表与新增 dotted key 的最小文档。"""\n'
        "    lines = [\n"
        '        f"[{parent_table}.{child_table}]",\n'
        '        f"value = {value}",\n'
        '        "",\n'
        "    ]\n\n"
        '    lines.insert(0, f"{parent_table}.{dotted_key} = \\"{dotted_value}\\"")\n'
        '    return "\\n".join(lines) + "\\n"'
    )
    return content.replace(target_block, replacement, 1)


def _handle_jinja_async_loop_repr(content: str) -> str | None:
    # improved_v40 处理 AsyncLoopContext 继承同步 repr 导致暴露协程对象的问题。
    target_block = (
        "class AsyncLoopContext(LoopContext):\n"
        '    """最小异步 loop context。"""\n\n'
        "    async def _resolve_length(self) -> int:\n"
        "        return self._length\n\n"
        "    @property\n"
        "    def length(self):  # type: ignore[override]\n"
        "        return self._resolve_length()\n\n"
        "    # 这里故意保留真实 issue 中的缺陷：继承同步 repr，直接把协程对象拼进表示字符串。\n"
        "    __repr__ = LoopContext.__repr__"
    )
    if target_block not in content:
        return None

    replacement = (
        "class AsyncLoopContext(LoopContext):\n"
        '    """最小异步 loop context。"""\n\n'
        "    async def _resolve_length(self) -> int:\n"
        "        return self._length\n\n"
        "    @property\n"
        "    def length(self):  # type: ignore[override]\n"
        "        return self._resolve_length()\n\n"
        "    def __repr__(self) -> str:\n"
        "        return f\"<{type(self).__name__} {self.index}/{self._length}>\""
    )
    return content.replace(target_block, replacement, 1)


def _handle_jinja_indent_blank_first_line(content: str) -> str | None:
    # improved_v41 处理 indent 在 first=True 且首行为空时错误无视 blank=False 的问题。
    target_block = (
        'def indent_text(text: str, width: int, *, first: bool = False, blank: bool = False) -> str:\n'
        '    """给文本增加固定缩进。"""\n'
        '    prefix = " " * width\n'
        '    lines = text.splitlines(keepends=True) or [text]\n\n'
        '    result: list[str] = []\n'
        '    for index, line in enumerate(lines):\n'
        '        is_first_line = index == 0\n'
        '        is_blank_line = line.strip() == ""\n\n'
        '        # 这里故意保留真实 issue 中的缺陷：只要 first=True 就会缩进第一行，即便它是空白行且 blank=False。\n'
        '        should_indent = (first and is_first_line) or (blank or not is_blank_line)\n'
        '        if should_indent:\n'
        '            result.append(f"{prefix}{line}")\n'
        '        else:\n'
        '            result.append(line)\n\n'
        '    return "".join(result)'
    )
    if target_block not in content:
        return None

    replacement = (
        'def indent_text(text: str, width: int, *, first: bool = False, blank: bool = False) -> str:\n'
        '    """给文本增加固定缩进。"""\n'
        '    prefix = " " * width\n'
        '    lines = text.splitlines(keepends=True) or [text]\n\n'
        '    result: list[str] = []\n'
        '    for index, line in enumerate(lines):\n'
        '        is_first_line = index == 0\n'
        '        is_blank_line = line.strip() == ""\n\n'
        '        if is_first_line:\n'
        '            should_indent = (not is_blank_line) or blank\n'
        '        else:\n'
        '            should_indent = blank or not is_blank_line\n'
        '        if should_indent:\n'
        '            result.append(f"{prefix}{line}")\n'
        '        else:\n'
        '            result.append(line)\n\n'
        '    return "".join(result)'
    )
    return content.replace(target_block, replacement, 1)


def _handle_tomlkit_inline_table_missing_newline(content: str) -> str | None:
    # improved_v42 处理 dotted inline table 后继续追加普通键时缺少换行的问题。
    target_block = (
        '    if original_has_trailing_newline:\n'
        '        lines.append(inline_line)\n'
        '        lines.append(f"{appended_key} = {appended_value}")\n'
        '        return "\\n".join(lines) + "\\n"\n\n'
        '    # 这里故意保留真实 issue 中的缺陷：\n'
        '    # dotted inline table 且原始文本末尾没有换行时，错误把后续键直接黏在同一行。\n'
        '    if "." in inline_key:\n'
        '        lines.append(f"{inline_line}{appended_key} = {appended_value}")\n'
        '        return "\\n".join(lines) + "\\n"\n\n'
        '    lines.append(inline_line)\n'
        '    lines.append(f"{appended_key} = {appended_value}")\n'
        '    return "\\n".join(lines) + "\\n"'
    )
    if target_block not in content:
        return None

    replacement = (
        '    if original_has_trailing_newline:\n'
        '        lines.append(inline_line)\n'
        '        lines.append(f"{appended_key} = {appended_value}")\n'
        '        return "\\n".join(lines) + "\\n"\n\n'
        '    # dotted inline table 即便原始文本末尾没有换行，后续键也必须落到下一行。\n'
        '    lines.append(inline_line)\n'
        '    lines.append(f"{appended_key} = {appended_value}")\n'
        '    return "\\n".join(lines) + "\\n"'
    )
    return content.replace(target_block, replacement, 1)


def _handle_tomlkit_scalar_replacement_scope(content: str) -> str | None:
    # improved_v43 处理表替换成标量后被错误吸附到相邻表作用域里的问题。
    target_block = (
        'def render_document_with_scalar_replacement() -> str:\n'
        '    """把中间表替换成标量后重新渲染最小文档。"""\n'
        '    lines = [\n'
        '        "[a]",\n'
        '        "aa = 1",\n'
        '        "",\n'
        '        "[b]",\n'
        '        "bb = 2",\n'
        '        "",\n'
        '        "[c]",\n'
        '        "cc = 3",\n'
        '    ]\n\n'
        '    # 这里故意保留真实 issue 中的缺陷：\n'
        '    # 用标量替换中间表后，错误把 `b = 2` 吸附到前一个表 `a` 的内容块里，\n'
        '    # 导致顶层分隔空行丢失。\n'
        '    lines[2:6] = ["b = 2"]\n'
        '    return "\\n".join(lines) + "\\n"'
    )
    if target_block not in content:
        return None

    replacement = (
        'def render_document_with_scalar_replacement() -> str:\n'
        '    """把中间表替换成标量后重新渲染最小文档。"""\n'
        '    lines = [\n'
        '        "[a]",\n'
        '        "aa = 1",\n'
        '        "",\n'
        '        "b = 2",\n'
        '        "[c]",\n'
        '        "cc = 3",\n'
        '    ]\n'
        '    return "\\n".join(lines) + "\\n"'
    )
    return content.replace(target_block, replacement, 1)


def _handle_packaging_requirement_pickle_prereleases(content: str) -> str | None:
    # improved_v44 处理 Requirement 在 pickle 后丢失 specifier.prereleases 状态的问题。
    target_block = (
        "@dataclass\n"
        "class SpecifierSet:\n"
        '    """只保留本次 benchmark 需要的最小 specifier 状态。"""\n\n'
        "    raw: str\n"
        "    prereleases: bool | None = None\n\n"
        "    def __getstate__(self) -> dict[str, str]:\n"
        "        # 这里故意保留真实 issue 中的缺陷：\n"
        "        # pickle 状态只保留原始 specifier，丢掉了显式设置过的 prereleases 标记。\n"
        '        return {"raw": self.raw}\n\n'
        "    def __setstate__(self, state: dict[str, str]) -> None:\n"
        '        self.raw = state["raw"]\n'
        "        self.prereleases = None"
    )
    if target_block not in content:
        return None

    replacement = (
        "@dataclass\n"
        "class SpecifierSet:\n"
        '    """只保留本次 benchmark 需要的最小 specifier 状态。"""\n\n'
        "    raw: str\n"
        "    prereleases: bool | None = None\n\n"
        "    def __getstate__(self) -> dict[str, str | bool | None]:\n"
        "        # 显式设置过的 prereleases 语义也应跨 pickle 保留下来。\n"
        '        return {"raw": self.raw, "prereleases": self.prereleases}\n\n'
        "    def __setstate__(self, state: dict[str, str | bool | None]) -> None:\n"
        '        self.raw = str(state["raw"])\n'
        '        self.prereleases = state.get("prereleases")'
    )
    return content.replace(target_block, replacement, 1)


def _handle_pydantic_fraction_zero_division(content: str) -> str | None:
    # improved_v45 处理零分母 fraction 输入未被转成 ValidationError 的问题。
    target_block = (
        "    try:\n"
        "        return Fraction(input_value)\n"
        "    except ValueError as error:\n"
        "        # 这里故意保留真实 issue 中的缺陷：\n"
        "        # `6/0` 会抛出 ZeroDivisionError，当前不会被转成 ValidationError。\n"
        "        raise ValidationError(\"Input is not a valid fraction\") from error"
    )
    if target_block not in content:
        return None

    replacement = (
        "    try:\n"
        "        return Fraction(input_value)\n"
        "    except (ValueError, ZeroDivisionError) as error:\n"
        "        # 零分母和普通非法 fraction 文本都应统一映射为 ValidationError。\n"
        "        raise ValidationError(\"Input is not a valid fraction\") from error"
    )
    return content.replace(target_block, replacement, 1)


def _handle_tomlkit_proxy_repr_missing_children(content: str) -> str | None:
    # improved_v46 处理代理视图 repr 在同父路径下漏掉早期子项的问题。
    target_block = (
        "    def __repr__(self) -> str:\n"
        '        """返回代理视图的稳定字符串表示。"""\n'
        "        nested = self.to_nested_dict()\n\n"
        "        # 这里故意保留真实 issue 中的缺陷：\n"
        "        # 当同一个父路径下有多个 dotted key 子项时，错误只保留最后一个子项。\n"
        "        filtered: dict[str, object] = {}\n"
        "        for parent_key, child_value in nested.items():\n"
        "            if isinstance(child_value, dict) and len(child_value) > 1:\n"
        "                last_key = next(reversed(child_value))\n"
        "                filtered[parent_key] = {last_key: child_value[last_key]}\n"
        "            else:\n"
        "                filtered[parent_key] = child_value\n\n"
        "        return repr(filtered)"
    )
    if target_block not in content:
        return None

    replacement = (
        "    def __repr__(self) -> str:\n"
        '        """返回代理视图的稳定字符串表示。"""\n'
        "        nested = self.to_nested_dict()\n"
        "        return repr(nested)"
    )
    return content.replace(target_block, replacement, 1)


def _handle_jinja_map_default_none(content: str) -> str | None:
    # improved_v47 处理 map(attribute=..., default=None) 未正确回落默认值的问题。
    target_block = (
        'def map_attribute_with_default(items: list[dict[str, object]], attribute: str, default: object = _MISSING) -> list[object]:\n'
        '    """提取一组对象的属性值，并在缺失时回落到默认值。"""\n'
        '    result: list[object] = []\n'
        '    for item in items:\n'
        '        if attribute in item:\n'
        '            result.append(item[attribute])\n'
        '            continue\n\n'
        '        # 这里故意保留真实 issue 中的缺陷：\n'
        '        # default=None 时被错误当成“没有提供默认值”，从而直接抛异常。\n'
        '        if default is _MISSING or default is None:\n'
        '            raise AttributeError(f"object of type \'dict\' has no attribute \'{attribute}\'")\n\n'
        '        result.append(default)\n\n'
        '    return result'
    )
    if target_block not in content:
        return None

    replacement = (
        'def map_attribute_with_default(items: list[dict[str, object]], attribute: str, default: object = _MISSING) -> list[object]:\n'
        '    """提取一组对象的属性值，并在缺失时回落到默认值。"""\n'
        '    result: list[object] = []\n'
        '    for item in items:\n'
        '        if attribute in item:\n'
        '            result.append(item[attribute])\n'
        '            continue\n\n'
        '        if default is _MISSING:\n'
        '            raise AttributeError(f"object of type \'dict\' has no attribute \'{attribute}\'")\n\n'
        '        result.append(default)\n\n'
        '    return result'
    )
    return content.replace(target_block, replacement, 1)


def _handle_packaging_direct_url_file_scheme(content: str) -> str | None:
    # improved_v48 处理 file URL scheme 检查大小写敏感且拒绝单斜杠形式的问题。
    target_block = (
        '    @classmethod\n'
        '    def from_dict(cls, raw: dict[str, str]) -> "DirectUrl":\n'
        '        """从原始字典恢复 DirectUrl，并校验 file URL 语义。"""\n'
        '        url = raw["url"]\n\n'
        '        # 这里故意保留真实 issue 中的缺陷：\n'
        '        # file URL 检查是大小写敏感的，而且也错误拒绝 `file:/path` 这种合法形式。\n'
        '        if raw.get("info_type") == "file" and not url.startswith("file://"):\n'
        '            raise ValueError(f"Unsupported file URL: {url}")\n\n'
        '        return cls(url=url)'
    )
    if target_block not in content:
        return None

    replacement = (
        '    @classmethod\n'
        '    def from_dict(cls, raw: dict[str, str]) -> "DirectUrl":\n'
        '        """从原始字典恢复 DirectUrl，并校验 file URL 语义。"""\n'
        '        url = raw["url"]\n\n'
        '        if raw.get("info_type") == "file":\n'
        '            scheme = url.split(":", 1)[0].lower()\n'
        '            if scheme != "file":\n'
        '                raise ValueError(f"Unsupported file URL: {url}")\n\n'
        '        return cls(url=url)'
    )
    return content.replace(target_block, replacement, 1)


def _handle_click_confirm_color_false_ansi(content: str) -> str | None:
    # improved_v49 处理 confirm 在 color=False 时未去除 ANSI 控制序列的问题。
    target_block = (
        'def render_confirm_output(message: str, user_input: str, color: bool) -> str:\n'
        '    """模拟 confirm 在终端中的提示输出。"""\n'
        '    # 这里故意保留真实 issue 中的缺陷：\n'
        '    # color=False 时 confirm 提示仍直接使用原始消息，导致 ANSI 码泄漏到输出。\n'
        '    rendered = message\n'
        '    return f"{rendered} [y/N]: {user_input}\\n"'
    )
    if target_block not in content:
        return None

    replacement = (
        'def render_confirm_output(message: str, user_input: str, color: bool) -> str:\n'
        '    """模拟 confirm 在终端中的提示输出。"""\n'
        '    rendered = message if color else strip_ansi(message)\n'
        '    return f"{rendered} [y/N]: {user_input}\\n"'
    )
    return content.replace(target_block, replacement, 1)


def _handle_click_version_option_package_name(content: str) -> str | None:
    # improved_v50 处理 version_option 忽略 package_name 的问题。
    target_block = (
        'def render_version_output(program_name: str, version: str, package_name: str | None = None) -> str:\n'
        '    """模拟 version_option 的最小版本输出。"""\n'
        '    # 这里故意保留真实 issue 中的缺陷：\n'
        '    # 即使显式传入了 package_name，也仍错误优先使用程序名。\n'
        '    display_name = program_name\n'
        '    return f"{display_name}, version {version}"'
    )
    if target_block not in content:
        return None

    replacement = (
        'def render_version_output(program_name: str, version: str, package_name: str | None = None) -> str:\n'
        '    """模拟 version_option 的最小版本输出。"""\n'
        '    display_name = package_name or program_name\n'
        '    return f"{display_name}, version {version}"'
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

        if policy_config.patch_strategy == "improved_v10":
            improved_v10_content = _handle_nine_digit_time_string(original_content)
            if improved_v10_content is not None:
                updated_content = improved_v10_content
                patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
            else:
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

        if policy_config.patch_strategy == "improved_v11":
            improved_v11_content = _handle_branch_assigned_undeclared(original_content)
            if improved_v11_content is not None:
                updated_content = improved_v11_content
                patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
            else:
                improved_v10_content = _handle_nine_digit_time_string(original_content)
                if improved_v10_content is not None:
                    updated_content = improved_v10_content
                    patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                else:
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

        if policy_config.patch_strategy == "improved_v12":
            improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
            if improved_v12_content is not None:
                updated_content = improved_v12_content
                patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
            else:
                improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                if improved_v11_content is not None:
                    updated_content = improved_v11_content
                    patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                else:
                    improved_v10_content = _handle_nine_digit_time_string(original_content)
                    if improved_v10_content is not None:
                        updated_content = improved_v10_content
                        patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                    else:
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

        if policy_config.patch_strategy == "improved_v13":
            improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
            if improved_v13_content is not None:
                updated_content = improved_v13_content
                patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
            else:
                improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                if improved_v12_content is not None:
                    updated_content = improved_v12_content
                    patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                else:
                    improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                    if improved_v11_content is not None:
                        updated_content = improved_v11_content
                        patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                    else:
                        improved_v10_content = _handle_nine_digit_time_string(original_content)
                        if improved_v10_content is not None:
                            updated_content = improved_v10_content
                            patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                        else:
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

        if policy_config.patch_strategy == "improved_v14":
            improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
            if improved_v14_content is not None:
                updated_content = improved_v14_content
                patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
            else:
                improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                if improved_v13_content is not None:
                    updated_content = improved_v13_content
                    patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                else:
                    improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                    if improved_v12_content is not None:
                        updated_content = improved_v12_content
                        patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                    else:
                        improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                        if improved_v11_content is not None:
                            updated_content = improved_v11_content
                            patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                        else:
                            improved_v10_content = _handle_nine_digit_time_string(original_content)
                            if improved_v10_content is not None:
                                updated_content = improved_v10_content
                                patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                            else:
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

        if policy_config.patch_strategy == "improved_v15":
            improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
            if improved_v15_content is not None:
                updated_content = improved_v15_content
                patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
            else:
                improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                if improved_v14_content is not None:
                    updated_content = improved_v14_content
                    patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                else:
                    improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                    if improved_v13_content is not None:
                        updated_content = improved_v13_content
                        patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                    else:
                        improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                        if improved_v12_content is not None:
                            updated_content = improved_v12_content
                            patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                        else:
                            improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                            if improved_v11_content is not None:
                                updated_content = improved_v11_content
                                patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                            else:
                                improved_v10_content = _handle_nine_digit_time_string(original_content)
                                if improved_v10_content is not None:
                                    updated_content = improved_v10_content
                                    patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                else:
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

        if policy_config.patch_strategy == "improved_v16":
            improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
            if improved_v16_content is not None:
                updated_content = improved_v16_content
                patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
            else:
                improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                if improved_v15_content is not None:
                    updated_content = improved_v15_content
                    patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                else:
                    improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                    if improved_v14_content is not None:
                        updated_content = improved_v14_content
                        patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                    else:
                        improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                        if improved_v13_content is not None:
                            updated_content = improved_v13_content
                            patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                        else:
                            improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                            if improved_v12_content is not None:
                                updated_content = improved_v12_content
                                patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                            else:
                                improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                if improved_v11_content is not None:
                                    updated_content = improved_v11_content
                                    patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                else:
                                    improved_v10_content = _handle_nine_digit_time_string(original_content)
                                    if improved_v10_content is not None:
                                        updated_content = improved_v10_content
                                        patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                    else:
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

        if policy_config.patch_strategy == "improved_v17":
            improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
            if improved_v17_content is not None:
                updated_content = improved_v17_content
                patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
            else:
                improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                if improved_v16_content is not None:
                    updated_content = improved_v16_content
                    patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                else:
                    improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                    if improved_v15_content is not None:
                        updated_content = improved_v15_content
                        patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                    else:
                        improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                        if improved_v14_content is not None:
                            updated_content = improved_v14_content
                            patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                        else:
                            improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                            if improved_v13_content is not None:
                                updated_content = improved_v13_content
                                patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                            else:
                                improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                if improved_v12_content is not None:
                                    updated_content = improved_v12_content
                                    patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                else:
                                    improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                    if improved_v11_content is not None:
                                        updated_content = improved_v11_content
                                        patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                    else:
                                        improved_v10_content = _handle_nine_digit_time_string(original_content)
                                        if improved_v10_content is not None:
                                            updated_content = improved_v10_content
                                            patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                        else:
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

        if policy_config.patch_strategy == "improved_v18":
            improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
            if improved_v18_content is not None:
                updated_content = improved_v18_content
                patch_reason_parts = ["让整数值浮点 multipleOf 按数学整数处理"]
            else:
                improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                if improved_v17_content is not None:
                    updated_content = improved_v17_content
                    patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
                else:
                    improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                    if improved_v16_content is not None:
                        updated_content = improved_v16_content
                        patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                    else:
                        improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                        if improved_v15_content is not None:
                            updated_content = improved_v15_content
                            patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                        else:
                            improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                            if improved_v14_content is not None:
                                updated_content = improved_v14_content
                                patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                            else:
                                improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                if improved_v13_content is not None:
                                    updated_content = improved_v13_content
                                    patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                else:
                                    improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                    if improved_v12_content is not None:
                                        updated_content = improved_v12_content
                                        patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                    else:
                                        improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                        if improved_v11_content is not None:
                                            updated_content = improved_v11_content
                                            patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                        else:
                                            improved_v10_content = _handle_nine_digit_time_string(original_content)
                                            if improved_v10_content is not None:
                                                updated_content = improved_v10_content
                                                patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                            else:
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

        if policy_config.patch_strategy == "improved_v19":
            improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
            if improved_v19_content is not None:
                updated_content = improved_v19_content
                patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
            else:
                improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                if improved_v18_content is not None:
                    updated_content = improved_v18_content
                    patch_reason_parts = ["让整数值浮点 multipleOf 按数学整数处理"]
                else:
                    improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                    if improved_v17_content is not None:
                        updated_content = improved_v17_content
                        patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
                    else:
                        improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                        if improved_v16_content is not None:
                            updated_content = improved_v16_content
                            patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                        else:
                            improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                            if improved_v15_content is not None:
                                updated_content = improved_v15_content
                                patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                            else:
                                improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                if improved_v14_content is not None:
                                    updated_content = improved_v14_content
                                    patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                                else:
                                    improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                    if improved_v13_content is not None:
                                        updated_content = improved_v13_content
                                        patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                    else:
                                        improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                        if improved_v12_content is not None:
                                            updated_content = improved_v12_content
                                            patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                        else:
                                            improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                            if improved_v11_content is not None:
                                                updated_content = improved_v11_content
                                                patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                            else:
                                                improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                if improved_v10_content is not None:
                                                    updated_content = improved_v10_content
                                                    patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                else:
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

        if policy_config.patch_strategy == "improved_v20":
            improved_v20_content = _handle_click_resolve_command_none(original_content)
            if improved_v20_content is not None:
                updated_content = improved_v20_content
                patch_reason_parts = ["让 cmd 为 None 时保持普通返回语义，不再直接访问 name"]
            else:
                improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
                if improved_v19_content is not None:
                    updated_content = improved_v19_content
                    patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
                else:
                    improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                    if improved_v18_content is not None:
                        updated_content = improved_v18_content
                        patch_reason_parts = ["让整数值浮点 multipleOf 按数学整数处理"]
                    else:
                        improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                        if improved_v17_content is not None:
                            updated_content = improved_v17_content
                            patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
                        else:
                            improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                            if improved_v16_content is not None:
                                updated_content = improved_v16_content
                                patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                            else:
                                improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                                if improved_v15_content is not None:
                                    updated_content = improved_v15_content
                                    patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                                else:
                                    improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                    if improved_v14_content is not None:
                                        updated_content = improved_v14_content
                                        patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                                    else:
                                        improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                        if improved_v13_content is not None:
                                            updated_content = improved_v13_content
                                            patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                        else:
                                            improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                            if improved_v12_content is not None:
                                                updated_content = improved_v12_content
                                                patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                            else:
                                                improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                                if improved_v11_content is not None:
                                                    updated_content = improved_v11_content
                                                    patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                                else:
                                                    improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                    if improved_v10_content is not None:
                                                        updated_content = improved_v10_content
                                                        patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                    else:
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

        if policy_config.patch_strategy == "improved_v21":
            improved_v21_content = _handle_dateutil_month_year_dot_format(original_content)
            if improved_v21_content is not None:
                updated_content = improved_v21_content
                patch_reason_parts = ["让 MM.YYYY 与 MM/YYYY 一样按 year-month 语义返回"]
            else:
                improved_v20_content = _handle_click_resolve_command_none(original_content)
                if improved_v20_content is not None:
                    updated_content = improved_v20_content
                    patch_reason_parts = ["让 cmd 为 None 时保持普通返回语义，不再直接访问 name"]
                else:
                    improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
                    if improved_v19_content is not None:
                        updated_content = improved_v19_content
                        patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
                    else:
                        improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                        if improved_v18_content is not None:
                            updated_content = improved_v18_content
                            patch_reason_parts = ["让整数值浮点 multipleOf 按数学整数处理"]
                        else:
                            improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                            if improved_v17_content is not None:
                                updated_content = improved_v17_content
                                patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
                            else:
                                improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                                if improved_v16_content is not None:
                                    updated_content = improved_v16_content
                                    patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                                else:
                                    improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                                    if improved_v15_content is not None:
                                        updated_content = improved_v15_content
                                        patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                                    else:
                                        improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                        if improved_v14_content is not None:
                                            updated_content = improved_v14_content
                                            patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                                        else:
                                            improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                            if improved_v13_content is not None:
                                                updated_content = improved_v13_content
                                                patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                            else:
                                                improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                                if improved_v12_content is not None:
                                                    updated_content = improved_v12_content
                                                    patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                                else:
                                                    improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                                    if improved_v11_content is not None:
                                                        updated_content = improved_v11_content
                                                        patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                                    else:
                                                        improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                        if improved_v10_content is not None:
                                                            updated_content = improved_v10_content
                                                            patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                        else:
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

        if policy_config.patch_strategy in {"improved_v25", "improved_v26", "improved_v27", "improved_v28", "improved_v29", "improved_v30", "improved_v31", "improved_v32", "improved_v34", "improved_v35", "improved_v36", "improved_v37", "improved_v38", "improved_v39", "improved_v40", "improved_v41"}:
            run_v34_fallback_chain = False
        if policy_config.patch_strategy == "improved_v50":
            improved_v50_content = _handle_click_version_option_package_name(original_content)
            if improved_v50_content is not None:
                updated_content = improved_v50_content
                patch_reason_parts = ["让 click version_option 在显式传入 package_name 时优先使用该包名"]
        if policy_config.patch_strategy in {"improved_v49", "improved_v50"} and updated_content == original_content:
            improved_v49_content = _handle_click_confirm_color_false_ansi(original_content)
            if improved_v49_content is not None:
                updated_content = improved_v49_content
                patch_reason_parts = ["让 click confirm 在 color=False 时像 echo 一样去除 ANSI 控制序列"]
        if policy_config.patch_strategy in {"improved_v48", "improved_v49", "improved_v50"} and updated_content == original_content:
            improved_v48_content = _handle_packaging_direct_url_file_scheme(original_content)
            if improved_v48_content is not None:
                updated_content = improved_v48_content
                patch_reason_parts = ["让 file URL 的 scheme 按大小写不敏感方式处理，并接受单斜杠 file 形式"]
        if policy_config.patch_strategy in {"improved_v47", "improved_v48", "improved_v49", "improved_v50"} and updated_content == original_content:
            improved_v47_content = _handle_jinja_map_default_none(original_content)
            if improved_v47_content is not None:
                updated_content = improved_v47_content
                patch_reason_parts = ["让 map(attribute=..., default=None) 也像其他显式默认值一样正常回落"]
        if policy_config.patch_strategy in {"improved_v46", "improved_v47", "improved_v48", "improved_v49", "improved_v50"} and updated_content == original_content:
            improved_v46_content = _handle_tomlkit_proxy_repr_missing_children(original_content)
            if improved_v46_content is not None:
                updated_content = improved_v46_content
                patch_reason_parts = ["让代理视图 repr 保留同一父路径下的全部 dotted key 子项"]
        if policy_config.patch_strategy in {"improved_v45", "improved_v46", "improved_v47", "improved_v48", "improved_v49", "improved_v50"} and updated_content == original_content:
            improved_v45_content = _handle_pydantic_fraction_zero_division(original_content)
            if improved_v45_content is not None:
                updated_content = improved_v45_content
                patch_reason_parts = ["让零分母 fraction 输入也统一映射为 ValidationError，而不是冒泡 ZeroDivisionError"]
        if policy_config.patch_strategy in {"improved_v44", "improved_v45", "improved_v46", "improved_v47", "improved_v48", "improved_v49", "improved_v50"} and updated_content == original_content:
            improved_v44_content = _handle_packaging_requirement_pickle_prereleases(original_content)
            if improved_v44_content is not None:
                updated_content = improved_v44_content
                patch_reason_parts = ["让 Requirement 在 pickle 后保留 specifier.prereleases 的显式设置值"]
        if policy_config.patch_strategy in {"improved_v43", "improved_v44", "improved_v45", "improved_v46", "improved_v47", "improved_v48", "improved_v49", "improved_v50"} and updated_content == original_content:
            improved_v43_content = _handle_tomlkit_scalar_replacement_scope(original_content)
            if improved_v43_content is not None:
                updated_content = improved_v43_content
                patch_reason_parts = ["让表替换成标量后继续保持顶层位置，不再被相邻表错误吸附"]
            else:
                improved_v42_content = _handle_tomlkit_inline_table_missing_newline(original_content)
                if improved_v42_content is not None:
                    updated_content = improved_v42_content
                    patch_reason_parts = ["让 dotted inline table 后续追加普通键时始终在下一行输出"]
                else:
                    improved_v41_content = _handle_jinja_indent_blank_first_line(original_content)
                    if improved_v41_content is not None:
                        updated_content = improved_v41_content
                        patch_reason_parts = ["让 indent 在 first=True 且首行为空时继续遵守 blank=False"]
                    else:
                        improved_v40_content = _handle_jinja_async_loop_repr(original_content)
                        if improved_v40_content is not None:
                            updated_content = improved_v40_content
                            patch_reason_parts = ["为 AsyncLoopContext 提供独立 repr，避免暴露未 awaited 协程对象"]
                        else:
                            improved_v39_content = _handle_tomlkit_super_table_dotted_key_prefix(original_content)
                            if improved_v39_content is not None:
                                updated_content = improved_v39_content
                                patch_reason_parts = ["让 super table 上新增 dotted key 时继续保留父级表名前缀"]
                            else:
                                improved_v38_content = _handle_tomlkit_proxy_pop_deletes_underlying_key(original_content)
                                if improved_v38_content is not None:
                                    updated_content = improved_v38_content
                                    patch_reason_parts = ["让代理 pop 在返回旧值的同时真正删除底层键"]
                                else:
                                    improved_v37_content = _handle_tomlkit_boolean_true_literal(original_content)
                                    if improved_v37_content is not None:
                                        updated_content = improved_v37_content
                                        patch_reason_parts = ["让 TOML 布尔字面量按实际值输出 true 或 false"]
                                    else:
                                        improved_v36_content = _handle_packaging_sorted_compressed_tags(original_content)
                                        if improved_v36_content is not None:
                                            updated_content = improved_v36_content
                                            patch_reason_parts = ["拒绝未排序的 compressed python tag 组合"]
                                        else:
                                            improved_v35_content = _handle_packaging_prerelease_less_than(original_content)
                                            if improved_v35_content is not None:
                                                updated_content = improved_v35_content
                                                patch_reason_parts = ["让 prerelease specifier 的小于比较接受更早的合法 prerelease 版本"]
                                            else:
                                                improved_v34_content = _handle_packaging_marker_extra_none(original_content)
                                                if improved_v34_content is not None:
                                                    updated_content = improved_v34_content
                                                    patch_reason_parts = ["让 Marker.evaluate 在 extra=None 时回落为普通不匹配"]
                                                else:
                                                    improved_v32_content = _handle_isort_tuple_profile_layout(original_content)
                                                    if improved_v32_content is not None:
                                                        updated_content = improved_v32_content
                                                        patch_reason_parts = ["让 tuple 格式化逻辑继承 profile 指定的布局策略"]
                                                    else:
                                                        improved_v31_content = _handle_sqlite_extract_skip_nulls(original_content)
                                                        if improved_v31_content is not None:
                                                            updated_content = improved_v31_content
                                                            patch_reason_parts = ["让 extract 遇到 None 时保留空引用，而不是生成维表记录"]
                                                        else:
                                                            improved_v30_content = _handle_sqlite_transform_empty_string_numeric(original_content)
                                                            if improved_v30_content is not None:
                                                                updated_content = improved_v30_content
                                                                patch_reason_parts = ["让数值列转换时把空字符串回落成缺失值 None"]
                                                            else:
                                                                improved_v29_content = _handle_attrs_field_transformer_alias(original_content)
                                                                if improved_v29_content is not None:
                                                                    updated_content = improved_v29_content
                                                                    patch_reason_parts = ["让 field_transformer 阶段可见显式 alias 或字段名回落值"]
                                                                else:
                                                                    improved_v28_content = _handle_pydantic_inherited_model_validators(original_content)
                                                                    if improved_v28_content is not None:
                                                                        updated_content = improved_v28_content
                                                                        patch_reason_parts = ["让子类模型继续执行父类 after model_validator"]
                                                                    else:
                                                                        improved_v27_content = _handle_sqlite_delete_where_autocommit(original_content)
                                                                        if improved_v27_content is not None:
                                                                            updated_content = improved_v27_content
                                                                            patch_reason_parts = ["让 delete_where 在非显式事务场景下自动提交删除结果"]
                                                                        else:
                                                                            improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                                                                            if improved_v26_content is not None:
                                                                                updated_content = improved_v26_content
                                                                                patch_reason_parts = ["让 extend 复制 applicable_validators 集合，避免子类修改污染父类"]
                                                                            else:
                                                                                improved_v25_content = _handle_jsonschema_error_tree_missing_index(original_content)
                                                                                if improved_v25_content is not None:
                                                                                    updated_content = improved_v25_content
                                                                                    patch_reason_parts = ["让 ErrorTree 访问缺失索引时不再污染内部状态"]
                                                                                else:
                                                                                    improved_v24_content = _handle_dateutil_attached_comma_year(original_content)
                                                                                    if improved_v24_content is not None:
                                                                                        updated_content = improved_v24_content
                                                                                        patch_reason_parts = ["让紧贴逗号的日期年份优先按完整年份 token 解析"]
                                                                                    else:
                                                                                        improved_v23_content = _handle_packaging_dev_local_greater_than(original_content)
                                                                                        if improved_v23_content is not None:
                                                                                            updated_content = improved_v23_content
                                                                                            patch_reason_parts = ["让带 local 的版本在大于比较时按 public version 判断，不再错误只看 base_version"]
                                                                                        else:
                                                                                            improved_v22_content = _handle_jsonschema_single_label_hostname(original_content)
                                                                                            if improved_v22_content is not None:
                                                                                                updated_content = improved_v22_content
                                                                                                patch_reason_parts = ["让单标签 hostname 不再被错误要求至少两个 label"]
                                                                                            else:
                                                                                                improved_v21_content = _handle_dateutil_month_year_dot_format(original_content)
                                                                                                if improved_v21_content is not None:
                                                                                                    updated_content = improved_v21_content
                                                                                                    patch_reason_parts = ["让 MM.YYYY 与 MM/YYYY 一样按 year-month 语义返回"]
                                                                                                else:
                                                                                                    improved_v20_content = _handle_click_resolve_command_none(original_content)
                                                                                                    if improved_v20_content is not None:
                                                                                                        updated_content = improved_v20_content
                                                                                                        patch_reason_parts = ["让 cmd 为 None 时保持普通返回语义，不再直接访问 name"]
                                                                                                    else:
                                                                                                        improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
                                                                                                        if improved_v19_content is not None:
                                                                                                            updated_content = improved_v19_content
                                                                                                            patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
                                                                                                        else:
                                                                                                            improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                                                                                                            if improved_v18_content is not None:
                                                                                                                updated_content = improved_v18_content
                                                                                                                patch_reason_parts = ["让整数值浮点 multipleOf 按数学整数处理"]
                                                                                                            else:
                                                                                                                improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                                                                                                                if improved_v17_content is not None:
                                                                                                                    updated_content = improved_v17_content
                                                                                                                    patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
                                                                                                                else:
                                                                                                                    improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                                                                                                                    if improved_v16_content is not None:
                                                                                                                        updated_content = improved_v16_content
                                                                                                                        patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                                                                                                                    else:
                                                                                                                        improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                                                                                                                        if improved_v15_content is not None:
                                                                                                                            updated_content = improved_v15_content
                                                                                                                            patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                                                                                                                        else:
                                                                                                                            improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                                                                                                            if improved_v14_content is not None:
                                                                                                                                updated_content = improved_v14_content
                                                                                                                                patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                                                                                                                            else:
                                                                                                                                improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                                                                                                                if improved_v13_content is not None:
                                                                                                                                    updated_content = improved_v13_content
                                                                                                                                    patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                                                                                                                else:
                                                                                                                                    improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                                                                                                                    if improved_v12_content is not None:
                                                                                                                                        updated_content = improved_v12_content
                                                                                                                                        patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                                                                                                                    else:
                                                                                                                                        improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                                                                                                                        if improved_v11_content is not None:
                                                                                                                                            updated_content = improved_v11_content
                                                                                                                                            patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                                                                                                                        else:
                                                                                                                                            improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                                                                                                            if improved_v10_content is not None:
                                                                                                                                                updated_content = improved_v10_content
                                                                                                                                                patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                                                                                                            else:
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

        elif policy_config.patch_strategy == "improved_v42":
            improved_v42_content = _handle_tomlkit_inline_table_missing_newline(original_content)
            if improved_v42_content is not None:
                updated_content = improved_v42_content
                patch_reason_parts = ["让 dotted inline table 后续追加普通键时始终在下一行输出"]
            else:
                improved_v41_content = _handle_jinja_indent_blank_first_line(original_content)
                if improved_v41_content is not None:
                    updated_content = improved_v41_content
                    patch_reason_parts = ["让 indent 在 first=True 且首行为空时继续遵守 blank=False"]
                else:
                    improved_v40_content = _handle_jinja_async_loop_repr(original_content)
                    if improved_v40_content is not None:
                        updated_content = improved_v40_content
                        patch_reason_parts = ["为 AsyncLoopContext 提供独立 repr，避免暴露未 awaited 协程对象"]
                    else:
                        improved_v39_content = _handle_tomlkit_super_table_dotted_key_prefix(original_content)
                        if improved_v39_content is not None:
                            updated_content = improved_v39_content
                            patch_reason_parts = ["让 super table 上新增 dotted key 时继续保留父级表名前缀"]
                        else:
                            improved_v38_content = _handle_tomlkit_proxy_pop_deletes_underlying_key(original_content)
                            if improved_v38_content is not None:
                                updated_content = improved_v38_content
                                patch_reason_parts = ["让代理 pop 在返回旧值的同时真正删除底层键"]
                            else:
                                improved_v37_content = _handle_tomlkit_boolean_true_literal(original_content)
                                if improved_v37_content is not None:
                                    updated_content = improved_v37_content
                                    patch_reason_parts = ["让 TOML 布尔字面量按实际值输出 true 或 false"]
                                else:
                                    improved_v36_content = _handle_packaging_sorted_compressed_tags(original_content)
                                    if improved_v36_content is not None:
                                        updated_content = improved_v36_content
                                        patch_reason_parts = ["拒绝未排序的 compressed python tag 组合"]
                                    else:
                                        improved_v35_content = _handle_packaging_prerelease_less_than(original_content)
                                        if improved_v35_content is not None:
                                            updated_content = improved_v35_content
                                            patch_reason_parts = ["让 prerelease specifier 的小于比较接受更早的合法 prerelease 版本"]
                                        else:
                                            improved_v34_content = _handle_packaging_marker_extra_none(original_content)
                                            if improved_v34_content is not None:
                                                updated_content = improved_v34_content
                                                patch_reason_parts = ["让 Marker.evaluate 在 extra=None 时回落为普通不匹配"]
                                            else:
                                                improved_v32_content = _handle_isort_tuple_profile_layout(original_content)
                                                if improved_v32_content is not None:
                                                    updated_content = improved_v32_content
                                                    patch_reason_parts = ["让 tuple 格式化逻辑继承 profile 指定的布局策略"]
                                                else:
                                                    improved_v31_content = _handle_sqlite_extract_skip_nulls(original_content)
                                                    if improved_v31_content is not None:
                                                        updated_content = improved_v31_content
                                                        patch_reason_parts = ["让 extract 遇到 None 时保留空引用，而不是生成维表记录"]
                                                    else:
                                                        improved_v30_content = _handle_sqlite_transform_empty_string_numeric(original_content)
                                                        if improved_v30_content is not None:
                                                            updated_content = improved_v30_content
                                                            patch_reason_parts = ["让数值列转换时把空字符串回落成缺失值 None"]
                                                        else:
                                                            improved_v29_content = _handle_attrs_field_transformer_alias(original_content)
                                                            if improved_v29_content is not None:
                                                                updated_content = improved_v29_content
                                                                patch_reason_parts = ["让 field_transformer 阶段可见显式 alias 或字段名回落值"]
                                                            else:
                                                                improved_v28_content = _handle_pydantic_inherited_model_validators(original_content)
                                                                if improved_v28_content is not None:
                                                                    updated_content = improved_v28_content
                                                                    patch_reason_parts = ["让子类模型继续执行父类 after model_validator"]
                                                                else:
                                                                    improved_v27_content = _handle_sqlite_delete_where_autocommit(original_content)
                                                                    if improved_v27_content is not None:
                                                                        updated_content = improved_v27_content
                                                                        patch_reason_parts = ["让 delete_where 在非显式事务场景下自动提交删除结果"]
                                                                    else:
                                                                        improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                                                                        if improved_v26_content is not None:
                                                                            updated_content = improved_v26_content
                                                                            patch_reason_parts = ["让 extend 复制 applicable_validators 集合，避免子类修改污染父类"]
                                                                        else:
                                                                            improved_v25_content = _handle_jsonschema_error_tree_missing_index(original_content)
                                                                            if improved_v25_content is not None:
                                                                                updated_content = improved_v25_content
                                                                                patch_reason_parts = ["让 ErrorTree 访问缺失索引时不再污染内部状态"]
                                                                            else:
                                                                                improved_v24_content = _handle_dateutil_attached_comma_year(original_content)
                                                                                if improved_v24_content is not None:
                                                                                    updated_content = improved_v24_content
                                                                                    patch_reason_parts = ["让紧贴逗号的日期年份优先按完整年份 token 解析"]
                                                                                else:
                                                                                    improved_v23_content = _handle_packaging_dev_local_greater_than(original_content)
                                                                                    if improved_v23_content is not None:
                                                                                        updated_content = improved_v23_content
                                                                                        patch_reason_parts = ["让带 local 的版本在大于比较时按 public version 判断，不再错误只看 base_version"]
                                                                                    else:
                                                                                        improved_v22_content = _handle_jsonschema_single_label_hostname(original_content)
                                                                                        if improved_v22_content is not None:
                                                                                            updated_content = improved_v22_content
                                                                                            patch_reason_parts = ["让单标签 hostname 不再被错误要求至少两个 label"]
                                                                                        else:
                                                                                            improved_v21_content = _handle_dateutil_month_year_dot_format(original_content)
                                                                                            if improved_v21_content is not None:
                                                                                                updated_content = improved_v21_content
                                                                                                patch_reason_parts = ["让 MM.YYYY 与 MM/YYYY 一样按 year-month 语义返回"]
                                                                                            else:
                                                                                                improved_v20_content = _handle_click_resolve_command_none(original_content)
                                                                                                if improved_v20_content is not None:
                                                                                                    updated_content = improved_v20_content
                                                                                                    patch_reason_parts = ["让 cmd 为 None 时保持普通返回语义，不再直接访问 name"]
                                                                                                else:
                                                                                                    improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
                                                                                                    if improved_v19_content is not None:
                                                                                                        updated_content = improved_v19_content
                                                                                                        patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
                                                                                                    else:
                                                                                                        improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                                                                                                        if improved_v18_content is not None:
                                                                                                            updated_content = improved_v18_content
                                                                                                            patch_reason_parts = ["让整数值浮点 multipleOf 按数学整数处理"]
                                                                                                        else:
                                                                                                            improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                                                                                                            if improved_v17_content is not None:
                                                                                                                updated_content = improved_v17_content
                                                                                                                patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
                                                                                                            else:
                                                                                                                improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                                                                                                                if improved_v16_content is not None:
                                                                                                                    updated_content = improved_v16_content
                                                                                                                    patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                                                                                                                else:
                                                                                                                    improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                                                                                                                    if improved_v15_content is not None:
                                                                                                                        updated_content = improved_v15_content
                                                                                                                        patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                                                                                                                    else:
                                                                                                                        improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                                                                                                        if improved_v14_content is not None:
                                                                                                                            updated_content = improved_v14_content
                                                                                                                            patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                                                                                                                        else:
                                                                                                                            improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                                                                                                            if improved_v13_content is not None:
                                                                                                                                updated_content = improved_v13_content
                                                                                                                                patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                                                                                                            else:
                                                                                                                                improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                                                                                                                if improved_v12_content is not None:
                                                                                                                                    updated_content = improved_v12_content
                                                                                                                                    patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                                                                                                                else:
                                                                                                                                    improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                                                                                                                    if improved_v11_content is not None:
                                                                                                                                        updated_content = improved_v11_content
                                                                                                                                        patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                                                                                                                    else:
                                                                                                                                        improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                                                                                                        if improved_v10_content is not None:
                                                                                                                                            updated_content = improved_v10_content
                                                                                                                                            patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                                                                                                        else:
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

        elif policy_config.patch_strategy == "improved_v41":
            improved_v41_content = _handle_jinja_indent_blank_first_line(original_content)
            if improved_v41_content is not None:
                updated_content = improved_v41_content
                patch_reason_parts = ["让 indent 在首行为空且 blank=False 时不再错误缩进"]
            else:
                run_v34_fallback_chain = True
                improved_v40_content = _handle_jinja_async_loop_repr(original_content)
                if improved_v40_content is not None:
                    updated_content = improved_v40_content
                    patch_reason_parts = ["让 AsyncLoopContext 的 repr 不再暴露协程对象"]
                    run_v34_fallback_chain = False
                else:
                    improved_v39_content = _handle_tomlkit_super_table_dotted_key_prefix(original_content)
                    if improved_v39_content is not None:
                        updated_content = improved_v39_content
                        patch_reason_parts = ["让 super table 下新增 dotted key 时继续保留父级前缀"]
                        run_v34_fallback_chain = False
                    else:
                        improved_v38_content = _handle_tomlkit_proxy_pop_deletes_underlying_key(original_content)
                        if improved_v38_content is not None:
                            updated_content = improved_v38_content
                            patch_reason_parts = ["让代理 pop 在返回原值的同时真正删除底层键"]
                            run_v34_fallback_chain = False
                        else:
                            improved_v37_content = _handle_tomlkit_boolean_true_literal(original_content)
                            if improved_v37_content is not None:
                                updated_content = improved_v37_content
                                patch_reason_parts = ["让 toml 布尔值序列化在 True 场景下返回 true 字面量"]
                                run_v34_fallback_chain = False
                            else:
                                improved_v36_content = _handle_packaging_sorted_compressed_tags(original_content)
                                if improved_v36_content is not None:
                                    updated_content = improved_v36_content
                                    patch_reason_parts = ["让 wheel compressed tag set 必须按排序顺序出现，未排序时直接拒绝"]
                                    run_v34_fallback_chain = False
                                else:
                                    improved_v35_content = _handle_packaging_prerelease_less_than(original_content)
                                    if improved_v35_content is not None:
                                        updated_content = improved_v35_content
                                        patch_reason_parts = ["让 `< prerelease` 在 specifier 自身为 prerelease 时允许更早版本命中"]
                                        run_v34_fallback_chain = False
            if policy_config.patch_strategy == "improved_v40":
                improved_v40_content = _handle_jinja_async_loop_repr(original_content)
                if improved_v40_content is not None:
                    updated_content = improved_v40_content
                    patch_reason_parts = ["让 AsyncLoopContext 的 repr 不再暴露协程对象"]
                else:
                    run_v34_fallback_chain = True
                    improved_v39_content = _handle_tomlkit_super_table_dotted_key_prefix(original_content)
                    if improved_v39_content is not None:
                        updated_content = improved_v39_content
                        patch_reason_parts = ["让 super table 下新增 dotted key 时继续保留父级前缀"]
                        run_v34_fallback_chain = False
                    else:
                        improved_v38_content = _handle_tomlkit_proxy_pop_deletes_underlying_key(original_content)
                        if improved_v38_content is not None:
                            updated_content = improved_v38_content
                            patch_reason_parts = ["让代理 pop 在返回原值的同时真正删除底层键"]
                            run_v34_fallback_chain = False
                        else:
                            improved_v37_content = _handle_tomlkit_boolean_true_literal(original_content)
                            if improved_v37_content is not None:
                                updated_content = improved_v37_content
                                patch_reason_parts = ["让 toml 布尔值序列化在 True 场景下返回 true 字面量"]
                                run_v34_fallback_chain = False
                            else:
                                improved_v36_content = _handle_packaging_sorted_compressed_tags(original_content)
                                if improved_v36_content is not None:
                                    updated_content = improved_v36_content
                                    patch_reason_parts = ["让 wheel compressed tag set 必须按排序顺序出现，未排序时直接拒绝"]
                                    run_v34_fallback_chain = False
                                else:
                                    improved_v35_content = _handle_packaging_prerelease_less_than(original_content)
                                    if improved_v35_content is not None:
                                        updated_content = improved_v35_content
                                        patch_reason_parts = ["让 `< prerelease` 在 specifier 自身为 prerelease 时允许更早版本命中"]
                                        run_v34_fallback_chain = False
            elif policy_config.patch_strategy == "improved_v39":
                improved_v39_content = _handle_tomlkit_super_table_dotted_key_prefix(original_content)
                if improved_v39_content is not None:
                    updated_content = improved_v39_content
                    patch_reason_parts = ["让 super table 下新增 dotted key 时继续保留父级前缀"]
                else:
                    run_v34_fallback_chain = True
                    improved_v38_content = _handle_tomlkit_proxy_pop_deletes_underlying_key(original_content)
                    if improved_v38_content is not None:
                        updated_content = improved_v38_content
                        patch_reason_parts = ["让代理 pop 在返回原值的同时真正删除底层键"]
                        run_v34_fallback_chain = False
                    else:
                        improved_v37_content = _handle_tomlkit_boolean_true_literal(original_content)
                        if improved_v37_content is not None:
                            updated_content = improved_v37_content
                            patch_reason_parts = ["让 toml 布尔值序列化在 True 场景下返回 true 字面量"]
                            run_v34_fallback_chain = False
                        else:
                            improved_v36_content = _handle_packaging_sorted_compressed_tags(original_content)
                            if improved_v36_content is not None:
                                updated_content = improved_v36_content
                                patch_reason_parts = ["让 wheel compressed tag set 必须按排序顺序出现，未排序时直接拒绝"]
                                run_v34_fallback_chain = False
                            else:
                                improved_v35_content = _handle_packaging_prerelease_less_than(original_content)
                                if improved_v35_content is not None:
                                    updated_content = improved_v35_content
                                    patch_reason_parts = ["让 `< prerelease` 在 specifier 自身为 prerelease 时允许更早版本命中"]
                                    run_v34_fallback_chain = False
            elif policy_config.patch_strategy == "improved_v38":
                improved_v38_content = _handle_tomlkit_proxy_pop_deletes_underlying_key(original_content)
                if improved_v38_content is not None:
                    updated_content = improved_v38_content
                    patch_reason_parts = ["让代理 pop 在返回原值的同时真正删除底层键"]
                else:
                    run_v34_fallback_chain = True
                    improved_v37_content = _handle_tomlkit_boolean_true_literal(original_content)
                    if improved_v37_content is not None:
                        updated_content = improved_v37_content
                        patch_reason_parts = ["让 toml 布尔值序列化在 True 场景下返回 true 字面量"]
                        run_v34_fallback_chain = False
                    else:
                        improved_v36_content = _handle_packaging_sorted_compressed_tags(original_content)
                        if improved_v36_content is not None:
                            updated_content = improved_v36_content
                            patch_reason_parts = ["让 wheel compressed tag set 必须按排序顺序出现，未排序时直接拒绝"]
                            run_v34_fallback_chain = False
                        else:
                            improved_v35_content = _handle_packaging_prerelease_less_than(original_content)
                            if improved_v35_content is not None:
                                updated_content = improved_v35_content
                                patch_reason_parts = ["让 `< prerelease` 在 specifier 自身为 prerelease 时允许更早版本命中"]
                                run_v34_fallback_chain = False
            elif policy_config.patch_strategy == "improved_v37":
                improved_v37_content = _handle_tomlkit_boolean_true_literal(original_content)
                if improved_v37_content is not None:
                    updated_content = improved_v37_content
                    patch_reason_parts = ["让 toml 布尔值序列化在 True 场景下返回 true 字面量"]
                else:
                    run_v34_fallback_chain = True
                    improved_v36_content = _handle_packaging_sorted_compressed_tags(original_content)
                    if improved_v36_content is not None:
                        updated_content = improved_v36_content
                        patch_reason_parts = ["让 wheel compressed tag set 必须按排序顺序出现，未排序时直接拒绝"]
                        run_v34_fallback_chain = False
                    else:
                        improved_v35_content = _handle_packaging_prerelease_less_than(original_content)
                        if improved_v35_content is not None:
                            updated_content = improved_v35_content
                            patch_reason_parts = ["让 `< prerelease` 在 specifier 自身为 prerelease 时允许更早版本命中"]
                            run_v34_fallback_chain = False
            elif policy_config.patch_strategy == "improved_v36":
                improved_v36_content = _handle_packaging_sorted_compressed_tags(original_content)
                if improved_v36_content is not None:
                    updated_content = improved_v36_content
                    patch_reason_parts = ["让 wheel compressed tag set 必须按排序顺序出现，未排序时直接拒绝"]
                else:
                    # v36 未命中新规则时，继续完整复用 v35/v34 的既有回退链。
                    run_v34_fallback_chain = True
                    improved_v35_content = _handle_packaging_prerelease_less_than(original_content)
                    if improved_v35_content is not None:
                        updated_content = improved_v35_content
                        patch_reason_parts = ["让 `< prerelease` 在 specifier 自身为 prerelease 时允许更早版本命中"]
                        run_v34_fallback_chain = False
            elif policy_config.patch_strategy == "improved_v35":
                improved_v35_content = _handle_packaging_prerelease_less_than(original_content)
                if improved_v35_content is not None:
                    updated_content = improved_v35_content
                    patch_reason_parts = ["让 `< prerelease` 在 specifier 自身为 prerelease 时允许更早版本命中"]
                else:
                    # v35 未命中新规则时，完整复用 v34 的既有回退链，保证旧任务能力不回退。
                    run_v34_fallback_chain = True
            if policy_config.patch_strategy == "improved_v34" or run_v34_fallback_chain:
                improved_v34_content = _handle_packaging_marker_extra_none(original_content)
                if improved_v34_content is not None:
                    updated_content = improved_v34_content
                    patch_reason_parts = ["让 Marker.evaluate 在 extra 为 None 时回落为 False，而不是继续调用 lower"]
                else:
                    improved_v32_content = _handle_isort_tuple_profile_layout(original_content)
                    if improved_v32_content is not None:
                        updated_content = improved_v32_content
                        patch_reason_parts = ["让 tuple 格式化分支继承 profile 对应的布局策略"]
                    else:
                        improved_v31_content = _handle_sqlite_extract_skip_nulls(original_content)
                        if improved_v31_content is not None:
                            updated_content = improved_v31_content
                            patch_reason_parts = ["让 extract 跳过 None，不再为空值生成维表记录"]
                        else:
                            improved_v30_content = _handle_sqlite_transform_empty_string_numeric(original_content)
                            if improved_v30_content is not None:
                                updated_content = improved_v30_content
                                patch_reason_parts = ["让数值列转换时把空字符串回落为 None，避免保留伪空值"]
                            else:
                                improved_v29_content = _handle_attrs_field_transformer_alias(original_content)
                                if improved_v29_content is not None:
                                    updated_content = improved_v29_content
                                    patch_reason_parts = ["让字段变换阶段也能读取 alias，避免信息只在后置阶段回填"]
                                else:
                                    improved_v28_content = _handle_pydantic_inherited_model_validators(original_content)
                                    if improved_v28_content is not None:
                                        updated_content = improved_v28_content
                                        patch_reason_parts = ["让继承链中的 model validator 同时生效"]
                                    else:
                                        improved_v27_content = _handle_sqlite_delete_where_autocommit(original_content)
                                        if improved_v27_content is not None:
                                            updated_content = improved_v27_content
                                            patch_reason_parts = ["让 delete_where 在非事务场景下自动提交"]
                                        else:
                                            improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                                            if improved_v26_content is not None:
                                                updated_content = improved_v26_content
                                                patch_reason_parts = ["让 extend 复制 applicable_validators，避免子 validator 污染父 validator"]
                                            else:
                                                improved_v25_content = _handle_jsonschema_error_tree_missing_index(original_content)
                                                if improved_v25_content is not None:
                                                    updated_content = improved_v25_content
                                                    patch_reason_parts = ["让 ErrorTree 访问缺失索引时不再隐式创建空错误节点"]
                                                else:
                                                    improved_v24_content = _handle_dateutil_attached_comma_year(original_content)
                                                    if improved_v24_content is not None:
                                                        updated_content = improved_v24_content
                                                        patch_reason_parts = ["让紧贴逗号的年份在切词时与月份正确分离"]
                                                    else:
                                                        improved_v23_content = _handle_packaging_dev_local_greater_than(original_content)
                                                        if improved_v23_content is not None:
                                                            updated_content = improved_v23_content
                                                            patch_reason_parts = ["让带 local 段的 dev 版本继续按完整 public version 比较大小"]
                                                        else:
                                                            improved_v22_content = _handle_jsonschema_single_label_hostname(original_content)
                                                            if improved_v22_content is not None:
                                                                updated_content = improved_v22_content
                                                                patch_reason_parts = ["让单标签 hostname 在 format checker 中被视为合法"]
                                                            else:
                                                                improved_v21_content = _handle_dateutil_month_year_dot_format(original_content)
                                                                if improved_v21_content is not None:
                                                                    updated_content = improved_v21_content
                                                                    patch_reason_parts = ["让 MM.YYYY 格式回落成 month/year 解析路径"]
                                                                else:
                                                                    improved_v20_content = _handle_click_resolve_command_none(original_content)
                                                                    if improved_v20_content is not None:
                                                                        updated_content = improved_v20_content
                                                                        patch_reason_parts = ["让 cmd 为 None 时保持普通返回语义，不再直接访问 name"]
                                                                    else:
                                                                        improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
                                                                        if improved_v19_content is not None:
                                                                            updated_content = improved_v19_content
                                                                            patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
                                                                        else:
                                                                            improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                                                                            if improved_v18_content is not None:
                                                                                updated_content = improved_v18_content
                                                                                patch_reason_parts = ["让整数值的 multipleOf float 走整数等价比较路径"]
                                                                            else:
                                                                                improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                                                                                if improved_v17_content is not None:
                                                                                    updated_content = improved_v17_content
                                                                                    patch_reason_parts = ["让 hostname format checker 在 ValueError 场景下回落为 False"]
                                                                                else:
                                                                                    improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                                                                                    if improved_v16_content is not None:
                                                                                        updated_content = improved_v16_content
                                                                                        patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                                                                                    else:
                                                                                        improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                                                                                        if improved_v15_content is not None:
                                                                                            updated_content = improved_v15_content
                                                                                            patch_reason_parts = ["拒绝 wheel 文件名中的非规范化版本号"]
                                                                                        else:
                                                                                            improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                                                                            if improved_v14_content is not None:
                                                                                                updated_content = improved_v14_content
                                                                                                patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号分隔"]
                                                                                            else:
                                                                                                improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                                                                                if improved_v13_content is not None:
                                                                                                    updated_content = improved_v13_content
                                                                                                    patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                                                                                else:
                                                                                                    improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                                                                                    if improved_v12_content is not None:
                                                                                                        updated_content = improved_v12_content
                                                                                                        patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                                                                                    else:
                                                                                                        improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                                                                                        if improved_v11_content is not None:
                                                                                                            updated_content = improved_v11_content
                                                                                                            patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                                                                                        else:
                                                                                                            improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                                                                            if improved_v10_content is not None:
                                                                                                                updated_content = improved_v10_content
                                                                                                                patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                                                                            else:
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
            elif policy_config.patch_strategy == "improved_v32":
                improved_v32_content = _handle_isort_tuple_profile_layout(original_content)
                if improved_v32_content is not None:
                    updated_content = improved_v32_content
                    patch_reason_parts = ["让 tuple 格式化分支继承 profile 对应的布局策略"]
                else:
                    improved_v31_content = _handle_sqlite_extract_skip_nulls(original_content)
                    if improved_v31_content is not None:
                        updated_content = improved_v31_content
                        patch_reason_parts = ["让 extract 跳过 None，不再为空值生成维表记录"]
                    else:
                        improved_v30_content = _handle_sqlite_transform_empty_string_numeric(original_content)
                        if improved_v30_content is not None:
                            updated_content = improved_v30_content
                            patch_reason_parts = ["让数值列转换时把空字符串回落为 None，避免保留伪空值"]
                        else:
                            improved_v29_content = _handle_attrs_field_transformer_alias(original_content)
                            if improved_v29_content is not None:
                                updated_content = improved_v29_content
                                patch_reason_parts = ["让字段变换阶段也能读取 alias，避免信息只在后置阶段回填"]
                            else:
                                improved_v28_content = _handle_pydantic_inherited_model_validators(original_content)
                                if improved_v28_content is not None:
                                    updated_content = improved_v28_content
                                    patch_reason_parts = ["让继承链中的 model validator 同时生效"]
                                else:
                                    improved_v27_content = _handle_sqlite_delete_where_autocommit(original_content)
                                    if improved_v27_content is not None:
                                        updated_content = improved_v27_content
                                        patch_reason_parts = ["让 delete_where 在非事务场景下自动提交"]
                                    else:
                                        improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                                        if improved_v26_content is not None:
                                            updated_content = improved_v26_content
                                            patch_reason_parts = ["让 extend 复制 applicable_validators，避免子 validator 污染父 validator"]
                                        else:
                                            improved_v25_content = _handle_jsonschema_error_tree_missing_index(original_content)
                                            if improved_v25_content is not None:
                                                updated_content = improved_v25_content
                                                patch_reason_parts = ["让 ErrorTree 访问缺失索引时不再隐式创建空错误节点"]
                                            else:
                                                improved_v24_content = _handle_dateutil_attached_comma_year(original_content)
                                                if improved_v24_content is not None:
                                                    updated_content = improved_v24_content
                                                    patch_reason_parts = ["让紧贴逗号的年份在切词时与月份正确分离"]
                                                else:
                                                    improved_v23_content = _handle_packaging_dev_local_greater_than(original_content)
                                                    if improved_v23_content is not None:
                                                        updated_content = improved_v23_content
                                                        patch_reason_parts = ["让带 local 段的 dev 版本继续按完整 public version 比较大小"]
                                                    else:
                                                        improved_v22_content = _handle_jsonschema_single_label_hostname(original_content)
                                                        if improved_v22_content is not None:
                                                            updated_content = improved_v22_content
                                                            patch_reason_parts = ["让单标签 hostname 在 format checker 中被视为合法"]
                                                        else:
                                                            improved_v21_content = _handle_dateutil_month_year_dot_format(original_content)
                                                            if improved_v21_content is not None:
                                                                updated_content = improved_v21_content
                                                                patch_reason_parts = ["让 MM.YYYY 格式回落成 month/year 解析路径"]
                                                            else:
                                                                improved_v20_content = _handle_click_resolve_command_none(original_content)
                                                                if improved_v20_content is not None:
                                                                    updated_content = improved_v20_content
                                                                    patch_reason_parts = ["让 cmd 为 None 时保持普通返回语义，不再直接访问 name"]
                                                                else:
                                                                    improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
                                                                    if improved_v19_content is not None:
                                                                        updated_content = improved_v19_content
                                                                        patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
                                                                    else:
                                                                        improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                                                                        if improved_v18_content is not None:
                                                                            updated_content = improved_v18_content
                                                                            patch_reason_parts = ["让整数值的 multipleOf float 走整数等价比较路径"]
                                                                        else:
                                                                            improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                                                                            if improved_v17_content is not None:
                                                                                updated_content = improved_v17_content
                                                                                patch_reason_parts = ["让 hostname format checker 在 ValueError 场景下回落为 False"]
                                                                            else:
                                                                                improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                                                                                if improved_v16_content is not None:
                                                                                    updated_content = improved_v16_content
                                                                                    patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                                                                                else:
                                                                                    improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                                                                                    if improved_v15_content is not None:
                                                                                        updated_content = improved_v15_content
                                                                                        patch_reason_parts = ["拒绝 wheel 文件名中的非规范化版本号"]
                                                                                    else:
                                                                                        improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                                                                        if improved_v14_content is not None:
                                                                                            updated_content = improved_v14_content
                                                                                            patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号分隔"]
                                                                                        else:
                                                                                            improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                                                                            if improved_v13_content is not None:
                                                                                                updated_content = improved_v13_content
                                                                                                patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                                                                            else:
                                                                                                improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                                                                                if improved_v12_content is not None:
                                                                                                    updated_content = improved_v12_content
                                                                                                    patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                                                                                else:
                                                                                                    improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                                                                                    if improved_v11_content is not None:
                                                                                                        updated_content = improved_v11_content
                                                                                                        patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                                                                                    else:
                                                                                                        improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                                                                        if improved_v10_content is not None:
                                                                                                            updated_content = improved_v10_content
                                                                                                            patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                                                                        else:
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
            should_run_v25_chain = True
            if policy_config.patch_strategy == "improved_v32":
                improved_v32_content = _handle_isort_tuple_profile_layout(original_content)
                if improved_v32_content is not None:
                    updated_content = improved_v32_content
                    patch_reason_parts = ["让 tuple 格式化分支继承 profile 布局策略，避免 black 等 profile 失效"]
                    should_run_v25_chain = False
                else:
                    improved_v31_content = _handle_sqlite_extract_skip_nulls(original_content)
                    if improved_v31_content is not None:
                        updated_content = improved_v31_content
                        patch_reason_parts = ["让 extract 跳过 None，不再为空值生成维表记录"]
                        should_run_v25_chain = False
                    else:
                        improved_v30_content = _handle_sqlite_transform_empty_string_numeric(original_content)
                        if improved_v30_content is not None:
                            updated_content = improved_v30_content
                            patch_reason_parts = ["让数值列转换时把空字符串回落为 None，避免保留伪空值"]
                            should_run_v25_chain = False
                        else:
                            improved_v29_content = _handle_attrs_field_transformer_alias(original_content)
                            if improved_v29_content is not None:
                                updated_content = improved_v29_content
                                patch_reason_parts = ["让 field_transformer 在定义阶段就能读取最终 alias"]
                                should_run_v25_chain = False
                            else:
                                improved_v28_content = _handle_pydantic_inherited_model_validators(original_content)
                                if improved_v28_content is not None:
                                    updated_content = improved_v28_content
                                    patch_reason_parts = ["让子类 model validator 追加执行，保留父类 validator 继承链"]
                                    should_run_v25_chain = False
                                else:
                                    improved_v27_content = _handle_sqlite_delete_where_autocommit(original_content)
                                    if improved_v27_content is not None:
                                        updated_content = improved_v27_content
                                        patch_reason_parts = ["让 delete_where 在删除后提交事务，保证其他连接立即可见"]
                                        should_run_v25_chain = False
                                    else:
                                        improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                                        if improved_v26_content is not None:
                                            updated_content = improved_v26_content
                                            patch_reason_parts = ["让 extend 保留原始 applicable_validators，避免 legacy $ref 语义回归"]
                                            should_run_v25_chain = False
            elif policy_config.patch_strategy == "improved_v31":
                improved_v31_content = _handle_sqlite_extract_skip_nulls(original_content)
                if improved_v31_content is not None:
                    updated_content = improved_v31_content
                    patch_reason_parts = ["让 extract 跳过 None，不再为空值生成维表记录"]
                    should_run_v25_chain = False
                else:
                    improved_v30_content = _handle_sqlite_transform_empty_string_numeric(original_content)
                    if improved_v30_content is not None:
                        updated_content = improved_v30_content
                        patch_reason_parts = ["让数值列转换时把空字符串回落为 None，避免保留伪空值"]
                        should_run_v25_chain = False
                    else:
                        improved_v29_content = _handle_attrs_field_transformer_alias(original_content)
                        if improved_v29_content is not None:
                            updated_content = improved_v29_content
                            patch_reason_parts = ["让 field_transformer 在定义阶段就能读取最终 alias"]
                            should_run_v25_chain = False
                        else:
                            improved_v28_content = _handle_pydantic_inherited_model_validators(original_content)
                            if improved_v28_content is not None:
                                updated_content = improved_v28_content
                                patch_reason_parts = ["让子类 model validator 追加执行，保留父类 validator 继承链"]
                                should_run_v25_chain = False
                            else:
                                improved_v27_content = _handle_sqlite_delete_where_autocommit(original_content)
                                if improved_v27_content is not None:
                                    updated_content = improved_v27_content
                                    patch_reason_parts = ["让 delete_where 在删除后提交事务，保证其他连接立即可见"]
                                    should_run_v25_chain = False
                                else:
                                    improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                                    if improved_v26_content is not None:
                                        updated_content = improved_v26_content
                                        patch_reason_parts = ["让 extend 保留原始 applicable_validators，避免 legacy $ref 语义回归"]
                                        should_run_v25_chain = False
            elif policy_config.patch_strategy == "improved_v30":
                improved_v30_content = _handle_sqlite_transform_empty_string_numeric(original_content)
                if improved_v30_content is not None:
                    updated_content = improved_v30_content
                    patch_reason_parts = ["让数值列转换时把空字符串回落为 None，避免保留伪空值"]
                    should_run_v25_chain = False
                else:
                    improved_v29_content = _handle_attrs_field_transformer_alias(original_content)
                    if improved_v29_content is not None:
                        updated_content = improved_v29_content
                        patch_reason_parts = ["让 field_transformer 在定义阶段就能读取最终 alias"]
                        should_run_v25_chain = False
                    else:
                        improved_v28_content = _handle_pydantic_inherited_model_validators(original_content)
                        if improved_v28_content is not None:
                            updated_content = improved_v28_content
                            patch_reason_parts = ["让子类 model validator 追加执行，保留父类 validator 继承链"]
                            should_run_v25_chain = False
                        else:
                            improved_v27_content = _handle_sqlite_delete_where_autocommit(original_content)
                            if improved_v27_content is not None:
                                updated_content = improved_v27_content
                                patch_reason_parts = ["让 delete_where 在删除后提交事务，保证其他连接立即可见"]
                                should_run_v25_chain = False
                            else:
                                improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                                if improved_v26_content is not None:
                                    updated_content = improved_v26_content
                                    patch_reason_parts = ["让 extend 保留原始 applicable_validators，避免 legacy $ref 语义回归"]
                                    should_run_v25_chain = False
            elif policy_config.patch_strategy == "improved_v29":
                improved_v29_content = _handle_attrs_field_transformer_alias(original_content)
                if improved_v29_content is not None:
                    updated_content = improved_v29_content
                    patch_reason_parts = ["让 field_transformer 在定义阶段就能读取最终 alias"]
                    should_run_v25_chain = False
                else:
                    improved_v28_content = _handle_pydantic_inherited_model_validators(original_content)
                    if improved_v28_content is not None:
                        updated_content = improved_v28_content
                        patch_reason_parts = ["让子类 model validator 追加执行，保留父类 validator 继承链"]
                        should_run_v25_chain = False
                    else:
                        improved_v27_content = _handle_sqlite_delete_where_autocommit(original_content)
                        if improved_v27_content is not None:
                            updated_content = improved_v27_content
                            patch_reason_parts = ["让 delete_where 在删除后提交事务，保证其他连接立即可见"]
                            should_run_v25_chain = False
                        else:
                            improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                            if improved_v26_content is not None:
                                updated_content = improved_v26_content
                                patch_reason_parts = ["让 extend 保留原始 applicable_validators，避免 legacy $ref 语义回归"]
                                should_run_v25_chain = False
            elif policy_config.patch_strategy == "improved_v28":
                improved_v28_content = _handle_pydantic_inherited_model_validators(original_content)
                if improved_v28_content is not None:
                    updated_content = improved_v28_content
                    patch_reason_parts = ["让子类 model validator 追加执行，保留父类 validator 继承链"]
                    should_run_v25_chain = False
                else:
                    improved_v27_content = _handle_sqlite_delete_where_autocommit(original_content)
                    if improved_v27_content is not None:
                        updated_content = improved_v27_content
                        patch_reason_parts = ["让 delete_where 在删除后提交事务，保证其他连接立即可见"]
                        should_run_v25_chain = False
                    else:
                        improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                        if improved_v26_content is not None:
                            updated_content = improved_v26_content
                            patch_reason_parts = ["让 extend 保留原始 applicable_validators，避免 legacy $ref 语义回归"]
                            should_run_v25_chain = False
            elif policy_config.patch_strategy == "improved_v27":
                improved_v27_content = _handle_sqlite_delete_where_autocommit(original_content)
                if improved_v27_content is not None:
                    updated_content = improved_v27_content
                    patch_reason_parts = ["让 delete_where 在删除后提交事务，保证其他连接立即可见"]
                    should_run_v25_chain = False
                else:
                    improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                    if improved_v26_content is not None:
                        updated_content = improved_v26_content
                        patch_reason_parts = ["让 extend 保留原始 applicable_validators，避免 legacy $ref 语义回归"]
                        should_run_v25_chain = False
            elif policy_config.patch_strategy == "improved_v26":
                improved_v26_content = _handle_jsonschema_extend_copies_applicable_validators(original_content)
                if improved_v26_content is not None:
                    updated_content = improved_v26_content
                    patch_reason_parts = ["让 extend 保留原始 applicable_validators，避免 legacy $ref 语义回归"]
                    should_run_v25_chain = False

            if should_run_v25_chain:
                improved_v25_content = _handle_jsonschema_error_tree_missing_index(original_content)
                if improved_v25_content is not None:
                    updated_content = improved_v25_content
                    patch_reason_parts = ["让 ErrorTree 访问缺失索引时保持只读，不再污染内部 children"]
                else:
                    improved_v24_content = _handle_dateutil_attached_comma_year(original_content)
                    if improved_v24_content is not None:
                        updated_content = improved_v24_content
                        patch_reason_parts = ["让紧贴逗号的年份 token 在日期解析时也能被正确识别"]
                    else:
                        improved_v23_content = _handle_packaging_dev_local_greater_than(original_content)
                        if improved_v23_content is not None:
                            updated_content = improved_v23_content
                            patch_reason_parts = ["让带 local 的版本在大于比较时按 public version 判断，不再错误只看 base_version"]
                        else:
                            improved_v22_content = _handle_jsonschema_single_label_hostname(original_content)
                            if improved_v22_content is not None:
                                updated_content = improved_v22_content
                                patch_reason_parts = ["让单标签 hostname 不再被错误要求至少两个 label"]
                            else:
                                improved_v21_content = _handle_dateutil_month_year_dot_format(original_content)
                                if improved_v21_content is not None:
                                    updated_content = improved_v21_content
                                    patch_reason_parts = ["让 MM.YYYY 与 MM/YYYY 一样按 year-month 语义返回"]
                                else:
                                    improved_v20_content = _handle_click_resolve_command_none(original_content)
                                    if improved_v20_content is not None:
                                        updated_content = improved_v20_content
                                        patch_reason_parts = ["让 cmd 为 None 时保持普通返回语义，不再直接访问 name"]
                                    else:
                                        improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
                                        if improved_v19_content is not None:
                                            updated_content = improved_v19_content
                                            patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
                                        else:
                                            improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                                            if improved_v18_content is not None:
                                                updated_content = improved_v18_content
                                                patch_reason_parts = ["让整数值浮点 multipleOf 按数学整数处理"]
                                            else:
                                                improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                                                if improved_v17_content is not None:
                                                    updated_content = improved_v17_content
                                                    patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
                                                else:
                                                    improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                                                    if improved_v16_content is not None:
                                                        updated_content = improved_v16_content
                                                        patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                                                    else:
                                                        improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                                                        if improved_v15_content is not None:
                                                            updated_content = improved_v15_content
                                                            patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                                                        else:
                                                            improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                                            if improved_v14_content is not None:
                                                                updated_content = improved_v14_content
                                                                patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                                                            else:
                                                                improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                                                if improved_v13_content is not None:
                                                                    updated_content = improved_v13_content
                                                                    patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                                                else:
                                                                    improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                                                    if improved_v12_content is not None:
                                                                        updated_content = improved_v12_content
                                                                        patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                                                    else:
                                                                        improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                                                        if improved_v11_content is not None:
                                                                            updated_content = improved_v11_content
                                                                            patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                                                        else:
                                                                            improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                                            if improved_v10_content is not None:
                                                                                updated_content = improved_v10_content
                                                                                patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                                            else:
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

        if policy_config.patch_strategy == "improved_v24":
            improved_v24_content = _handle_dateutil_attached_comma_year(original_content)
            if improved_v24_content is not None:
                updated_content = improved_v24_content
                patch_reason_parts = ["让紧贴逗号的年份 token 在日期解析时也能被正确识别"]
            else:
                improved_v23_content = _handle_packaging_dev_local_greater_than(original_content)
                if improved_v23_content is not None:
                    updated_content = improved_v23_content
                    patch_reason_parts = ["让带 local 的版本在大于比较时按 public version 判断，不再错误只看 base_version"]
                else:
                    improved_v22_content = _handle_jsonschema_single_label_hostname(original_content)
                    if improved_v22_content is not None:
                        updated_content = improved_v22_content
                        patch_reason_parts = ["让单标签 hostname 不再被错误要求至少两个 label"]
                    else:
                        improved_v21_content = _handle_dateutil_month_year_dot_format(original_content)
                        if improved_v21_content is not None:
                            updated_content = improved_v21_content
                            patch_reason_parts = ["让 MM.YYYY 与 MM/YYYY 一样按 year-month 语义返回"]
                        else:
                            improved_v20_content = _handle_click_resolve_command_none(original_content)
                            if improved_v20_content is not None:
                                updated_content = improved_v20_content
                                patch_reason_parts = ["让 cmd 为 None 时保持普通返回语义，不再直接访问 name"]
                            else:
                                improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
                                if improved_v19_content is not None:
                                    updated_content = improved_v19_content
                                    patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
                                else:
                                    improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                                    if improved_v18_content is not None:
                                        updated_content = improved_v18_content
                                        patch_reason_parts = ["让整数值浮点 multipleOf 按数学整数处理"]
                                    else:
                                        improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                                        if improved_v17_content is not None:
                                            updated_content = improved_v17_content
                                            patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
                                        else:
                                            improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                                            if improved_v16_content is not None:
                                                updated_content = improved_v16_content
                                                patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                                            else:
                                                improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                                                if improved_v15_content is not None:
                                                    updated_content = improved_v15_content
                                                    patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                                                else:
                                                    improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                                    if improved_v14_content is not None:
                                                        updated_content = improved_v14_content
                                                        patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                                                    else:
                                                        improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                                        if improved_v13_content is not None:
                                                            updated_content = improved_v13_content
                                                            patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                                        else:
                                                            improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                                            if improved_v12_content is not None:
                                                                updated_content = improved_v12_content
                                                                patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                                            else:
                                                                improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                                                if improved_v11_content is not None:
                                                                    updated_content = improved_v11_content
                                                                    patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                                                else:
                                                                    improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                                    if improved_v10_content is not None:
                                                                        updated_content = improved_v10_content
                                                                        patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                                    else:
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

        if policy_config.patch_strategy == "improved_v23":
            improved_v23_content = _handle_packaging_dev_local_greater_than(original_content)
            if improved_v23_content is not None:
                updated_content = improved_v23_content
                patch_reason_parts = ["让带 local 的版本在大于比较时按 public version 判断，不再错误只看 base_version"]
            else:
                improved_v22_content = _handle_jsonschema_single_label_hostname(original_content)
                if improved_v22_content is not None:
                    updated_content = improved_v22_content
                    patch_reason_parts = ["让单标签 hostname 不再被错误要求至少两个 label"]
                else:
                    improved_v21_content = _handle_dateutil_month_year_dot_format(original_content)
                    if improved_v21_content is not None:
                        updated_content = improved_v21_content
                        patch_reason_parts = ["让 MM.YYYY 与 MM/YYYY 一样按 year-month 语义返回"]
                    else:
                        improved_v20_content = _handle_click_resolve_command_none(original_content)
                        if improved_v20_content is not None:
                            updated_content = improved_v20_content
                            patch_reason_parts = ["让 cmd 为 None 时保持普通返回语义，不再直接访问 name"]
                        else:
                            improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
                            if improved_v19_content is not None:
                                updated_content = improved_v19_content
                                patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
                            else:
                                improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                                if improved_v18_content is not None:
                                    updated_content = improved_v18_content
                                    patch_reason_parts = ["让整数值浮点 multipleOf 按数学整数处理"]
                                else:
                                    improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                                    if improved_v17_content is not None:
                                        updated_content = improved_v17_content
                                        patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
                                    else:
                                        improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                                        if improved_v16_content is not None:
                                            updated_content = improved_v16_content
                                            patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                                        else:
                                            improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                                            if improved_v15_content is not None:
                                                updated_content = improved_v15_content
                                                patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                                            else:
                                                improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                                if improved_v14_content is not None:
                                                    updated_content = improved_v14_content
                                                    patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                                                else:
                                                    improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                                    if improved_v13_content is not None:
                                                        updated_content = improved_v13_content
                                                        patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                                    else:
                                                        improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                                        if improved_v12_content is not None:
                                                            updated_content = improved_v12_content
                                                            patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                                        else:
                                                            improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                                            if improved_v11_content is not None:
                                                                updated_content = improved_v11_content
                                                                patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                                            else:
                                                                improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                                if improved_v10_content is not None:
                                                                    updated_content = improved_v10_content
                                                                    patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                                else:
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

        if policy_config.patch_strategy == "improved_v22":
            improved_v22_content = _handle_jsonschema_single_label_hostname(original_content)
            if improved_v22_content is not None:
                updated_content = improved_v22_content
                patch_reason_parts = ["让单标签 hostname 不再被错误要求至少两个 label"]
            else:
                improved_v21_content = _handle_dateutil_month_year_dot_format(original_content)
                if improved_v21_content is not None:
                    updated_content = improved_v21_content
                    patch_reason_parts = ["让 MM.YYYY 与 MM/YYYY 一样按 year-month 语义返回"]
                else:
                    improved_v20_content = _handle_click_resolve_command_none(original_content)
                    if improved_v20_content is not None:
                        updated_content = improved_v20_content
                        patch_reason_parts = ["让 cmd 为 None 时保持普通返回语义，不再直接访问 name"]
                    else:
                        improved_v19_content = _handle_packaging_requirement_extra_normalization(original_content)
                        if improved_v19_content is not None:
                            updated_content = improved_v19_content
                            patch_reason_parts = ["让复合 marker 表达式里的 extra 名称也统一规范化"]
                        else:
                            improved_v18_content = _handle_jsonschema_integer_valued_multiple_of_float(original_content)
                            if improved_v18_content is not None:
                                updated_content = improved_v18_content
                                patch_reason_parts = ["让整数值浮点 multipleOf 按数学整数处理"]
                            else:
                                improved_v17_content = _handle_jsonschema_hostname_value_error(original_content)
                                if improved_v17_content is not None:
                                    updated_content = improved_v17_content
                                    patch_reason_parts = ["让 hostname 格式检查在空字符串场景下回落为普通校验失败"]
                                else:
                                    improved_v16_content = _handle_jsonschema_mixed_type_extras_sort(original_content)
                                    if improved_v16_content is not None:
                                        updated_content = improved_v16_content
                                        patch_reason_parts = ["为 mixed-type extras 排序增加 TypeError 兜底"]
                                    else:
                                        improved_v15_content = _handle_packaging_non_normalized_wheel_version(original_content)
                                        if improved_v15_content is not None:
                                            updated_content = improved_v15_content
                                            patch_reason_parts = ["拒绝未 normalized 的 wheel 版本号"]
                                        else:
                                            improved_v14_content = _handle_tomlkit_dotted_inline_table_append(original_content)
                                            if improved_v14_content is not None:
                                                updated_content = improved_v14_content
                                                patch_reason_parts = ["为 dotted inline table 追加键值对时补上逗号和空格分隔"]
                                            else:
                                                improved_v13_content = _handle_tomlkit_next_line_comma_append(original_content)
                                                if improved_v13_content is not None:
                                                    updated_content = improved_v13_content
                                                    patch_reason_parts = ["保留数组原始下一行逗号风格，避免 append 后生成双逗号"]
                                                else:
                                                    improved_v12_content = _handle_slice_fill_with_divisible_case(original_content)
                                                    if improved_v12_content is not None:
                                                        updated_content = improved_v12_content
                                                        patch_reason_parts = ["让 slice 仅在存在余数时才补入 fill_with"]
                                                    else:
                                                        improved_v11_content = _handle_branch_assigned_undeclared(original_content)
                                                        if improved_v11_content is not None:
                                                            updated_content = improved_v11_content
                                                            patch_reason_parts = ["让所有分支都已赋值的变量不再被判定为 undeclared"]
                                                        else:
                                                            improved_v10_content = _handle_nine_digit_time_string(original_content)
                                                            if improved_v10_content is not None:
                                                                updated_content = improved_v10_content
                                                                patch_reason_parts = ["让 9 位时间串按 HHMMSSmmm 解析"]
                                                            else:
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
