"""jsonschema ErrorTree 状态污染回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jsonschema_error_tree_repo.error_tree import ErrorTree


class ErrorTreeStateTests(unittest.TestCase):
    def test_initial_iteration_and_contains_reflect_real_errors(self) -> None:
        tree = ErrorTree({0: ErrorTree()})

        self.assertEqual(list(tree), [0])
        self.assertNotIn(1, tree)

    def test_accessing_missing_index_does_not_mutate_tree(self) -> None:
        tree = ErrorTree({0: ErrorTree()})

        empty_child = tree[1]

        self.assertEqual(list(empty_child), [])
        self.assertEqual(list(tree), [0])
        self.assertNotIn(1, tree)
