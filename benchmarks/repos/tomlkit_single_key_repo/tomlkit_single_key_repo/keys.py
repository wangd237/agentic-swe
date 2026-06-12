"""从 tomlkit#430 提炼出的最小 key 构造实现。"""

from __future__ import annotations


class SingleKey:
    """表示普通单段 key。"""

    def __init__(self, name: str) -> None:
        self.name = name

    def matches(self, raw_key: str) -> bool:
        """判断当前 key 是否能被普通字符串命中。"""
        return self.name == raw_key

    def render(self) -> str:
        """返回渲染后的 key 文本。"""
        return self.name


class DottedKey:
    """表示 dotted key。"""

    def __init__(self, parts: list[str]) -> None:
        self.parts = parts

    def matches(self, raw_key: str) -> bool:
        """判断当前 key 是否能被普通字符串命中。"""
        return ".".join(self.parts) == raw_key

    def render(self) -> str:
        """返回渲染后的 key 文本。"""
        return ".".join(self.parts)


def build_key(key_spec: str | list[str]) -> SingleKey | DottedKey:
    """按最小规则构造 key。"""
    if isinstance(key_spec, str):
        return SingleKey(key_spec)

    # 这里故意保留真实 issue 中的缺陷：即使只有一个元素，也直接构造成 dotted key。
    return DottedKey(list(key_spec))


def document_contains_key(key_spec: str | list[str], query: str) -> bool:
    """模拟文档里按普通字符串判断 key 是否存在。"""
    built = build_key(key_spec)
    return built.matches(query)
