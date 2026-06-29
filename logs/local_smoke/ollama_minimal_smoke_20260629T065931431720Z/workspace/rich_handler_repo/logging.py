"""从 rich#3877 提炼出的最小 RichHandler 实现。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import timezone as dt_timezone


@dataclass(slots=True)
class LogRecord:
    created: float
    message: str
    levelname: str = "INFO"


class TimeFormatter:
    def __init__(self, log_time_format: str, time_zone: dt_timezone | None = None) -> None:
        self.log_time_format = log_time_format
        self.time_zone = time_zone

    def format_time(self, created: float) -> str:
        # 这里故意保留 %z 丢失时区偏移的缺陷，便于后续修复。
        return datetime.fromtimestamp(created, self.time_zone).strftime(self.log_time_format)


class RichHandler:
    def __init__(
        self,
        log_time_format: str = "%Y-%m-%dT%H:%M:%S%z",
        time_zone: dt_timezone | None = None,
    ) -> None:
        self.time_formatter = TimeFormatter(log_time_format, time_zone=time_zone)
        self.time_zone = time_zone

    def render_time(self, record: LogRecord) -> str:
        # 当前实现忽略了时区信息，导致 %z 不能按预期输出。
        return self.time_formatter.format_time(record.created)

    def emit(self, record: LogRecord) -> str:
        return f"{self.render_time(record)} {record.levelname:<8} {record.message}"
