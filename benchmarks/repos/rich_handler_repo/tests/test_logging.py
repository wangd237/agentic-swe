"""RichHandler %z 回归测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta

from rich_handler_repo.logging import LogRecord, RichHandler


class RichHandlerTimezoneTests(unittest.TestCase):
    def test_timezone_offset_is_rendered(self) -> None:
        # 这里用固定偏移时区，确保 %z 的输出可预测。
        handler = RichHandler("%Y-%m-%dT%H:%M:%S%z", time_zone=timezone(timedelta(hours=2)))
        created = datetime(2025, 7, 4, 19, 14, 41, tzinfo=timezone(timedelta(hours=2))).timestamp()
        record = LogRecord(created=created, message="info message", levelname="INFO")

        rendered = handler.emit(record)

        self.assertIn("+0200", rendered)
        self.assertTrue(rendered.startswith("2025-07-04T19:14:41+0200"))
