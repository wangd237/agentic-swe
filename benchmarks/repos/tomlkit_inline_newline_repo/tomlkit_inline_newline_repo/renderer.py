"""从 tomlkit#440 提炼出的最小 inline table 渲染实现。"""

from __future__ import annotations


def render_document_after_inline_table_append(
    section: str,
    inline_key: str,
    appended_key: str,
    appended_value: int,
    *,
    original_has_trailing_newline: bool = False,
) -> str:
    """渲染一个“inline table 后继续追加普通键”的最小文档。"""
    lines = [f"[{section}]"]
    inline_line = f"{inline_key} = {{}}"

    if original_has_trailing_newline:
        lines.append(inline_line)
        lines.append(f"{appended_key} = {appended_value}")
        return "\n".join(lines) + "\n"

    # 这里故意保留真实 issue 中的缺陷：
    # dotted inline table 且原始文本末尾没有换行时，错误把后续键直接黏在同一行。
    if "." in inline_key:
        lines.append(f"{inline_line}{appended_key} = {appended_value}")
        return "\n".join(lines) + "\n"

    lines.append(inline_line)
    lines.append(f"{appended_key} = {appended_value}")
    return "\n".join(lines) + "\n"
