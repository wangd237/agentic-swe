"""tomlkit 负整数渲染回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_negative_int_repo.items import dumps_document
from tomlkit_negative_int_repo.items import parse_document


class NegativeIntegerValueTests(unittest.TestCase):
    def test_negative_value_flips_to_positive_without_extra_plus_sign(self) -> None:
        document = parse_document("x=-3")

        document["x"] *= -1

        self.assertEqual(document["x"].value, 3)
        self.assertEqual(dumps_document(document), "x=3")

    def test_second_flip_returns_to_negative_without_double_minus(self) -> None:
        document = parse_document("x=-3")

        document["x"] *= -1
        document["x"] *= -1

        self.assertEqual(document["x"].value, -3)
        self.assertEqual(dumps_document(document), "x=-3")

    def test_other_multiplier_keeps_plain_numeric_rendering(self) -> None:
        document = parse_document("x=-3")

        document["x"] *= 2

        self.assertEqual(document["x"].value, -6)
        self.assertEqual(dumps_document(document), "x=-6")
