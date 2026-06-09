"""dateutil tzstr 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dateutil_tz_repo.tz import tzstr


class TzStrTests(unittest.TestCase):
    def test_gmt_without_offset_returns_zero_offset(self) -> None:
        zone = tzstr("GMT")

        self.assertEqual(zone.name, "GMT")
        self.assertEqual(zone.offset_minutes, 0)

    def test_utc_without_offset_returns_zero_offset(self) -> None:
        zone = tzstr("UTC")

        self.assertEqual(zone.name, "UTC")
        self.assertEqual(zone.offset_minutes, 0)
