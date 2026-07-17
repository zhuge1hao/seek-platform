import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.config_backup_service import resolve_runtime_path

_ALLOWED_SCHEMA_COLUMNS = {
    ("documents", "metadata_json", "TEXT"),
    ("chunks", "metadata_json", "TEXT"),
}
_RAG_TABLES = {"documents", "chunks"}


def _use_pgvector() -> bool:
    return os.getenv("RAG_BACKEND", "sqlite").lower() == "pgvector"


def _pgvector():
    from rag.pgvector_provider import PgVectorRagProvider
    return PgVectorRagProvider()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path() -> Path:
    return resolve_runtime_path(os.getenv("RAG_SQLITE_PATH", "apps/api/runtime/rag/rag.sqlite3"))


def _connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if table not in _RAG_TABLES:
        raise ValueError("unsupported RAG table")
    return {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}  # nosec B608: table is validated against _RAG_TABLES.


def _add_column(conn: sqlite3.Connection, table: str, name: str, definition: str) -> None:
    if (table, name, definition) not in _ALLOWED_SCHEMA_COLUMNS:
        raise ValueError("unsupported RAG schema column")
    if name not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")  # nosec B608: table, column, and definition are validated against _ALLOWED_SCHEMA_COLUMNS.


def init_db() -> None:
    if _use_pgvector():
        _pgvector().init_db()
        return
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
              doc_id TEXT PRIMARY KEY,
              user_id TEXT,
              title TEXT,
              source_path TEXT,
              source_type TEXT,
              status TEXT,
              chunk_count INTEGER,
              created_at TEXT,
              updated_at TEXT,
              metadata_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
              chunk_id TEXT PRIMARY KEY,
              doc_id TEXT,
              user_id TEXT,
              chunk_index INTEGER,
              content TEXT,
              embedding_json TEXT,
              metadata_json TEXT,
              created_at TEXT
            )
            """
        )
        for name, definition in {
            "user_id": "TEXT",
            "status": "TEXT",
            "chunk_count": "INTEGER DEFAULT 0",
            "updated_at": "TEXT",
        }.items():
            _add_column(conn, "documents", name, definition)
        _add_column(conn, "chunks", "user_id", "TEXT")


def _loads(value: str | None) -> Any:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    item["metadata"] = _loads(item.get("metadata_json"))
    return item


def create_document(user_id: str, doc_id: str, title: str, source_path: str, source_type: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if _use_pgvector():
        return _pgvector().create_document(user_id, doc_id, title, source_path, source_type, metadata)
    init_db()
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO documents
            (doc_id, user_id, title, source_path, source_type, status, chunk_count, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, user_id, title, source_path, source_type, "pending", 0, now, now, json.dumps(metadata or {}, ensure_ascii=False)),
        )
    return get_document(doc_id, user_id) or {}


def add_document(doc_id: str, title: str, source_path: str = "", source_type: str = "", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return create_document(str((metadata or {}).get("user_id") or ""), doc_id, title, source_path, source_type, metadata)


def update_document_status(user_id: str, doc_id: str, status: str, chunk_count: int | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if _use_pgvector():
        return _pgvector().update_document_status(user_id, doc_id, status, chunk_count, metadata)
    init_db()
    updates = ["status = ?", "updated_at = ?"]
    params: list[Any] = [status, _now()]
    if chunk_count is not None:
        updates.append("chunk_count = ?")
        params.append(chunk_count)
    if metadata is not None:
        current = get_document(doc_id, user_id) or {}
        merged = {**(current.get("metadata") or {}), **metadata}
        updates.append("metadata_json = ?")
        params.append(json.dumps(merged, ensure_ascii=False))
    params.extend([doc_id, user_id])
    with _connect() as conn:
        conn.execute(f"UPDATE documents SET {', '.join(updates)} WHERE doc_id = ? AND user_id = ?", params)  # nosec B608: update columns are fixed service-generated names; values are parameterized.
    return get_document(doc_id, user_id)


def delete_document(user_id: str, doc_id: str) -> dict[str, Any] | None:
    if _use_pgvector():
        return _pgvector().delete_document(user_id, doc_id)
    document = get_document(doc_id, user_id)
    if document is None:
        return None
    delete_chunks_by_doc(user_id, doc_id)
    update_document_status(user_id, doc_id, "deleted", chunk_count=0)
    document["status"] = "deleted"
    document["chunk_count"] = 0
    return document


def list_documents(user_id: str | None = None) -> list[dict[str, Any]]:
    if _use_pgvector():
        return _pgvector().list_documents(user_id)
    init_db()
    query = "SELECT * FROM documents WHERE status != 'deleted'"
    params: list[Any] = []
    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)
    query += " ORDER BY updated_at DESC, created_at DESC"
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [item for row in rows if (item := _row(row))]


def get_document(doc_id: str, user_id: str) -> dict[str, Any] | None:
    if _use_pgvector():
        return _pgvector().get_document(doc_id, user_id)
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM documents WHERE doc_id = ? AND user_id = ? AND status != 'deleted'", (doc_id, user_id)).fetchone()
    return _row(row)


def add_chunk(chunk_id: str, doc_id: str, chunk_index: int, content: str, embedding: list[float], metadata: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    if _use_pgvector():
        return _pgvector().add_chunk(chunk_id, doc_id, chunk_index, content, embedding, metadata, user_id)
    init_db()
    created_at = _now()
    owner = user_id or str((metadata or {}).get("user_id") or "")
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO chunks
            (chunk_id, doc_id, user_id, chunk_index, content, embedding_json, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (chunk_id, doc_id, owner, chunk_index, content, json.dumps(embedding), json.dumps(metadata or {}, ensure_ascii=False), created_at),
        )
    return {"chunk_id": chunk_id, "doc_id": doc_id, "user_id": owner, "chunk_index": chunk_index, "content": content, "created_at": created_at, "metadata": metadata or {}}


def delete_chunks_by_doc(user_id: str, doc_id: str) -> int:
    if _use_pgvector():
        return _pgvector().delete_chunks_by_doc(user_id, doc_id)
    init_db()
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM chunks WHERE doc_id = ? AND user_id = ?", (doc_id, user_id))
        return int(cursor.rowcount or 0)


def list_chunks(user_id: str | None = None) -> list[dict[str, Any]]:
    if _use_pgvector():
        return _pgvector().list_chunks(user_id)
    init_db()
    params: list[Any] = []
    where = "WHERE documents.status IN ('ready', 'completed')"
    if user_id is not None:
        where += " AND chunks.user_id = ?"
        params.append(user_id)
    with _connect() as conn:
        sql = "SELECT chunks.*, documents.title AS title FROM chunks LEFT JOIN documents ON documents.doc_id = chunks.doc_id AND documents.user_id = chunks.user_id " + where + " ORDER BY chunks.created_at DESC"  # nosec B608
        rows = conn.execute(sql, params).fetchall()
    return [item for row in rows if (item := _row(row))]


def get_chunk(chunk_id: str) -> dict[str, Any] | None:
    if _use_pgvector():
        return _pgvector().get_chunk(chunk_id)
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,)).fetchone()
    return _row(row)


def count_chunks(user_id: str | None = None) -> int:
    if _use_pgvector():
        return _pgvector().count_chunks(user_id)
    init_db()
    query = "SELECT COUNT(*) AS count FROM chunks"
    params: list[Any] = []
    if user_id is not None:
        query += " WHERE user_id = ?"
        params.append(user_id)
    with _connect() as conn:
        row = conn.execute(query, params).fetchone()
    return int(row["count"] if row else 0)


def count_documents(user_id: str) -> int:
    if _use_pgvector():
        return _pgvector().count_documents(user_id)
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM documents WHERE user_id = ? AND status != 'deleted'", (user_id,)).fetchone()
    return int(row["count"] if row else 0)


def get_stats(user_id: str) -> dict[str, Any]:
    if _use_pgvector():
        return _pgvector().get_stats(user_id)
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT status, COUNT(*) AS count FROM documents WHERE user_id = ? AND status != 'deleted' GROUP BY status", (user_id,)).fetchall()
    counts = {str(row["status"]): int(row["count"]) for row in rows}
    return {
        "document_count": sum(counts.values()),
        "chunk_count": count_chunks(user_id),
        "ready_count": counts.get("ready", 0) + counts.get("completed", 0),
        "failed_count": counts.get("failed", 0),
        "rag_sqlite_exists": db_path().exists(),
    }
