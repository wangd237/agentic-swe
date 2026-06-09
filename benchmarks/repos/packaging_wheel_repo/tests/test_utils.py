"""packaging wheel filename 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packaging_wheel_repo.utils import InvalidWheelFilename, parse_wheel_filename


class WheelFilenameTests(unittest.TestCase):
    def test_non_normalized_version_is_rejected(self) -> None:
        with self.assertRaises(InvalidWheelFilename):
            parse_wheel_filename("demo-01.0.0-py3-none-any.whl")

    def test_normalized_version_is_accepted(self) -> None:
        self.assertEqual(
            parse_wheel_filename("demo-1.0.0-py3-none-any.whl"),
            ("demo", "1.0.0"),
        )
