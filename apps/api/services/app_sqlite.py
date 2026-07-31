from __future__ import annotations

import json
import os
import queue
import sqlite3
import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from middleware import metrics as app_metrics
from services.config_backup_service import resolve_runtime_path


_LOCK = threading.RLock()
_INIT_DONE = False
_INIT_KEY = ""
_LAST_ERROR = ""
_PG_POOL: "_PostgresPool | None" = None
_PG_POOL_LOCK = threading.Lock()
_PG_LAST_WAIT_MS = 0.0
_TRANSACTION_TRACE: ContextVar[dict[str, int] | None] = ContextVar("app_db_transaction_trace", default=None)


def is_postgres() -> bool:
    return os.getenv("APP_DB_BACKEND", "sqlite").lower() == "postgres"


def _postgres_url() -> str:
    url = os.getenv("APP_DATABASE_URL", "")
    if not url:
        raise RuntimeError("APP_DATABASE_URL is required when APP_DB_BACKEND=postgres")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def _translate_sql(sql: str) -> str:
    return sql.replace("?", "%s")


class _PostgresCursor:
    def __init__(self, cursor: Any):
        self._cursor = cursor

    @property
    def rowcount(self) -> int:
        return int(self._cursor.rowcount or 0)

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def fetchall(self) -> list[Any]:
        return self._cursor.fetchall()

    def close(self) -> None:
        close = getattr(self._cursor, "close", None)
        if callable(close):
            close()


class _PostgresConnection:
    def __init__(self, conn: Any, pool: "_PostgresPool"):
        self._conn = conn
        self._pool = pool
        self._closed = False

    def execute(self, sql: str, params: Any = ()) -> _PostgresCursor:
        cursor = self._conn.execute(_translate_sql(sql), params)
        return _PostgresCursor(cursor)

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._pool.release(self._conn)


class _ObservedConnection:
    def __init__(self, conn: Any, backend: str):
        self._conn = conn
        self._backend = backend
        self.dirty = False

    def execute(self, sql: str, params: Any = ()) -> Any:
        started = time.perf_counter()
        operation = (sql.lstrip().split(None, 1)[0].lower() if sql.strip() else "other")
        if operation not in {"select", "insert", "update", "delete"}:
            operation = "other"
        if operation != "select":
            self.dirty = True
        try:
            return self._conn.execute(sql, params)
        finally:
            app_metrics.observe_db_execute(self._backend, operation, time.perf_counter() - started)
            trace = _TRANSACTION_TRACE.get()
            if trace is not None:
                trace["executes"] += 1

    def commit(self) -> None:
        started = time.perf_counter()
        failed = False
        try:
            self._conn.commit()
        except Exception:
            failed = True
            raise
        finally:
            app_metrics.observe_db_commit(self._backend, time.perf_counter() - started, failed)
            trace = _TRANSACTION_TRACE.get()
            if trace is not None:
                trace["commits"] += 1

    def rollback(self) -> None:
        started = time.perf_counter()
        try:
            self._conn.rollback()
        finally:
            app_metrics.observe_db_rollback(self._backend, time.perf_counter() - started)
            trace = _TRANSACTION_TRACE.get()
            if trace is not None:
                trace["rollbacks"] += 1

    def close(self) -> None:
        self._conn.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)


