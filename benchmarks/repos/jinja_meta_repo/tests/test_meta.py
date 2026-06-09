"""jinja undeclared variable 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jinja_meta_repo.meta import find_undeclared_variables


class MetaTests(unittest.TestCase):
    def test_branch_assigned_variable_is_not_undeclared(self) -> None:
        branch_assigned = {
            "if": ["output"],
            "elif": ["output"],
            "else": ["output"],
        }
        used_variables = ["output"]

        undeclared = find_undeclared_variables(branch_assigned, used_variables)

        self.assertEqual(undeclared, set())

    def test_control_variable_remains_undeclared(self) -> None:
        branch_assigned = {
            "if": ["output"],
            "elif": ["output"],
            "else": ["output"],
        }
        used_variables = ["control"]

        undeclared = find_undeclared_variables(branch_assigned, used_variables)

        self.assertEqual(undeclared, {"control"})
