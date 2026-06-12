"""click confirm ANSI 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from click_confirm_repo.prompts import render_confirm_output, render_echo_output, style_text


class ConfirmOutputTests(unittest.TestCase):
    def test_echo_strips_ansi_when_color_false(self) -> None:
        styled = style_text("Hello World!", fg="green")

        rendered = render_echo_output(styled, color=False)

        self.assertEqual(rendered, "Hello World!\n")

    def test_confirm_strips_ansi_when_color_false(self) -> None:
        styled = style_text("Hello World!", fg="green")

        rendered = render_confirm_output(styled, user_input="Y", color=False)

        self.assertEqual(rendered, "Hello World! [y/N]: Y\n")

    def test_confirm_keeps_ansi_when_color_true(self) -> None:
        styled = style_text("Hello World!", fg="green")

        rendered = render_confirm_output(styled, user_input="Y", color=True)

        self.assertIn("\x1b[32mHello World!\x1b[0m", rendered)
