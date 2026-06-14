"""rich#2411 的最小回归测试。"""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rich_windows_rule_repo.console import Console


class FakeEncodedStream:
    """用显式 encoding 模拟 Windows-like 旧编码输出流。"""

    def __init__(self, encoding: str) -> None:
        self.encoding = encoding
        self.parts: list[str] = []

    def write(self, text: str) -> None:
        text.encode(self.encoding)
        self.parts.append(text)

    def getvalue(self) -> str:
        return "".join(self.parts)


class RichWindowsRuleRegressionTests(unittest.TestCase):
    def test_rule_falls_back_on_cp1252_stream(self) -> None:
        stream = FakeEncodedStream("cp1252")
        console = Console(file=stream)

        console.rule()

        output = stream.getvalue()
        self.assertIn("-", output)
        self.assertNotIn("─", output)

    def test_print_box_drawing_char_falls_back_on_ascii_stream(self) -> None:
        stream = FakeEncodedStream("ascii")
        console = Console(file=stream)

        console.print("─")

        self.assertEqual(stream.getvalue(), "-")

    def test_rule_preserves_unicode_on_utf8_stream(self) -> None:
        stream = FakeEncodedStream("utf-8")
        console = Console(file=stream)

        console.rule()

        output = stream.getvalue()
        self.assertIn("─", output)
        self.assertNotIn("----------", output)
