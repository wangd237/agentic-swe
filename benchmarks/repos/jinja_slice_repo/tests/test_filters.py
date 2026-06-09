"""jinja slice filter 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jinja_slice_repo.filters import slice_items


class SliceTests(unittest.TestCase):
    def test_fill_with_does_not_append_extra_item_when_evenly_divisible(self) -> None:
        result = slice_items([1, 2, 3, 4], 4, fill_with="foo")

        self.assertEqual(result, [[1], [2], [3], [4]])

    def test_fill_with_still_pads_shorter_tail_slices(self) -> None:
        result = slice_items([1, 2, 3], 2, fill_with="foo")

        self.assertEqual(result, [[1, 2], [3, "foo"]])
