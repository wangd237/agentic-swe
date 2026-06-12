"""tomlkit bool item 注释回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_bool_comment_repo.items import BoolItem, Item, Table


class TableBoolCommentTests(unittest.TestCase):
    def test_bool_entry_supports_comment_after_add(self) -> None:
        owner = Table()
        owner.add("abool", True)

        entry = owner["abool"]
        self.assertIsInstance(entry, BoolItem)
        entry.comment("comment on bool")

        self.assertEqual(owner.render(), "abool = true # comment on bool\n")

    def test_non_bool_entries_still_support_comment(self) -> None:
        owner = Table()
        owner.add("bio", "GitHub Cofounder & CEO")
        owner.add("inum", 33)

        bio = owner["bio"]
        inum = owner["inum"]
        self.assertIsInstance(bio, Item)
        self.assertIsInstance(inum, Item)

        bio.comment("comment on string")
        inum.comment("comment on integer")

        self.assertEqual(
            owner.render(),
            'bio = "GitHub Cofounder & CEO" # comment on string\ninum = 33 # comment on integer\n',
        )

    def test_bool_comment_does_not_change_false_rendering(self) -> None:
        owner = Table()
        owner.add("enabled", False)

        entry = owner["enabled"]
        self.assertIsInstance(entry, BoolItem)
        entry.comment("comment on false bool")

        self.assertEqual(owner.render(), "enabled = false # comment on false bool\n")
