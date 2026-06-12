"""tomlkit inline table newline 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_inline_newline_repo.renderer import render_document_after_inline_table_append


class InlineTableNewlineTests(unittest.TestCase):
    def test_dotted_inline_table_without_trailing_newline_gets_split_line(self) -> None:
        result = render_document_after_inline_table_append(
            section="x",
            inline_key="a.b",
            appended_key="c",
            appended_value=3,
            original_has_trailing_newline=False,
        )

        self.assertIn("a.b = {}\nc = 3\n", result)
        self.assertNotIn("a.b = {}c = 3", result)

    def test_existing_trailing_newline_keeps_expected_layout(self) -> None:
        result = render_document_after_inline_table_append(
            section="x",
            inline_key="a.b",
            appended_key="c",
            appended_value=3,
            original_has_trailing_newline=True,
        )

        self.assertIn("a.b = {}\nc = 3\n", result)

    def test_non_dotted_inline_table_is_not_regressed(self) -> None:
        result = render_document_after_inline_table_append(
            section="x",
            inline_key="a",
            appended_key="c",
            appended_value=3,
            original_has_trailing_newline=False,
        )

        self.assertIn("a = {}\nc = 3\n", result)
