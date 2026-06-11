"""从 packaging#638 提炼出的最小 Marker 计算实现。"""

from __future__ import annotations


class Marker:
    """只保留本次 benchmark 需要的最小 marker 行为。"""

    def __init__(self, raw_marker: str) -> None:
        expected_prefix = 'extra == "'
        expected_suffix = '"'
        if not raw_marker.startswith(expected_prefix) or not raw_marker.endswith(expected_suffix):
            raise ValueError(f"Unsupported marker: {raw_marker}")

        self.raw_marker = raw_marker
        self.expected_extra = raw_marker[len(expected_prefix) : -len(expected_suffix)]

    def evaluate(self, environment: dict[str, str | None]) -> bool:
        """根据 environment 里的 extra 值判断当前 marker 是否命中。"""
        raw_value = environment.get("extra")

        # 这里故意保留真实 issue 中的缺陷：当 extra 为 None 时直接调用 lower，
        # 会抛出 AttributeError，而不是像旧版本那样回落为 False。
        normalized_value = raw_value.lower().replace("_", "-")
        normalized_expected = self.expected_extra.lower().replace("_", "-")
        return normalized_value == normalized_expected
