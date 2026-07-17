from __future__ import annotations

import gc
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_rag_init_upgrades_legacy_sqlite_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rag_path = Path(tmp) / "rag.sqlite3"
            conn = sqlite3.connect(rag_path)
            try:
                conn.execute("CREATE TABLE documents(doc_id TEXT PRIMARY KEY, metadata_json TEXT)")
                conn.execute("CREATE TABLE chunks(chunk_id TEXT PRIMARY KEY, metadata_json TEXT)")
                conn.commit()
            finally:
                conn.close()

            with patch.dict("os.environ", {"RAG_BACKEND": "sqlite", "RAG_SQLITE_PATH": str(rag_path)}, clear=False):
                qa_rag_store.init_db()

            conn = sqlite3.connect(rag_path)
            try:
                document_columns = {row[1] for row in conn.execute("PRAGMA table_info(documents)").fetchall()}
                chunk_columns = {row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()}
            finally:
                conn.close()

            self.assertIn("user_id", document_columns)
            self.assertIn("status", document_columns)
            self.assertIn("chunk_count", document_columns)
            self.assertIn("updated_at", document_columns)
            self.assertIn("user_id", chunk_columns)
            gc.collect()


if __name__ == "__main__":
    unittest.main()
