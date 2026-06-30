import os
from pathlib import Path
from typing import Any

from services import app_sqlite
from services.config_backup_service import resolve_runtime_path
from services.config_guard import guard_file_store
from services.user_context import files_dir


class FileStoreError(RuntimeError):
    pass


def _legacy_store_path() -> Path:
    path = resolve_runtime_path(os.getenv("FILE_STORE_PATH", "runtime/files/files.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _store_path(user_id: str | None = None) -> Path:
    return files_dir(user_id) / "files.json" if user_id else _legacy_store_path()


def _row_to_record(row: Any) -> dict[str, Any]:
    metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
    return {
        **metadata,
        "file_id": row["file_id"],
        "user_id": row["user_id"],
        "filename": row["filename"],
        "saved_path": row["storage_path"],
        "file_type": row["content_type"],
        "size": row["size_bytes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _load_records(user_id: str | None = None) -> list[dict[str, Any]]:
    with app_sqlite.connection() as conn:
        if user_id:
            rows = conn.execute("SELECT * FROM files WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM files WHERE user_id='legacy' ORDER BY created_at DESC").fetchall()
    records = [_row_to_record(row) for row in rows]
    if records:
        return records
    path = _store_path(user_id)
    if not path.exists():
        return []
    try:
        records = guard_file_store(path)["items"]
        if user_id and records:
            _write_records(records, user_id)
        return records
    except Exception as exc:
        raise FileStoreError(f"文件记录读取失败：{exc}") from exc


def _write_records(records: list[dict[str, Any]], user_id: str) -> list[dict[str, Any]]:
    with app_sqlite.connection() as conn:
        for record in records:
            owner = record.get("user_id") or user_id
            conn.execute(
                """
                INSERT INTO files(file_id, user_id, filename, storage_path, content_type, size_bytes, source, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_id) DO UPDATE SET user_id=excluded.user_id, filename=excluded.filename, storage_path=excluded.storage_path,
                  content_type=excluded.content_type, size_bytes=excluded.size_bytes, updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
                """,
                (
                    record["file_id"], owner, record.get("filename"), record.get("saved_path") or record.get("storage_path"),
                    record.get("file_type") or record.get("content_type"), record.get("size") or record.get("size_bytes"),
                    record.get("source"), record.get("created_at"), record.get("updated_at") or record.get("created_at"),
                    app_sqlite.json_dump(record),
                ),
            )
    return records


def add_file_record(record: dict[str, Any], user_id: str) -> dict[str, Any]:
    record["user_id"] = user_id
    records = [item for item in _load_records(user_id) if item.get("file_id") != record.get("file_id")]
    records.append(record)
    _write_records(records, user_id)
    return record


def get_file_record(file_id: str, user_id: str | None = None, include_all_users: bool = False, include_legacy: bool = True) -> dict[str, Any] | None:
    if user_id:
        match = next((record for record in _load_records(user_id) if record.get("file_id") == file_id), None)
        if match:
            return match
    if include_all_users:
        with app_sqlite.connection() as conn:
            row = conn.execute("SELECT * FROM files WHERE file_id=? LIMIT 1", (file_id,)).fetchone()
        if row:
            return _row_to_record(row)
    if include_legacy:
        return next((record for record in _load_records(None) if record.get("file_id") == file_id), None)
    return None


def list_file_records(user_id: str | None = None, include_legacy: bool = False, include_all_users: bool = False) -> list[dict[str, Any]]:
    if include_all_users:
        with app_sqlite.connection() as conn:
            rows = conn.execute("SELECT * FROM files ORDER BY created_at DESC").fetchall()
        records = [_row_to_record(row) for row in rows]
    else:
        records = _load_records(user_id) if user_id else []
    if include_legacy:
        records.extend(_load_records(None))
    return records
