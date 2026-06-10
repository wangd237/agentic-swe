"""jsonschema extend 语义回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jsonschema_extend_repo.validators import Draft4Validator, extend


class ExtendValidatorTests(unittest.TestCase):
    def test_legacy_validator_ignores_ref_siblings(self) -> None:
        schema = {"$ref": "#/$defs/limit", "maximum": 5, "type": "number"}

        self.assertEqual(Draft4Validator.applicable_keyword_names(schema), ["$ref"])

    def test_extend_preserves_legacy_ref_filtering(self) -> None:
        schema = {"$ref": "#/$defs/limit", "maximum": 5, "type": "number"}
        extended_validator = extend(Draft4Validator, {"minimum": object()})

        self.assertEqual(extended_validator.applicable_keyword_names(schema), ["$ref"])

    def test_extend_still_handles_non_ref_keywords(self) -> None:
        schema = {"maximum": 5, "type": "number"}
        extended_validator = extend(Draft4Validator, {"minimum": object()})

        self.assertEqual(
            extended_validator.applicable_keyword_names(schema),
            ["maximum", "type"],
        )
