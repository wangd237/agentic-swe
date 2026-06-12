"""pytest expression scanner 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pytest_expression_repo.expression import compile_expression


class ExpressionScannerTests(unittest.TestCase):
    def test_identifier_with_backslashes_is_allowed_without_string_literal(self) -> None:
        compiled = compile_expression(r"test\nfoo\n")

        self.assertEqual(compiled, r"test\nfoo\n")

    def test_backslash_in_identifier_does_not_break_later_string_literal(self) -> None:
        compiled = compile_expression(r'test\nfoo\n and mark(x="y")')

        self.assertEqual(compiled, r'test\nfoo\n and mark(x="y")')

    def test_backslash_inside_string_literal_is_rejected(self) -> None:
        with self.assertRaisesRegex(SyntaxError, "not supported in marker expression"):
            compile_expression(r"mark(var='\hello')")
