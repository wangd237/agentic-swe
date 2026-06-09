"""tomlkit dotted inline table 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_inline_table_repo.formatter import append_key_to_dotted_inline_table


class InlineTableFormatterTests(unittest.TestCase):
    def test_append_key_preserves_spacing_in_dotted_inline_table(self) -> None:
        source = "a = {b.c = 1}\n"

        result = append_key_to_dotted_inline_table(source, "d", 2)

        self.assertEqual(result, "a = {b.c = 1, d = 2}\n")

    def test_append_key_keeps_assignment_prefix(self) -> None:
        source = "a = {x.y = 3}\n"

        result = append_key_to_dotted_inline_table(source, "z", 4)

        self.assertTrue(result.startswith("a = {"))
