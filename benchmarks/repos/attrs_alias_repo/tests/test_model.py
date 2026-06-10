"""attrs alias 字段变换回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from attrs_alias_repo.model import define, field, fields


class FieldTransformerAliasTests(unittest.TestCase):
    def test_field_transformer_can_read_default_alias(self) -> None:
        seen_aliases: dict[str, str | None] = {}

        def transformer(_cls: type[object], attributes: list[object]) -> list[object]:
            seen_aliases.update({attribute.name: attribute.alias for attribute in attributes})
            return attributes

        @define(field_transformer=transformer)
        class User:
            name = field()
            nickname = field(alias="nick")

        self.assertEqual(User.__name__, "User")
        self.assertEqual(
            seen_aliases,
            {
                "name": "name",
                "nickname": "nick",
            },
        )

    def test_fields_keep_final_aliases_after_build(self) -> None:
        @define()
        class User:
            name = field()
            nickname = field(alias="nick")

        self.assertEqual(
            [(attribute.name, attribute.alias) for attribute in fields(User)],
            [
                ("name", "name"),
                ("nickname", "nick"),
            ],
        )
