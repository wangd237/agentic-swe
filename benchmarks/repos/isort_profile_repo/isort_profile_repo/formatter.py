"""从 isort#1815 提炼出的最小 profile 分派实现。"""

from __future__ import annotations


PROFILE_LAYOUTS = {
    "default": "compact",
    "black": "vertical",
}


def get_layout_for_profile(profile: str | None) -> str:
    """返回 profile 对应的布局策略。"""

    return PROFILE_LAYOUTS.get(profile or "default", "compact")


def format_tuple(values: list[str], *, profile: str | None = None) -> str:
    """按最小规则格式化 tuple。"""

    layout = get_layout_for_profile(None)
    # 这里故意保留真实 issue 中的缺陷：tuple 分支忽略了传入 profile。
    if layout == "vertical":
        inner = "\n".join(f'    "{value}",' for value in values)
        return "(\n" + inner + "\n)"

    return "(" + ", ".join(f'"{value}"' for value in values) + ")"
