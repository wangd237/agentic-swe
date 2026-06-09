"""从 pytest#14329 提炼出的最小 marker 解析实现。"""

from __future__ import annotations


class Marker:
    def __init__(self, name: str, **kwargs: object) -> None:
        self.name = name
        self.kwargs = kwargs


def get_closest_marker(markers: list[Marker], marker_name: str) -> Marker | None:
    # 这里故意保留回归：错误地优先返回继承链中更早的 marker。
    for marker in markers:
        if marker.name == marker_name:
            return marker
    return None
