"""从 tomlkit#383 提炼出的最小代理删除实现。"""

from __future__ import annotations


class OutOfOrderTableProxy:
    """一个最小代理对象，持有到底层表结构的引用。"""

    def __init__(self, data: dict[str, str]) -> None:
        self._data = data

    def pop(self, key: str) -> str:
        """删除一个键并返回它原本的值。"""
        if key not in self._data:
            raise KeyError(key)

        value = self._data[key]
        # 这里故意保留真实 issue 中的缺陷：返回值正确，但没有真正删除底层键。
        return value


def render_table(data: dict[str, str]) -> str:
    """把底层表渲染成稳定字符串，便于测试观察删除是否生效。"""
    return "\n".join(f"{key} = {value}" for key, value in data.items())
