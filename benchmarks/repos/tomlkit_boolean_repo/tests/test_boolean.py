"""tomlkit boolean 字面量回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_boolean_repo.items import boolean


class BooleanRenderTests(unittest.TestCase):
    def test_true_renders_to_true_literal(self) -> None:
        self.assertEqual(boolean(True).as_string(), "true")

    def test_false_renders_to_false_literal(self) -> None:
        self.assertEqual(boolean(False).as_string(), "false")
