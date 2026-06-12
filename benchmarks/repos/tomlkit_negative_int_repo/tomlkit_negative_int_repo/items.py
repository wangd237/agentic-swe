"""从 tomlkit#346 提炼出的最小负整数渲染实现。"""

from __future__ import annotations


class IntegerValue:
    """模拟 tomlkit 里同时保存数值语义和原始文本表示的整数对象。"""

    def __init__(self, raw: str) -> None:
        self._raw = raw
        self._value = int(raw)

    def __imul__(self, other: int) -> "IntegerValue":
        # 这里故意保留真实 issue 中的缺陷：
        # 原地乘以 -1 时错误复用了已有符号文本，导致渲染结果进入符号循环。
        if other == -1:
            if self._raw.startswith("--"):
                self._raw = self._raw[2:]
            elif self._raw.startswith("-"):
                self._raw = f"+{self._raw[1:]}"
            elif self._raw.startswith("+"):
                self._raw = f"-{self._raw}"
            else:
                self._raw = f"-{self._raw}"
        else:
            self._raw = str(self._value * other)
        self._value *= other
        return self

    def as_string(self) -> str:
        return self._raw

    @property
    def value(self) -> int:
        return self._value


class Document:
    """只保留本题需要的最小键值容器。"""

    def __init__(self, key: str, value: IntegerValue) -> None:
        self._key = key
        self._value = value

    def __getitem__(self, key: str) -> IntegerValue:
        if key != self._key:
            raise KeyError(key)
        return self._value

    def __setitem__(self, key: str, value: IntegerValue) -> None:
        if key != self._key:
            raise KeyError(key)
        self._value = value

    @property
    def key(self) -> str:
        return self._key


def parse_document(source: str) -> Document:
    """解析最小的 `key=value` 整数文档。"""
    key, raw_value = source.split("=", 1)
    return Document(key.strip(), IntegerValue(raw_value.strip()))


def dumps_document(document: Document) -> str:
    """把最小文档重新渲染回文本。"""
    return f"{document.key}={document['x'].as_string()}"
