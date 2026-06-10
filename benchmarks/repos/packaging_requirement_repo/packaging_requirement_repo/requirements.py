"""从 packaging#845 提炼出的最小 Requirement 字符串化实现。"""

from __future__ import annotations

import re


_EXTRA_MARKER_RE = re.compile(r'(extra\s*==\s*")([^"]+)(")')


def _normalize_extra_name(extra_name: str) -> str:
    """把 extra 名称归一化为连字符风格。"""
    return extra_name.replace("_", "-")


def _normalize_extra_markers(expression: str) -> str:
    """规范化 marker 表达式里出现的 extra 名称。"""

    def replace(match: re.Match[str]) -> str:
        prefix, extra_name, suffix = match.groups()
        return f"{prefix}{_normalize_extra_name(extra_name)}{suffix}"

    return _EXTRA_MARKER_RE.sub(replace, expression)


class Requirement:
    """只保留本次 benchmark 需要的最小 Requirement 行为。"""

    def __init__(self, requirement: str) -> None:
        parts = requirement.split(";", 1)
        self.base = parts[0].strip()
        self.marker = parts[1].strip() if len(parts) > 1 else None

    def __str__(self) -> str:
        if self.marker is None:
            return self.base

        # 这里故意保留真实 issue 中的缺陷：只有单独 extra marker 才会被规范化。
        if self.marker.startswith('extra == "'):
            extra_name = self.marker[len('extra == "') : -1]
            normalized = _normalize_extra_name(extra_name)
            return f'{self.base}; extra == "{normalized}"'

        return f"{self.base}; {self.marker}"
