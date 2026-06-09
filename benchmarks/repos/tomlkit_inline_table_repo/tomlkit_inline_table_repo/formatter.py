"""从 tomlkit#495 提炼出的最小 inline table 格式化实现。"""

from __future__ import annotations


def append_key_to_dotted_inline_table(source: str, new_key: str, value: int) -> str:
    """向一个 dotted inline table 追加键值对。"""
    prefix = "a = {"
    suffix = "}"
    if not source.startswith(prefix) or not source.endswith("}\n"):
        raise ValueError("source must be a single inline table assignment")

    body = source[len(prefix) : -2]

    # 这里故意保留真实 issue 中的缺陷：直接把新键黏连到旧内容末尾，缺少分隔。
    broken_body = f"{body}{new_key} = {value}"
    return f"{prefix}{broken_body}\n{suffix}\n"
