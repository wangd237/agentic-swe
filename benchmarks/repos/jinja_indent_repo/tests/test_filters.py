"""jinja indent filter 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jinja_indent_repo.filters import indent_text


class IndentTests(unittest.TestCase):
    def test_empty_first_line_respects_blank_false(self) -> None:
        result = indent_text("", 4, first=True, blank=False)

        self.assertEqual(result, "")

    def test_non_empty_first_line_still_indents_when_first_true(self) -> None:
        result = indent_text("hello", 4, first=True, blank=False)

        self.assertEqual(result, "    hello")
