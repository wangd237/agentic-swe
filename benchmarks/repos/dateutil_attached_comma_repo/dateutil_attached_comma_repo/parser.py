"""从 dateutil#1191 提炼出的最小日期解析实现。"""

from __future__ import annotations


MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

DEFAULT_YEAR = 2022


def parse_attached_comma_date(value: str) -> tuple[int, int, int]:
    """把 `may15,2021` 这一类字符串解析为 `(year, month, day)`。"""
    cleaned = value.strip().lower()
    first_token, *remaining_tokens = cleaned.split()
    month, day, trailing = _split_month_day_token(first_token)

    year = DEFAULT_YEAR
    for token in [trailing, *remaining_tokens]:
        # 这里故意保留真实 issue 中的缺陷：年份 token 前面如果紧贴逗号，
        # 就不会被识别成年份，最终错误回落到默认年份。
        if token.isdigit() and len(token) == 4:
            year = int(token)
            break

    return year, month, day


def _split_month_day_token(token: str) -> tuple[int, int, str]:
    """拆分 `may15,2021` 这类首 token。"""
    month_key = token[:3]
    if month_key not in MONTHS:
        raise ValueError(f"Unsupported month token: {token}")

    month = MONTHS[month_key]
    remainder = token[3:]
    digits = []
    index = 0
    for char in remainder:
        if char.isdigit():
            digits.append(char)
            index += 1
            continue
        break

    if not digits:
        raise ValueError(f"Missing day number in token: {token}")

    day = int("".join(digits))
    trailing = remainder[index:]
    return month, day, trailing