class _PostgresPool:
    def __init__(self) -> None:
        self._pool: queue.LifoQueue[Any] = queue.LifoQueue(maxsize=max(1, int(os.getenv("APP_DB_POOL_SIZE", "5"))))
        self._max_total = self._pool.maxsize + max(0, int(os.getenv("APP_DB_MAX_OVERFLOW", "5")))
        self._timeout = max(1.0, float(os.getenv("APP_DB_POOL_TIMEOUT", "10")))
        self._recycle_seconds = max(0, int(os.getenv("APP_DB_POOL_RECYCLE", "1800")))
        self._created = 0
        self._in_use = 0
        self._waiters = 0
        self._timeouts = 0
        self._discarded = 0
        self._reconnects = 0
        self._created_at: dict[int, float] = {}
        self._lock = threading.Lock()

    def stats(self) -> dict[str, int | float]:
        with self._lock:
            overflow = max(0, self._created - self._pool.maxsize)
            return {
                "pool_size": self._pool.maxsize,
                "max_overflow": max(0, self._max_total - self._pool.maxsize),
                "max_total": self._max_total,
                "in_use": self._in_use,
                "idle": self._pool.qsize(),
                "overflow": overflow,
                "waiters": self._waiters,
                "timeout_total": self._timeouts,
                "discarded_total": self._discarded,
                "reconnect_total": self._reconnects,
                "pool_timeout_seconds": self._timeout,
                "pool_recycle_seconds": self._recycle_seconds,
            }

    def _sync_metrics(self) -> None:
        app_metrics.set_db_pool_gauges({key: int(value) for key, value in self.stats().items() if isinstance(value, int)})

    def _new_connection(self) -> Any:
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(_postgres_url(), row_factory=dict_row)
        self._created_at[id(conn)] = time.monotonic()
        return conn

    def _remember(self, conn: Any) -> Any:
        self._created_at.setdefault(id(conn), time.monotonic())
        return conn

    def _forget(self, conn: Any) -> None:
        self._created_at.pop(id(conn), None)

    def _expired_or_closed(self, conn: Any) -> bool:
        if bool(getattr(conn, "closed", False)):
            return True
        if self._recycle_seconds <= 0:
            return False
        return time.monotonic() - self._created_at.get(id(conn), time.monotonic()) >= self._recycle_seconds

    def _discard(self, conn: Any) -> None:
        try:
            conn.close()
        finally:
            self._forget(conn)
            with self._lock:
                self._created = max(0, self._created - 1)
                self._discarded += 1
            app_metrics.inc_db_pool_discarded()
            self._sync_metrics()

    def acquire(self) -> _PostgresConnection:
        global _PG_LAST_WAIT_MS
        started = time.perf_counter()
        counted_waiter = False
        while True:
            try:
                conn = self._pool.get_nowait()
            except queue.Empty:
                with self._lock:
                    if self._created < self._max_total:
                        self._created += 1
                        self._reconnects += 1
                        app_metrics.inc_db_pool_reconnect()
                        try:
                            conn = self._remember(self._new_connection())
                            break
                        except Exception:
                            self._created = max(0, self._created - 1)
                            raise
                    self._waiters += 1
                    counted_waiter = True
                self._sync_metrics()
                try:
                    conn = self._pool.get(timeout=self._timeout)
                except queue.Empty as exc:
                    with self._lock:
                        self._timeouts += 1
                        if counted_waiter:
                            self._waiters = max(0, self._waiters - 1)
                            counted_waiter = False
                    app_metrics.inc_db_pool_timeout()
                    self._sync_metrics()
                    raise RuntimeError("PostgreSQL connection pool exhausted") from exc
                finally:
                    if counted_waiter:
                        with self._lock:
                            self._waiters = max(0, self._waiters - 1)
                        counted_waiter = False
            if self._expired_or_closed(conn):
                self._discard(conn)
                continue
            break
        wait_ms = round((time.perf_counter() - started) * 1000, 3)
        _PG_LAST_WAIT_MS = wait_ms
        app_metrics.observe_db_pool_acquire(wait_ms / 1000)
        with self._lock:
            self._in_use += 1
        self._sync_metrics()
        return _PostgresConnection(conn, self)

    def release(self, conn: Any) -> None:
        try:
            with self._lock:
                self._in_use = max(0, self._in_use - 1)
            if self._expired_or_closed(conn) or self._pool.full():
                self._discard(conn)
            else:
                self._pool.put_nowait(conn)
                self._sync_metrics()
        except Exception:
            self._discard(conn)


def _postgres_pool() -> _PostgresPool:
    global _PG_POOL
    if _PG_POOL is None:
        with _PG_POOL_LOCK:
            if _PG_POOL is None:
                _PG_POOL = _PostgresPool()
    return _PG_POOL


