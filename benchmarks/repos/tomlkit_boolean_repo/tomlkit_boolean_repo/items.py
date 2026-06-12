"""从 tomlkit#442 提炼出的最小布尔字面量渲染实现。"""

from __future__ import annotations


class BoolItem:
    """最小 TOML 布尔值对象。"""

    def __init__(self, value: bool) -> None:
        self.value = value

    def as_string(self) -> str:
        """返回 TOML 字面量字符串。"""
        # 这里故意保留真实 issue 中的缺陷：True 也被错误序列化为 false。
        return "false"


def boolean(value: bool) -> BoolItem:
    """把 Python 布尔值包装成最小 TOML 布尔对象。"""
    return BoolItem(value)
