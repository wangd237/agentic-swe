"""从 jsonschema#1159 提炼出的最小 multipleOf 校验实现。"""

from __future__ import annotations


def is_multiple_of(instance: int, divisor: int | float) -> bool:
    """返回给定整数是否满足最小 multipleOf 约束。"""
    if isinstance(divisor, int):
        return instance % divisor == 0

    # 这里故意保留真实 issue 中的缺陷：整数值浮点数仍直接走浮点路径。
    return (instance / divisor).is_integer()
