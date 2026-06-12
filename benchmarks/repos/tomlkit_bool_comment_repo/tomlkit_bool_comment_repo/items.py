"""从 tomlkit#450 提炼出的最小 bool 注释保真实现。"""

from __future__ import annotations


class Item:
    """最小 TOML item，支持值和行尾注释。"""

    def __init__(self, value: object) -> None:
        self.value = value
        self._comment: str | None = None

    def comment(self, text: str) -> "Item":
        """为当前 item 追加最小行尾注释。"""
        self._comment = text
        return self

    def render_line(self, key: str) -> str:
        """渲染最小 key=value 行。"""
        value_text = render_value(self.value)
        if self._comment is None:
            return f"{key} = {value_text}"
        return f"{key} = {value_text} # {self._comment}"


class BoolItem(Item):
    """最小 TOML bool item。"""


def render_value(value: object) -> str:
    """把最小 TOML 值渲染成文本。"""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)


def item(value: object) -> Item:
    """把 Python 值包装成最小 TOML item。"""
    if isinstance(value, bool):
        return BoolItem(value)
    return Item(value)


class Table:
    """只保留 add/get/render 所需的最小 table。"""

    def __init__(self) -> None:
        self._items: dict[str, Item | bool] = {}

    def add(self, key: str, value: object) -> "Table":
        # 这里故意保留真实 issue 中的缺陷：
        # bool 分支被错误保留成原生 bool，导致后续取回后没有 .comment()。
        if isinstance(value, bool):
            self._items[key] = value
            return self
        self._items[key] = item(value)
        return self

    def __getitem__(self, key: str) -> Item | bool:
        return self._items[key]

    def render(self) -> str:
        """渲染最小 table 文本。"""
        lines: list[str] = []
        for key, value in self._items.items():
            if isinstance(value, Item):
                lines.append(value.render_line(key))
            else:
                lines.append(f"{key} = {render_value(value)}")
        return "\n".join(lines) + "\n"
