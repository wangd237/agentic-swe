"""pydantic model validator 继承回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pydantic_inheritance_repo.models import ChildModel, ParentModel, ValidationError


class ModelValidatorInheritanceTests(unittest.TestCase):
    def test_parent_model_validator_still_runs_for_parent(self) -> None:
        validated = ParentModel.model_validate(positive=2)

        self.assertEqual(validated.events, ["parent"])

    def test_child_model_runs_parent_and_child_validators(self) -> None:
        validated = ChildModel.model_validate(positive=4)

        self.assertEqual(validated.events, ["parent", "child"])

    def test_child_model_keeps_parent_rejection(self) -> None:
        with self.assertRaisesRegex(ValidationError, "greater than zero"):
            ChildModel.model_validate(positive=-2)

    def test_child_model_keeps_own_validator(self) -> None:
        with self.assertRaisesRegex(ValidationError, "even"):
            ChildModel.model_validate(positive=3)
