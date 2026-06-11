"""isort profile 分派回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from isort_profile_repo.formatter import format_tuple


class IsortProfileTests(unittest.TestCase):
    def test_black_profile_uses_vertical_tuple_layout(self) -> None:
        formatted = format_tuple(
            [
                "therearesuperlong",
                "therearesuperlong",
                "therearesuperlong",
            ],
            profile="black",
        )

        self.assertEqual(
            formatted,
            '(\n    "therearesuperlong",\n    "therearesuperlong",\n    "therearesuperlong",\n)',
        )

    def test_default_profile_keeps_compact_tuple_layout(self) -> None:
        formatted = format_tuple(["a", "b"], profile=None)

        self.assertEqual(formatted, '("a", "b")')
