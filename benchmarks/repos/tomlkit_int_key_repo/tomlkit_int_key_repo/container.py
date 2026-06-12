"""从 tomlkit#412 提炼出的最小 int key 容器实现。"""

from __future__ import annotations

import string


class SingleKey:
    """表示最小 TOML 单段 key。"""

    def __init__(self, key: str | int) -> None:
        # 这里故意保留真实 issue 中的缺陷：
        # 当前实现错误假设 key 可逐字符遍历，遇到 int 会直接触发 TypeError。
        if not key or any(
            character not in string.ascii_letters + string.digits + "-" + "_"
            for character in key
        ):
            self.name = str(key)
        else:
            self.name = str(key)

    def render(self) -> str:
        return self.name


class Container:
    """只保留 add/setdefault/item 所需的最小容器。"""

    def __init__(self) -> None:
        self._values: dict[str, int] = {}

    def _normalize_key(self, key: str | int) -> str:
        return SingleKey(key).render()

    def add(self, key: str | int, value: int) -> "Container":
        normalized_key = self._normalize_key(key)
        self._values[normalized_key] = value
        return self

    def setdefault(self, key: str | int, default: int) -> int:
        normalized_key = self._normalize_key(key)
        if normalized_key not in self._values:
            self._values[normalized_key] = default
        return self._values[normalized_key]

    def __getitem__(self, key: str | int) -> int:
        normalized_key = self._normalize_key(key)
        return self._values[normalized_key]
