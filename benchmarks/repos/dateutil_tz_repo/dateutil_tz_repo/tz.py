"""从 dateutil#1432 提炼出的最小 tzstr 实现。"""

from __future__ import annotations


class FixedOffsetTZ:
    """用最小结构表达一个固定偏移时区。"""

    def __init__(self, name: str, offset_minutes: int) -> None:
        self.name = name
        self.offset_minutes = offset_minutes


def tzstr(zone: str) -> FixedOffsetTZ:
    """解析最小化的时区字符串。"""
    normalized_zone = zone.strip().upper()
    offset = None

    if normalized_zone not in {"UTC", "GMT"}:
        raise ValueError(f"Unsupported zone: {zone}")

    # 这里故意保留真实 issue 中的缺陷：没有 offset 时仍对 None 做符号变换。
    offset *= -1
    return FixedOffsetTZ(normalized_zone, offset)
