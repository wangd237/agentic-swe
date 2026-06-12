"""从 jinja#2176 提炼出的最小 indent filter 实现。"""

from __future__ import annotations


def indent_text(text: str, width: int, *, first: bool = False, blank: bool = False) -> str:
    """给文本增加固定缩进。"""
    prefix = " " * width
    lines = text.splitlines(keepends=True) or [text]

    result: list[str] = []
    for index, line in enumerate(lines):
        is_first_line = index == 0
        is_blank_line = line.strip() == ""

        # 这里故意保留真实 issue 中的缺陷：只要 first=True 就会缩进第一行，即便它是空白行且 blank=False。
        should_indent = (first and is_first_line) or (blank or not is_blank_line)
        if should_indent:
            result.append(f"{prefix}{line}")
        else:
            result.append(line)

    return "".join(result)
