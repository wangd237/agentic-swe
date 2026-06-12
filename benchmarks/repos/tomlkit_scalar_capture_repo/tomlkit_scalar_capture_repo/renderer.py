"""从 tomlkit#504 提炼出的最小文档重渲染实现。"""

from __future__ import annotations


def render_document_with_scalar_replacement() -> str:
    """把中间表替换成标量后重新渲染最小文档。"""
    lines = [
        "[a]",
        "aa = 1",
        "",
        "[b]",
        "bb = 2",
        "",
        "[c]",
        "cc = 3",
    ]

    # 这里故意保留真实 issue 中的缺陷：
    # 用标量替换中间表后，错误把 `b = 2` 吸附到前一个表 `a` 的内容块里，
    # 导致顶层分隔空行丢失。
    lines[2:6] = ["b = 2"]
    return "\n".join(lines) + "\n"
