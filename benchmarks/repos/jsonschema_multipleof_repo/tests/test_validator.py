"""jsonschema multipleOf 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jsonschema_multipleof_repo.validator import is_multiple_of


class MultipleOfValidatorTests(unittest.TestCase):
    def test_integer_valued_float_is_treated_like_integer(self) -> None:
        self.assertTrue(is_multiple_of(9007199254740995, 11.0))

    def test_integer_divisor_still_passes(self) -> None:
        self.assertTrue(is_multiple_of(9007199254740995, 11))

    def test_non_multiple_value_still_returns_false(self) -> None:
        self.assertFalse(is_multiple_of(10, 3.0))
