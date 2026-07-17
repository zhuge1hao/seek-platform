from __future__ import annotations

import sqlite3
import unittest

from services import app_sqlite_migrations, qa_rag_store


class SqlGuardrailsTest(unittest.TestCase):
    def test_app_sqlite_migration_rejects_unlisted_column(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE safe_table(id TEXT)")

        with self.assertRaises(ValueError):
            app_sqlite_migrations._ensure_column(conn, "safe_table", "unsafe", "TEXT")

    def test_rag_schema_rejects_unlisted_table_and_column(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE documents(doc_id TEXT)")

        with self.assertRaises(ValueError):
            qa_rag_store._columns(conn, "documents; DROP TABLE documents")
        with self.assertRaises(ValueError):
            qa_rag_store._add_column(conn, "documents", "unsafe", "TEXT")


if __name__ == "__main__":
    unittest.main()
