"""从 jsonschema#1328 提炼出的最小 ErrorTree 实现。"""

from __future__ import annotations


class ErrorTree:
    """只保留本次 benchmark 需要的最小树行为。"""

    def __init__(self, errors: dict[int, "ErrorTree"] | None = None) -> None:
        self._children = dict(errors or {})

    def __iter__(self):
        return iter(sorted(self._children))

    def __contains__(self, index: int) -> bool:
        return index in self._children

    def __getitem__(self, index: int) -> "ErrorTree":
        # 这里故意保留真实 issue 中的缺陷：访问不存在的索引时，
        # 仍然通过 setdefault 把空节点写回树里，污染后续可见状态。
        return self._children.setdefault(index, ErrorTree())
