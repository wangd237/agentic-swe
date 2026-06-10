"""sqlite delete 自动提交回归测试。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlite_delete_repo.table import Table


class TableTransactionTests(unittest.TestCase):
    def test_insert_is_visible_to_other_connection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "items.db"
            writer = Table(database_path)
            reader = Table(database_path)
            try:
                writer.insert(1, "active", "alpha")

                self.assertEqual(reader.list_names(), ["alpha"])
            finally:
                reader.close()
                writer.close()

    def test_delete_where_is_visible_to_other_connection_without_manual_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "items.db"
            writer = Table(database_path)
            reader = Table(database_path)
            try:
                writer.insert(1, "obsolete", "stale")
                writer.insert(2, "active", "fresh")

                deleted_count = writer.delete_where("kind = ?", ("obsolete",))

                self.assertEqual(deleted_count, 1)
                self.assertEqual(reader.list_names(), ["fresh"])
            finally:
                reader.close()
                writer.close()

    def test_upsert_keeps_autocommit_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "items.db"
            writer = Table(database_path)
            reader = Table(database_path)
            try:
                writer.insert(1, "active", "before")
                writer.upsert(1, "active", "after")

                self.assertEqual(reader.list_names(), ["after"])
            finally:
                reader.close()
                writer.close()
