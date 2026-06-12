"""pydantic fraction validator 回归测试。"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pydantic_fraction_repo.validators import ValidationError, fraction_validator


class FractionValidatorTests(unittest.TestCase):
    def test_zero_denominator_is_mapped_to_validation_error(self) -> None:
        with self.assertRaisesRegex(ValidationError, "valid fraction"):
            fraction_validator("6/0")

    def test_invalid_fraction_text_still_raises_validation_error(self) -> None:
        with self.assertRaisesRegex(ValidationError, "valid fraction"):
            fraction_validator("not-a-fraction")

    def test_valid_fraction_input_still_parses(self) -> None:
        validated = fraction_validator("6/3")

        self.assertEqual(validated, Fraction(2, 1))
