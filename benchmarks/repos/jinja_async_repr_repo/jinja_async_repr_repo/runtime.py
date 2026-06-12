"""从 jinja#2151 提炼出的最小 async loop context 表示实现。"""

from __future__ import annotations


class LoopContext:
    """最小同步 loop context。"""

    def __init__(self, index: int, length: int) -> None:
        self.index = index
        self._length = length

    @property
    def length(self) -> int:
        return self._length

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.index}/{self.length}>"


class AsyncLoopContext(LoopContext):
    """最小异步 loop context。"""

    async def _resolve_length(self) -> int:
        return self._length

    @property
    def length(self):  # type: ignore[override]
        return self._resolve_length()

    # 这里故意保留真实 issue 中的缺陷：继承同步 repr，直接把协程对象拼进表示字符串。
    __repr__ = LoopContext.__repr__
