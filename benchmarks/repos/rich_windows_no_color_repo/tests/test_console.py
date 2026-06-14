"""rich#2457 的最小回归测试。"""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rich_windows_no_color_repo.console import Console, WindowsConsoleFeatures


class RichWindowsNoColorRegressionTests(unittest.TestCase):
    def test_legacy_windows_no_color_should_disable_windows_markup(self) -> None:
        console = Console(
            no_color=True,
            legacy_windows=True,
            features=WindowsConsoleFeatures(vt=False, truecolor=False),
        )

        output = console.render("hello", style="red")

        self.assertEqual(output, "hello")

    def test_legacy_windows_without_no_color_still_keeps_windows_markup(self) -> None:
        console = Console(
            no_color=False,
            legacy_windows=True,
            features=WindowsConsoleFeatures(vt=False, truecolor=False),
        )

        output = console.render("hello", style="red")

        self.assertEqual(output, "<WIN:red>hello</WIN:red>")

    def test_non_windows_no_color_still_strips_ansi_style(self) -> None:
        console = Console(
            no_color=True,
            legacy_windows=False,
            features=WindowsConsoleFeatures(vt=True, truecolor=False),
        )

        output = console.render("hello", style="red")

        self.assertEqual(output, "hello")
