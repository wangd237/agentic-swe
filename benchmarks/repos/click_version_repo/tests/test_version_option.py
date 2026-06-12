"""click version option 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from click_version_repo.version_option import render_version_output


class VersionOptionTests(unittest.TestCase):
    def test_explicit_package_name_is_used(self) -> None:
        rendered = render_version_output(
            program_name="main.py",
            package_name="click-sub-commands",
            version="0.1.0",
        )

        self.assertEqual(rendered, "click-sub-commands, version 0.1.0")

    def test_program_name_is_used_as_fallback(self) -> None:
        rendered = render_version_output(
            program_name="main.py",
            package_name=None,
            version="0.1.0",
        )

        self.assertEqual(rendered, "main.py, version 0.1.0")

    def test_version_string_is_preserved(self) -> None:
        rendered = render_version_output(
            program_name="cli.py",
            package_name="demo-package",
            version="1.2.3",
        )

        self.assertTrue(rendered.endswith("version 1.2.3"))
