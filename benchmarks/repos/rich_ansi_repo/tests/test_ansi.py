"""rich ANSI CRLF 回归测试。"""

from __future__ import annotations

import unittest

from rich_ansi_repo.ansi import Text


class AnsiDecodeTests(unittest.TestCase):
    def test_empty_string_is_preserved(self) -> None:
        self.assertEqual(Text.from_ansi("").plain, "")

    def test_lf_line_endings_are_preserved(self) -> None:
        self.assertEqual(Text.from_ansi("Hello\nWorld\n").plain, "Hello\nWorld\n")

    def test_crlf_line_endings_are_preserved(self) -> None:
        # 这里接受统一归一化到 LF，只要不要退化成空白行即可。
        self.assertEqual(Text.from_ansi("Hello\r\nWorld\r\n").plain, "Hello\nWorld\n")
