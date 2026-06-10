"""sqlite transform 数值列空字符串回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlite_transform_repo.transform import transform_rows


class SqliteTransformTests(unittest.TestCase):
    def test_numeric_empty_strings_become_none(self) -> None:
        rows = [
            {"id": "1", "age": "3", "weight": "2.5"},
            {"id": "2", "age": "", "weight": ""},
        ]

        transformed = transform_rows(
            rows,
            {
                "age": "integer",
                "weight": "float",
            },
        )

        self.assertEqual(
            transformed,
            [
                {"id": "1", "age": 3, "weight": 2.5},
                {"id": "2", "age": None, "weight": None},
            ],
        )

    def test_non_target_text_columns_stay_unchanged(self) -> None:
        rows = [
            {"id": "2", "age": "", "note": ""},
        ]

        transformed = transform_rows(
            rows,
            {
                "age": "integer",
            },
        )

        self.assertEqual(
            transformed,
            [
                {"id": "2", "age": None, "note": ""},
            ],
        )
