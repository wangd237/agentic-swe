"""tomlkit 代理 repr 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_repr_repo.proxy import OutOfOrderTableProxy


class OutOfOrderTableProxyReprTests(unittest.TestCase):
    def test_repr_keeps_all_children_under_same_parent(self) -> None:
        proxy = OutOfOrderTableProxy(
            [
                ("b.c", "d"),
                ("b.e", "f"),
            ]
        )

        self.assertEqual(proxy.to_nested_dict(), {"b": {"c": "d", "e": "f"}})
        self.assertEqual(repr(proxy), repr({"b": {"c": "d", "e": "f"}}))

    def test_repr_of_single_child_parent_is_unchanged(self) -> None:
        proxy = OutOfOrderTableProxy(
            [
                ("b.e", "f"),
            ]
        )

        self.assertEqual(repr(proxy), repr({"b": {"e": "f"}}))

    def test_repr_of_multiple_top_level_groups_keeps_each_group(self) -> None:
        proxy = OutOfOrderTableProxy(
            [
                ("b.c", "d"),
                ("b.e", "f"),
                ("x.y", "z"),
            ]
        )

        self.assertEqual(
            repr(proxy),
            repr({"b": {"c": "d", "e": "f"}, "x": {"y": "z"}}),
        )
