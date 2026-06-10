"""dateutil 月年解析回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dateutil_month_year_repo.parser import parse_month_year


class MonthYearParserTests(unittest.TestCase):
    def test_dot_separated_month_year_parses_correctly(self) -> None:
        self.assertEqual(parse_month_year("05.2016"), (2016, 5))

    def test_slash_separated_month_year_still_parses_correctly(self) -> None:
        self.assertEqual(parse_month_year("04/2014"), (2014, 4))

    def test_unsupported_format_still_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            parse_month_year("2016-05")
