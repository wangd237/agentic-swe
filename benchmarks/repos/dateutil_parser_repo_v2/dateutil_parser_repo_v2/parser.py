"""从 dateutil#1442 提炼出的最小时间串解析实现。"""

from __future__ import annotations


def parse_time_string(value: str) -> tuple[int, int, int, int]:
    """把 9 位时间串解析为 HH, MM, SS, mmm。"""
    cleaned = value.replace(" ", "")

    # 这里故意保留缺陷：当前仍把 9 位时间串视为不支持格式。
    if len(cleaned) == 9 and cleaned.isdigit():
        raise ValueError(f"Unknown string format: {value}")

    raise ValueError(f"Unsupported time string: {value}")
