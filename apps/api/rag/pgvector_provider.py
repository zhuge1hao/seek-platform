import json
import os
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PgVectorRagProvider:
    backend = "pgvector"

    def _url(self) -> str:
        url = os.getenv("RAG_DATABASE_URL") or os.getenv("APP_DATABASE_URL", "")
        if not url:
            raise RuntimeError("RAG_DATABASE_URL or APP_DATABASE_URL is required for pgvector")
        return url.replace("postgresql+asyncpg://", "postgresql://")

    def _connect(self):
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self._url(), row_factory=dict_row)

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rag_documents (
                  doc_id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  title TEXT,
                  source_path TEXT,
                  source_type TEXT,
                  status TEXT,
                  chunk_count INTEGER DEFAULT 0,
                  created_at TEXT,
                  updated_at TEXT,
                  metadata_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rag_chunks (
                  chunk_id TEXT PRIMARY KEY,
                  doc_id TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  chunk_index INTEGER,
                  content TEXT,
                  embedding vector,
                  metadata_json TEXT,
                  created_at TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rag_documents_user_status ON rag_documents(user_id, status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rag_chunks_user_doc ON rag_chunks(user_id, doc_id)")

    def health_check(self) -> dict:
        try:
            self.init_db()
            return {"backend": self.backend, "status": "ok"}
        except Exception as exc:
            return {"backend": self.backend, "status": "failed", "error": str(exc)}

    def create_document(self, user_id: str, doc_id: str, title: str, source_path: str, source_type: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        self.init_db()
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rag_documents(doc_id, user_id, title, source_path, source_type, status, chunk_count, created_at, updated_at, metadata_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(doc_id) DO UPDATE SET user_id=excluded.user_id, title=excluded.title, source_path=excluded.source_path,
                  source_type=excluded.source_type, status=excluded.status, chunk_count=excluded.chunk_count,
                  updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
                """,
                (doc_id, user_id, title, source_path, source_type, "indexing", 0, now, now, json.dumps(metadata or {}, ensure_ascii=False)),
            )
        return self.get_document(doc_id, user_id) or {}

    def update_document_status(self, user_id: str, doc_id: str, status: str, chunk_count: int | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any] | None:
        current = self.get_document(doc_id, user_id) or {}
        merged = {**(current.get("metadata") or {}), **(metadata or {})}
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE rag_documents
                SET status=%s, updated_at=%s, chunk_count=COALESCE(%s, chunk_count), metadata_json=%s
                WHERE doc_id=%s AND user_id=%s
                """,
                (status, _now(), chunk_count, json.dumps(merged, ensure_ascii=False), doc_id, user_id),
            )
        return self.get_document(doc_id, user_id)

    def delete_document(self, user_id: str, doc_id: str) -> dict[str, Any] | None:
        document = self.get_document(doc_id, user_id)
        if document is None:
            return None
        self.delete_chunks_by_doc(user_id, doc_id)
        self.update_document_status(user_id, doc_id, "deleted", 0)
        document["status"] = "deleted"
        document["chunk_count"] = 0
        return document

    def list_documents(self, user_id: str | None = None) -> list[dict[str, Any]]:
        self.init_db()
        params: list[Any] = []
        where = "WHERE status != 'deleted'"
        if user_id is not None:
            where += " AND user_id=%s"
            params.append(user_id)
        with self._connect() as conn:
            rows = conn.execute(f"SELECT * FROM rag_documents {where} ORDER BY updated_at DESC, created_at DESC", params).fetchall()  # nosec B608: where is built from fixed clauses with parameterized values.
        return [self._row(row) for row in rows]

    def get_document(self, doc_id: str, user_id: str) -> dict[str, Any] | None:
        self.init_db()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM rag_documents WHERE doc_id=%s AND user_id=%s AND status != 'deleted'", (doc_id, user_id)).fetchone()
        return self._row(row) if row else None

    def add_chunk(self, chunk_id: str, doc_id: str, chunk_index: int, content: str, embedding: list[float], metadata: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
        self.init_db()
        owner = user_id or str((metadata or {}).get("user_id") or "")
        created_at = _now()
        vector = "[" + ",".join(str(float(value)) for value in embedding) + "]"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rag_chunks(chunk_id, doc_id, user_id, chunk_index, content, embedding, metadata_json, created_at)
                VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s)
                ON CONFLICT(chunk_id) DO UPDATE SET doc_id=excluded.doc_id, user_id=excluded.user_id,
                  chunk_index=excluded.chunk_index, content=excluded.content, embedding=excluded.embedding,
                  metadata_json=excluded.metadata_json
                """,
                (chunk_id, doc_id, owner, chunk_index, content, vector, json.dumps(metadata or {}, ensure_ascii=False), created_at),
            )
        return {"chunk_id": chunk_id, "doc_id": doc_id, "user_id": owner, "chunk_index": chunk_index, "content": content, "created_at": created_at, "metadata": metadata or {}}

    def delete_chunks_by_doc(self, user_id: str, doc_id: str) -> int:
        self.init_db()
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM rag_chunks WHERE doc_id=%s AND user_id=%s", (doc_id, user_id))
            return int(cursor.rowcount or 0)

    def list_chunks(self, user_id: str | None = None) -> list[dict[str, Any]]:
        self.init_db()
        params: list[Any] = []
        where = "WHERE d.status='ready'"
        if user_id is not None:
            where += " AND c.user_id=%s"
            params.append(user_id)
        with self._connect() as conn:
            sql = "SELECT c.chunk_id, c.doc_id, c.user_id, c.chunk_index, c.content, c.embedding::text AS embedding_json, c.metadata_json, c.created_at, d.title FROM rag_chunks c LEFT JOIN rag_documents d ON d.doc_id=c.doc_id AND d.user_id=c.user_id " + where + " ORDER BY c.created_at DESC"  # nosec B608
            rows = conn.execute(sql, params).fetchall()
        return [self._row(row) for row in rows]

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        self.init_db()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT chunk_id, doc_id, user_id, chunk_index, content, embedding::text AS embedding_json, metadata_json, created_at FROM rag_chunks WHERE chunk_id=%s",
                (chunk_id,),
            ).fetchone()
        return self._row(row) if row else None

    def count_chunks(self, user_id: str | None = None) -> int:
        self.init_db()
        params: list[Any] = []
        where = ""
        if user_id is not None:
            where = "WHERE user_id=%s"
            params.append(user_id)
        with self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) AS count FROM rag_chunks {where}", params).fetchone()  # nosec B608: where is selected from fixed clauses with bound values.
        return int(row["count"] if row else 0)

    def count_documents(self, user_id: str) -> int:
        self.init_db()
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM rag_documents WHERE user_id=%s AND status != 'deleted'", (user_id,)).fetchone()
        return int(row["count"] if row else 0)

    def get_stats(self, user_id: str) -> dict[str, Any]:
        self.init_db()
        with self._connect() as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS count FROM rag_documents WHERE user_id=%s AND status != 'deleted' GROUP BY status", (user_id,)).fetchall()
        counts = {str(row["status"]): int(row["count"]) for row in rows}
        return {"document_count": sum(counts.values()), "chunk_count": self.count_chunks(user_id), "ready_count": counts.get("ready", 0), "failed_count": counts.get("failed", 0), "rag_sqlite_exists": False}

    def search(self, user_id: str, embedding: list[float], limit: int = 5) -> list[dict[str, Any]]:
        self.init_db()
        vector = "[" + ",".join(str(float(value)) for value in embedding) + "]"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT c.chunk_id, c.doc_id, c.user_id, c.chunk_index, c.content, c.metadata_json, c.created_at, d.title,
                       1 - (c.embedding <=> %s::vector) AS score
                FROM rag_chunks c
                LEFT JOIN rag_documents d ON d.doc_id=c.doc_id AND d.user_id=c.user_id
                WHERE c.user_id=%s AND d.status='ready'
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                (vector, user_id, vector, limit),
            ).fetchall()
        return [self._row(row) for row in rows]

    def _row(self, row: dict[str, Any]) -> dict[str, Any]:
        item = dict(row)
        metadata = item.get("metadata_json")
        try:
            item["metadata"] = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            item["metadata"] = {}
        return item
