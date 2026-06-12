"""packaging wheel compressed tag order 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packaging_tag_order_repo.utils import InvalidWheelFilename, parse_wheel_filename


class WheelTagOrderTests(unittest.TestCase):
    def test_unsorted_compressed_python_tags_are_rejected(self) -> None:
        with self.assertRaises(InvalidWheelFilename):
            parse_wheel_filename("demo-1.0.0-py3.py2-none-any.whl")

    def test_sorted_compressed_python_tags_are_accepted(self) -> None:
        self.assertEqual(
            parse_wheel_filename("demo-1.0.0-py2.py3-none-any.whl"),
            ("demo", "1.0.0", "py2.py3"),
        )

    def test_single_python_tag_is_accepted(self) -> None:
        self.assertEqual(
            parse_wheel_filename("demo-1.0.0-py3-none-any.whl"),
            ("demo", "1.0.0", "py3"),
        )
