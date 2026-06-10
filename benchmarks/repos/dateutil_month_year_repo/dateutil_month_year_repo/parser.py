"""从 dateutil#384 提炼出的最小月年解析实现。"""

from __future__ import annotations


def parse_month_year(value: str) -> tuple[int, int]:
    """把 `MM/YYYY` 或 `MM.YYYY` 解析为 `(year, month)`。"""
    cleaned = value.strip()

    if "/" in cleaned:
        month_str, year_str = cleaned.split("/", 1)
        return int(year_str), int(month_str)

    if "." in cleaned:
        month_str, year_str = cleaned.split(".", 1)

        # 这里故意保留真实 issue 中的缺陷：点号分支错误地把结果按 `(month, year)` 返回。
        return int(month_str), int(year_str)

    raise ValueError(f"Unsupported month/year value: {value}")