def pool_stats() -> dict[str, int | float]:
    if not is_postgres():
        return {}
    return _postgres_pool().stats()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path() -> Path:
    path = resolve_runtime_path(os.getenv("APP_SQLITE_PATH", "apps/api/runtime/app/meizhaiseek.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _init_key() -> str:
    if is_postgres():
        return f"postgres:{_postgres_url()}"
    return f"sqlite:{db_path()}"


def get_connection() -> Any:
    if is_postgres():
        init_app_db()
        conn = _ObservedConnection(_postgres_pool().acquire(), "postgres")
    else:
        init_app_db()
        raw = sqlite3.connect(db_path())
        raw.row_factory = sqlite3.Row
        raw.execute("PRAGMA foreign_keys=ON")
        conn = _ObservedConnection(raw, "sqlite")
    trace = _TRANSACTION_TRACE.get()
    if trace is not None:
        trace["transactions"] += 1
        trace["acquires"] += 1
    return conn


def start_transaction_trace() -> Any:
    return _TRANSACTION_TRACE.set({"transactions": 0, "acquires": 0, "executes": 0, "commits": 0, "rollbacks": 0})


def transaction_trace_snapshot() -> dict[str, int]:
    return dict(_TRANSACTION_TRACE.get() or {})


def stop_transaction_trace(token: Any) -> None:
    _TRANSACTION_TRACE.reset(token)


@contextmanager
def connection(existing_connection: Any | None = None) -> Iterator[Any]:
    if existing_connection is not None:
        yield existing_connection
        return
    conn = get_connection()
    try:
        yield conn
        if conn.dirty:
            conn.commit()
        else:
            conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_app_db() -> None:
    global _INIT_DONE, _INIT_KEY, _LAST_ERROR
    key = _init_key()
    if _INIT_DONE and _INIT_KEY == key:
        return
    with _LOCK:
        key = _init_key()
        if _INIT_DONE and _INIT_KEY == key:
            return
        _INIT_DONE = False
        if is_postgres():
            try:
                from db.models import TABLE_NAMES

                pg_conn = _PostgresPool().acquire()
                existing = {
                    row["table_name"]
                    for row in pg_conn.execute(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                    ).fetchall()
                }
                missing = [table for table in TABLE_NAMES if table not in existing]
                if missing:
                    raise RuntimeError(f"missing PostgreSQL APP tables: {', '.join(missing)}")
                pg_conn.close()
                _LAST_ERROR = ""
                _INIT_DONE = True
                _INIT_KEY = key
                return
            except Exception as exc:
                _LAST_ERROR = str(exc)
                raise
        try:
            sqlite_conn = sqlite3.connect(db_path())
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_conn.execute("PRAGMA journal_mode=WAL")
            sqlite_conn.execute("PRAGMA foreign_keys=ON")
            from services import app_sqlite_migrations
            app_sqlite_migrations.run_migrations(sqlite_conn)
            sqlite_conn.close()
            _LAST_ERROR = ""
            _INIT_DONE = True
            _INIT_KEY = key
        except Exception as exc:
            _LAST_ERROR = str(exc)
            raise


def run_migrations() -> None:
    if is_postgres():
        init_app_db()
        return
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
    if table not in allowed_table_names():
        raise ValueError(f"table is not allowed: {table}")
    with connection() as conn:
        return int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])  # nosec B608: table is checked against allowed_table_names whitelist above.


def allowed_table_names() -> set[str]:
    try:
        from db.models import TABLE_NAMES
        names = set(TABLE_NAMES)
    except Exception:
        names = set()
    names.update({"alembic_version"})
    return names


def health_check() -> dict[str, Any]:
    if is_postgres():
        tables = [
            "users", "audit_logs", "qa_conversations", "qa_messages", "agent_conversations",
            "agent_messages", "agent_runs", "local_agent_connectors", "debug_payloads",
            "files", "artifacts", "datasets", "dataset_files", "dataset_jobs",
            "agent_blueprints", "agent_blueprint_versions", "agent_blueprint_test_cases", "agent_blueprint_releases",
            "agent_blueprint_test_runs", "agent_blueprint_validation_results",
            "app_kv", "schema_migrations",
        ]
        try:
            init_app_db()
            return {"status": "ok", "backend": "postgres", "tables": {table: table_count(table) for table in tables}}
        except Exception as exc:
            return {"status": "failed", "backend": "postgres", "error": str(exc)}
    tables = [
        "users", "audit_logs", "qa_conversations", "qa_messages", "agent_conversations",
        "agent_messages", "agent_runs", "local_agent_connectors", "debug_payloads",
        "files", "artifacts", "datasets", "dataset_files", "dataset_jobs",
        "agent_blueprints", "agent_blueprint_versions", "agent_blueprint_test_cases", "agent_blueprint_releases",
        "agent_blueprint_test_runs", "agent_blueprint_validation_results",
        "app_kv", "schema_migrations",
    ]
    result: dict[str, Any] = {
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
        legacy_json = result["legacy_json"]
        legacy_json["backup_dir"] = get_kv("json_migration_backup_dir", "")
        legacy_json["migration_completed"] = bool(get_kv("json_migration_completed", False))
        legacy_json["migration_at"] = get_kv("json_migration_at", "")
        legacy_json["dataset_migration_completed"] = bool(get_kv("dataset_migration_completed", False))
        legacy_json["dataset_migration_at"] = get_kv("dataset_migration_at", "")
        result["tables"] = {table: table_count(table) for table in tables}
        legacy_dataset_files = list((db_path().parents[1] / "users").glob("*/datasets/datasets.json"))
        if legacy_dataset_files and result["tables"].get("datasets", 0) == 0:
            warning = "legacy datasets.json exists but SQLite datasets table is empty"
            legacy_json["dataset_warnings"].append(warning)
            legacy_json["warnings"].append(warning)
            result["status"] = "warning"
        if _LAST_ERROR:
            result["status"] = "warning"
            legacy_json["warnings"].append(_LAST_ERROR)
    except Exception as exc:
        result["status"] = "failed"
        result["legacy_json"]["warnings"].append(str(exc))
    return result
