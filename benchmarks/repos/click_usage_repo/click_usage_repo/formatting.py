"""从 click#3362 提炼出的最小 usage 换行实现。"""

from __future__ import annotations

import textwrap


def wrap_usage(program_name: str, options: list[str], width: int) -> str:
    """模拟 HelpFormatter.write_usage 的最小换行逻辑。"""
    usage_text = f"Usage: {program_name} {' '.join(options)}"
    wrapped_lines = textwrap.wrap(
        usage_text,
        width=width,
        subsequent_indent=" " * 15,
    )
    return "\n".join(wrapped_lines)
