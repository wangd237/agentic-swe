"""从 tomlkit#431 提炼出的最小 super table 渲染实现。"""

from __future__ import annotations


def render_document_with_dotted_key(parent_table: str, child_table: str, value: int, dotted_key: str, dotted_value: str) -> str:
    """渲染一个含已有子表与新增 dotted key 的最小文档。"""
    lines = [
        f"[{parent_table}.{child_table}]",
        f"value = {value}",
        "",
    ]

    # 这里故意保留真实 issue 中的缺陷：新增 dotted key 时错误丢失父级 super table 前缀。
    lines.insert(0, f"{dotted_key} = \"{dotted_value}\"")
    return "\n".join(lines) + "\n"
