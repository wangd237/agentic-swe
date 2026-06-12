"""tomlkit int key 容器回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_int_key_repo.container import Container


class ContainerIntegerKeyTests(unittest.TestCase):
    def test_add_accepts_integer_key(self) -> None:
        document = Container()
        document.add(4, 5)

        self.assertEqual(document["4"], 5)
        self.assertEqual(document[4], 5)

    def test_setdefault_accepts_integer_key(self) -> None:
        document = Container()

        value = document.setdefault(4, 5)

        self.assertEqual(value, 5)
        self.assertEqual(document["4"], 5)

    def test_setdefault_reuses_existing_value_for_integer_key(self) -> None:
        document = Container()
        document.add(4, 5)

        value = document.setdefault(4, 9)

        self.assertEqual(value, 5)
        self.assertEqual(document["4"], 5)

    def test_string_key_behavior_is_unchanged(self) -> None:
        document = Container()
        document.add("alpha", 7)

        self.assertEqual(document["alpha"], 7)
