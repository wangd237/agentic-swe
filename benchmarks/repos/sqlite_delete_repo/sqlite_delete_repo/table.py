"""从 sqlite-utils#159 提炼出的最小事务提交实现。"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class Table:
    """只保留本 benchmark 所需的最小表操作封装。"""

    def __init__(self, database_path: Path) -> None:
        self._connection = sqlite3.connect(database_path)
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, kind TEXT, name TEXT)"
        )
        self._connection.commit()

    def insert(self, row_id: int, kind: str, name: str) -> None:
        """插入一条记录，并立即提交。"""
        self._connection.execute(
            "INSERT INTO items(id, kind, name) VALUES (?, ?, ?)",
            (row_id, kind, name),
        )
        self._connection.commit()

    def upsert(self, row_id: int, kind: str, name: str) -> None:
        """更新或插入一条记录，并立即提交。"""
        self._connection.execute(
            "INSERT OR REPLACE INTO items(id, kind, name) VALUES (?, ?, ?)",
            (row_id, kind, name),
        )
        self._connection.commit()

    def delete_where(self, where_clause: str, params: tuple[object, ...]) -> int:
        """删除满足条件的记录，并返回删除行数。"""
        cursor = self._connection.execute(
            f"DELETE FROM items WHERE {where_clause}",
            params,
        )
        # 这里故意保留真实 issue 中的缺陷：删除后没有提交事务。
        return cursor.rowcount

    def list_names(self) -> list[str]:
        """返回当前表中的 name 列。"""
        rows = self._connection.execute(
            "SELECT name FROM items ORDER BY id"
        ).fetchall()
        return [row[0] for row in rows]

    def close(self) -> None:
        """关闭连接。"""
        self._connection.close()
