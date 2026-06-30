from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from services.config_backup_service import resolve_runtime_path


_LOCK = threading.RLock()
_INIT_DONE = False
_LAST_ERROR = ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path() -> Path:
    path = resolve_runtime_path(os.getenv("APP_SQLITE_PATH", "apps/api/runtime/app/meizhaiseek.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection() -> sqlite3.Connection:
    init_app_db()
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_app_db() -> None:
    global _INIT_DONE, _LAST_ERROR
    if _INIT_DONE:
        return
    with _LOCK:
        if _INIT_DONE:
            return
        try:
            conn = sqlite3.connect(db_path())
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            from services import app_sqlite_migrations
            app_sqlite_migrations.run_migrations(conn)
            conn.close()
            _LAST_ERROR = ""
            _INIT_DONE = True
        except Exception as exc:
            _LAST_ERROR = str(exc)
            raise


def run_migrations() -> None:
    with sqlite3.connect(db_path()) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        from services import app_sqlite_migrations
        app_sqlite_migrations.run_migrations(conn)


def json_dump(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def json_load(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def get_kv(key: str, default: Any = None) -> Any:
    with connection() as conn:
        row = conn.execute("SELECT value_json FROM app_kv WHERE key=?", (key,)).fetchone()
    return json_load(row["value_json"], default) if row else default


def set_kv(key: str, value: Any) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO app_kv(key, value_json, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=excluded.updated_at",
            (key, json_dump(value), _now()),
        )


def table_count(table: str) -> int:
    with connection() as conn:
        return int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])


def health_check() -> dict[str, Any]:
    tables = [
        "users", "audit_logs", "qa_conversations", "qa_messages", "agent_conversations",
        "agent_messages", "agent_runs", "local_agent_connectors", "debug_payloads",
        "files", "artifacts", "datasets", "dataset_files", "dataset_jobs", "app_kv", "schema_migrations",
    ]
    result = {
        "status": "ok",
        "backend": os.getenv("APP_STORAGE_BACKEND", "sqlite"),
        "sqlite_path": str(db_path()),
        "sqlite_exists": db_path().exists(),
        "tables": {},
        "legacy_json": {
            "backup_dir": "",
            "migration_completed": False,
            "migration_at": "",
            "dataset_migration_completed": False,
            "dataset_migration_at": "",
            "dataset_warnings": [],
            "warnings": [],
        },
    }
    try:
        init_app_db()
        result["legacy_json"]["backup_dir"] = get_kv("json_migration_backup_dir", "")
        result["legacy_json"]["migration_completed"] = bool(get_kv("json_migration_completed", False))
        result["legacy_json"]["migration_at"] = get_kv("json_migration_at", "")
        result["legacy_json"]["dataset_migration_completed"] = bool(get_kv("dataset_migration_completed", False))
        result["legacy_json"]["dataset_migration_at"] = get_kv("dataset_migration_at", "")
        result["tables"] = {table: table_count(table) for table in tables}
        legacy_dataset_files = list((db_path().parents[1] / "users").glob("*/datasets/datasets.json"))
        if legacy_dataset_files and result["tables"].get("datasets", 0) == 0:
            warning = "legacy datasets.json exists but SQLite datasets table is empty"
            result["legacy_json"]["dataset_warnings"].append(warning)
            result["legacy_json"]["warnings"].append(warning)
            result["status"] = "warning"
        if _LAST_ERROR:
            result["status"] = "warning"
            result["legacy_json"]["warnings"].append(_LAST_ERROR)
    except Exception as exc:
        result["status"] = "failed"
        result["legacy_json"]["warnings"].append(str(exc))
    return result
