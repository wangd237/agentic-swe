"""jsonschema extras_msg 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jsonschema_extras_repo.utils import extras_msg


class ExtrasMessageTests(unittest.TestCase):
    def test_mixed_type_extras_do_not_raise_type_error(self) -> None:
        message = extras_msg([True, "two"])

        self.assertEqual(message, "[True, 'two']")

    def test_same_type_extras_keep_stable_output(self) -> None:
        message = extras_msg(["b", "a"])

        self.assertEqual(message, "['a', 'b']")

    def test_empty_extras_render_as_empty_list(self) -> None:
        self.assertEqual(extras_msg([]), "[]")
