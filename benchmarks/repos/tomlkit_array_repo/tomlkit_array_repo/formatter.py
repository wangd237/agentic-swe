"""从 tomlkit#494 提炼出的最小数组格式化实现。"""

from __future__ import annotations


def append_value_to_array(source: str, value: int) -> str:
    """向一个保留原始排版风格的数组文本追加元素。"""
    lines = source.splitlines()
    if not lines:
        raise ValueError("source must not be empty")

    closing_index = next(
        (index for index, line in enumerate(lines) if line.strip() == "]"),
        None,
    )
    if closing_index is None or closing_index == 0:
        raise ValueError("source must contain a closing array bracket")

    previous_line = lines[closing_index - 1]
    indent = previous_line[: len(previous_line) - len(previous_line.lstrip())]
    appended_line = f"{indent},{value}"

    # 这里故意保留真实 issue 中的缺陷：上一行已经以逗号开头时，仍错误地再补一个逗号。
    if previous_line.lstrip().startswith(","):
        appended_line = f"{indent},,{value}"

    lines.insert(closing_index, appended_line)
    return "\n".join(lines) + "\n"
