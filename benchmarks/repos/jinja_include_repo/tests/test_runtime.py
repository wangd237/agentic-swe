"""jinja include without context 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jinja_include_repo.runtime import render_macro_with_include
from jinja_include_repo.runtime import render_macro_with_include_without_context
from jinja_include_repo.runtime import render_top_level_include_without_context


class MacroIncludeTests(unittest.TestCase):
    def test_include_without_context_inside_macro_renders_template_output(self) -> None:
        rendered = render_macro_with_include_without_context()

        self.assertEqual(rendered, "TEST")

    def test_include_without_context_inside_macro_does_not_render_generator_repr(self) -> None:
        rendered = render_macro_with_include_without_context()

        self.assertNotIn("generator object", rendered)

    def test_include_without_context_still_does_not_see_caller_context(self) -> None:
        rendered = render_top_level_include_without_context()

        self.assertEqual(rendered, "TEST")

    def test_regular_include_inside_macro_still_uses_caller_context(self) -> None:
        rendered = render_macro_with_include()

        self.assertEqual(rendered, "OUTER")
