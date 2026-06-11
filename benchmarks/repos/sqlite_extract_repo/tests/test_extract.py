"""sqlite extract 空值提取回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlite_extract_repo.extract import extract_column


class SqliteExtractTests(unittest.TestCase):
    def test_extract_skips_none_values(self) -> None:
        rows = [
            {"id": 1, "name": "Simon", "type": None},
            {"id": 2, "name": "Natalie", "type": None},
            {"id": 3, "name": "Cleo", "type": "dog"},
        ]

        extracted_rows, dimension_rows = extract_column(rows, "type")

        self.assertEqual(
            extracted_rows,
            [
                {"id": 1, "name": "Simon", "type_id": None},
                {"id": 2, "name": "Natalie", "type_id": None},
                {"id": 3, "name": "Cleo", "type_id": 1},
            ],
        )
        self.assertEqual(dimension_rows, [{"id": 1, "value": "dog"}])

    def test_extract_still_deduplicates_non_null_values(self) -> None:
        rows = [
            {"id": 1, "type": "dog"},
            {"id": 2, "type": "dog"},
            {"id": 3, "type": "cat"},
        ]

        extracted_rows, dimension_rows = extract_column(rows, "type")

        self.assertEqual(
            extracted_rows,
            [
                {"id": 1, "type_id": 1},
                {"id": 2, "type_id": 1},
                {"id": 3, "type_id": 2},
            ],
        )
        self.assertEqual(
            dimension_rows,
            [
                {"id": 1, "value": "dog"},
                {"id": 2, "value": "cat"},
            ],
        )
