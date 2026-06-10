"""click alias command 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from click_alias_repo.cli import AliasedGroup, Command


class ResolveCommandTests(unittest.TestCase):
    def test_existing_command_is_resolved(self) -> None:
        group = AliasedGroup({"workspace": Command("workspace")})

        resolved_name, command, args = group.resolve_command("workspace")

        self.assertEqual(resolved_name, "workspace")
        self.assertIsNotNone(command)
        self.assertEqual(command.name, "workspace")
        self.assertEqual(args, [])

    def test_missing_command_returns_none_tuple_without_crashing(self) -> None:
        group = AliasedGroup({"workspace": Command("workspace")})

        resolved_name, command, args = group.resolve_command("workspaceTYPO")

        self.assertIsNone(resolved_name)
        self.assertIsNone(command)
        self.assertEqual(args, [])

    def test_none_command_name_is_handled_gracefully(self) -> None:
        group = AliasedGroup({"workspace": Command("workspace")})

        resolved_name, command, args = group.resolve_command(None)

        self.assertIsNone(resolved_name)
        self.assertIsNone(command)
        self.assertEqual(args, [])
