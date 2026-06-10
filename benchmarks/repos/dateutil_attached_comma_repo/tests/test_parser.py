"""dateutil attached comma year 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dateutil_attached_comma_repo.parser import parse_attached_comma_date


class AttachedCommaDateTests(unittest.TestCase):
    def test_spaced_comma_still_parses_correct_year(self) -> None:
        self.assertEqual(parse_attached_comma_date("may15 , 2021"), (2021, 5, 15))

    def test_attached_comma_year_is_detected(self) -> None:
        self.assertEqual(parse_attached_comma_date("may15,2021"), (2021, 5, 15))
