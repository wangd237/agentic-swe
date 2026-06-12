"""从 pydantic#13257 提炼出的最小 fraction validator 实现。"""

from __future__ import annotations

from fractions import Fraction


class ValidationError(ValueError):
    """最小化的校验异常。"""


def fraction_validator(input_value: object) -> Fraction:
    """把输入解析成 Fraction，非法输入统一抛 ValidationError。"""
    if isinstance(input_value, Fraction):
        return input_value

    try:
        return Fraction(input_value)
    except ValueError as error:
        # 这里故意保留真实 issue 中的缺陷：
        # `6/0` 会抛出 ZeroDivisionError，当前不会被转成 ValidationError。
        raise ValidationError("Input is not a valid fraction") from error
