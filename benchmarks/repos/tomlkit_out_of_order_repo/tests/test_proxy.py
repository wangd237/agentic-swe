"""tomlkit out-of-order table 访问回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_out_of_order_repo.proxy import parse_document


VALID_HOOKS_TEXT = """
[hooks]

[[hooks.Stop]]
matcher = ".*"

[[hooks.Stop.hooks]]
type = "command"
command = "one"

[[hooks.Stop]]
matcher = ".*"

[[hooks.Stop.hooks]]
type = "command"
command = "two"

[hooks.state]

[hooks.state.example]
trusted_hash = "sha256:abc"
"""


class OutOfOrderTableProxyAccessTests(unittest.TestCase):
    def test_accessing_valid_hooks_table_keeps_repeated_array_tables(self) -> None:
        doc = parse_document(VALID_HOOKS_TEXT)

        hooks = doc.get("hooks")

        self.assertIsInstance(hooks, dict)
        assert isinstance(hooks, dict)
        stop_entries = hooks["Stop"]
        self.assertEqual(len(stop_entries), 2)
        self.assertEqual(stop_entries[0]["hooks"][0]["command"], "one")
        self.assertEqual(stop_entries[1]["hooks"][0]["command"], "two")
        self.assertEqual(hooks["state"]["example"]["trusted_hash"], "sha256:abc")

    def test_repeated_array_tables_without_sibling_tables_still_work(self) -> None:
        text = """
[hooks]

[[hooks.Stop]]
matcher = ".*"

[[hooks.Stop.hooks]]
type = "command"
command = "one"

[[hooks.Stop]]
matcher = ".*"
"""
        doc = parse_document(text)

        hooks = doc.get("hooks")

        self.assertEqual(len(hooks["Stop"]), 2)
        self.assertEqual(hooks["Stop"][0]["matcher"], ".*")
        self.assertEqual(hooks["Stop"][1]["matcher"], ".*")

    def test_sibling_subtable_without_repeated_arrays_is_unchanged(self) -> None:
        text = """
[hooks]

[hooks.state]

[hooks.state.example]
trusted_hash = "sha256:abc"
"""
        doc = parse_document(text)

        hooks = doc.get("hooks")

        self.assertEqual(hooks, {"state": {"example": {"trusted_hash": "sha256:abc"}}})
