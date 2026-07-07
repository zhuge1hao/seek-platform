from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _sqlite_rows(table: str) -> list[dict[str, Any]]:
    from services import qa_rag_store

    path = qa_rag_store.db_path()
    if not path.exists():
        return []
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()]  # nosec B608: table is selected by this script from fixed callers.
        except sqlite3.OperationalError:
            return []


def _loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _checkpoint(path: str | None) -> set[str]:
    if not path:
        return set()
    file = Path(path)
    if not file.exists():
        return set()
    return set(_loads(file.read_text(encoding="utf-8"), []))


def _write_checkpoint(path: str | None, done: set[str]) -> None:
    if path:
        Path(path).write_text(json.dumps(sorted(done), ensure_ascii=False), encoding="utf-8")


def _embedding(row: dict[str, Any]) -> list[float]:
    value = _loads(row.get("embedding_json"), [])
    return [float(item) for item in value]


def _model() -> str:
    from services import qa_embedding_service

    return qa_embedding_service.embedding_model_path()


def migrate(args: argparse.Namespace) -> dict[str, Any]:
    documents = _sqlite_rows("documents")
    chunks = _sqlite_rows("chunks")
    orphan_chunks = [row["chunk_id"] for row in chunks if row.get("doc_id") not in {doc.get("doc_id") for doc in documents}]
    dims = sorted({len(_embedding(row)) for row in chunks if row.get("embedding_json")})
    result: dict[str, Any] = {
        "mode": "dry-run" if args.dry_run else "execute" if args.execute else "verify",
        "status": "passed",
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "orphan_chunk_count": len(orphan_chunks),
        "embedding_dimensions": dims,
        "embedding_model": _model(),
    }
    if args.dry_run:
        return result

    from rag.pgvector_provider import PgVectorRagProvider

    provider = PgVectorRagProvider()
    provider.init_db()
    if args.execute:
        done = _checkpoint(args.checkpoint) if args.resume else set()
        migrated_docs = 0
        migrated_chunks = 0
        for doc in documents:
            doc_id = str(doc["doc_id"])
            if f"doc:{doc_id}" in done:
                continue
            provider.create_document(
                str(doc.get("user_id") or ""),
                doc_id,
                str(doc.get("title") or doc_id),
                str(doc.get("source_path") or ""),
                str(doc.get("source_type") or ""),
                _loads(doc.get("metadata_json"), {}),
            )
            provider.update_document_status(str(doc.get("user_id") or ""), doc_id, str(doc.get("status") or "completed"), int(doc.get("chunk_count") or 0))
            done.add(f"doc:{doc_id}")
            migrated_docs += 1
            if migrated_docs % max(1, args.batch_size) == 0:
                _write_checkpoint(args.checkpoint, done)
        for chunk in chunks:
            chunk_id = str(chunk["chunk_id"])
            if f"chunk:{chunk_id}" in done:
                continue
            provider.add_chunk(
                chunk_id,
                str(chunk.get("doc_id") or ""),
                int(chunk.get("chunk_index") or 0),
                str(chunk.get("content") or ""),
                _embedding(chunk),
                _loads(chunk.get("metadata_json"), {}),
                user_id=str(chunk.get("user_id") or ""),
            )
            done.add(f"chunk:{chunk_id}")
            migrated_chunks += 1
            if migrated_chunks % max(1, args.batch_size) == 0:
                _write_checkpoint(args.checkpoint, done)
        _write_checkpoint(args.checkpoint, done)
        result.update({"migrated_documents": migrated_docs, "migrated_chunks": migrated_chunks})

    pg_docs = provider.list_documents(None)
    pg_chunk_count = provider.count_chunks(None)
    result.update({"pgvector_document_count": len(pg_docs), "pgvector_chunk_count": pg_chunk_count})
    if len(pg_docs) < len(documents) or pg_chunk_count < len(chunks) or orphan_chunks:
        result["status"] = "failed"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--checkpoint")
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()
    result = migrate(args)
    if args.json_report:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"])
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
