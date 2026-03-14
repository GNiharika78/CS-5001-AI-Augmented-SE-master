import sqlite3
from typing import Any


class SQLTool:
    def __init__(self, db_path: str = "data/structured/energy_stats.db") -> None:
        self.db_path = db_path

    def run_query(self, query: str) -> list[tuple[Any, ...]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows