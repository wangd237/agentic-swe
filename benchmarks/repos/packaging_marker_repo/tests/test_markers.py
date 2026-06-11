"""packaging Marker extra=None 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packaging_marker_repo.markers import Marker


class MarkerEvaluateTests(unittest.TestCase):
    def test_matching_extra_returns_true(self) -> None:
        marker = Marker('extra == "opt-feature"')

        self.assertTrue(marker.evaluate({"extra": "opt_feature"}))

    def test_non_matching_extra_returns_false(self) -> None:
        marker = Marker('extra == "opt-feature"')

        self.assertFalse(marker.evaluate({"extra": "other-feature"}))

    def test_none_extra_returns_false_instead_of_raising(self) -> None:
        marker = Marker('extra == "opt-feature"')

        self.assertFalse(marker.evaluate({"extra": None}))
