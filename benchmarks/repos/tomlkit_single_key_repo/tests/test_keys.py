"""tomlkit single-key / dotted-key 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_single_key_repo.keys import DottedKey, SingleKey, build_key, document_contains_key


class SingleKeyNormalizationTests(unittest.TestCase):
    def test_string_key_matches_plain_lookup(self) -> None:
        self.assertTrue(document_contains_key("my_key", "my_key"))
        self.assertIsInstance(build_key("my_key"), SingleKey)

    def test_single_element_list_key_matches_string_lookup(self) -> None:
        self.assertTrue(document_contains_key(["my_key"], "my_key"))
        self.assertIsInstance(build_key(["my_key"]), SingleKey)

    def test_multi_element_list_still_uses_dotted_key(self) -> None:
        built = build_key(["tool", "poetry"])
        self.assertIsInstance(built, DottedKey)
        self.assertEqual(built.render(), "tool.poetry")
        self.assertTrue(document_contains_key(["tool", "poetry"], "tool.poetry"))
