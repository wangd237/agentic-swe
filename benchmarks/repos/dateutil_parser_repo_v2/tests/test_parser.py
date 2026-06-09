"""dateutil 9 位时间串回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dateutil_parser_repo_v2.parser import parse_time_string


class ParserTests(unittest.TestCase):
    def test_nine_digit_time_string_parses_as_time(self) -> None:
        parsed = parse_time_string("040506789")

        self.assertEqual(parsed, (4, 5, 6, 789))

    def test_spaced_nine_digit_time_string_parses_as_time(self) -> None:
        parsed = parse_time_string("04 05 06 789")

        self.assertEqual(parsed, (4, 5, 6, 789))
