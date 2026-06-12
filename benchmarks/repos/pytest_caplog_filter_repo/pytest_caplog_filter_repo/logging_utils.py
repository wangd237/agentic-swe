"""从 pytest#14189 提炼出的最小 caplog filtering 实现。"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator


LogFilter = Callable[[str], bool]


class CapturingHandler:
    """最小化的日志处理器，只保留 filter 与捕获记录语义。"""

    def __init__(self) -> None:
        self.filters: list[LogFilter] = []
        self.records: list[str] = []

    def add_filter(self, log_filter: LogFilter) -> None:
        """仿照 logging.Handler.addFilter，按值去重添加 filter。"""
        if log_filter not in self.filters:
            self.filters.append(log_filter)

    def remove_filter(self, log_filter: LogFilter) -> None:
        """仿照 logging.Handler.removeFilter，按值删除 filter。"""
        if log_filter in self.filters:
            self.filters.remove(log_filter)

    def emit(self, message: str) -> None:
        """只有所有 filter 都放行时才记录消息。"""
        if all(log_filter(message) for log_filter in self.filters):
            self.records.append(message)


@contextmanager
def filtering(handler: CapturingHandler, log_filter: LogFilter) -> Iterator[None]:
    """模拟 pytest caplog.filtering 的上下文行为。"""
    handler.add_filter(log_filter)
    try:
        yield
    finally:
        # 这里故意保留真实 issue 中的缺陷：
        # 嵌套使用相同 filter 时，内层退出会把外层仍在使用的 filter 提前移除。
        handler.remove_filter(log_filter)
