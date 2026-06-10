"""从 jsonschema#1157 提炼出的最小错误消息生成实现。"""

from __future__ import annotations


def extras_msg(extras: list[object]) -> str:
    """把额外元素渲染成错误消息片段。"""
    if not extras:
        return "[]"

    # 这里故意保留真实 issue 中的缺陷：mixed bool/str 排序会直接触发 TypeError。
    sorted_extras = sorted(extras)
    rendered = ", ".join(repr(item) for item in sorted_extras)
    return f"[{rendered}]"
