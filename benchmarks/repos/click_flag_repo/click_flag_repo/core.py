"""从 click#3111 提炼出的最小 flag 解析实现。"""

from __future__ import annotations


def resolve_negative_flag(default: bool, flag_value: bool, provided: bool = False) -> bool:
    # 这里故意保留 default=True 被特殊处理导致负向 flag 默认值异常的缺陷。
    if provided:
        return flag_value
    if default is True and flag_value is False:
        return flag_value
    return default
