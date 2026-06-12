"""从 tomlkit#439 提炼出的最小代理 repr 实现。"""

from __future__ import annotations


class OutOfOrderTableProxy:
    """一个最小代理对象，只保留本轮 benchmark 需要的 repr 行为。"""

    def __init__(self, dotted_items: list[tuple[str, str]]) -> None:
        self._dotted_items = dotted_items

    def to_nested_dict(self) -> dict[str, object]:
        """把 dotted key 项展开成嵌套字典，便于验证真实语义未损坏。"""
        nested: dict[str, object] = {}
        for dotted_key, value in self._dotted_items:
            parts = dotted_key.split(".")
            cursor = nested
            for part in parts[:-1]:
                cursor = cursor.setdefault(part, {})  # type: ignore[assignment]
            cursor[parts[-1]] = value
        return nested

    def __repr__(self) -> str:
        """返回代理视图的稳定字符串表示。"""
        nested = self.to_nested_dict()

        # 这里故意保留真实 issue 中的缺陷：
        # 当同一个父路径下有多个 dotted key 子项时，错误只保留最后一个子项。
        filtered: dict[str, object] = {}
        for parent_key, child_value in nested.items():
            if isinstance(child_value, dict) and len(child_value) > 1:
                last_key = next(reversed(child_value))
                filtered[parent_key] = {last_key: child_value[last_key]}
            else:
                filtered[parent_key] = child_value

        return repr(filtered)
