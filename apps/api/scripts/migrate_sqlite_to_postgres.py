from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(API_ROOT))

from services import app_sqlite  # noqa: E402


TABLES = [
    "users", "audit_logs", "qa_conversations", "qa_messages", "agent_conversations", "agent_messages",
    "agent_runs", "local_agent_connectors", "debug_payloads", "files", "artifacts", "datasets",
    "dataset_files", "dataset_jobs", "app_kv", "agent_blueprints", "agent_blueprint_versions",
    "agent_blueprint_test_cases", "agent_blueprint_releases", "agent_blueprint_test_runs",
    "agent_blueprint_validation_results", "schema_migrations",
]


def _sqlite_path() -> Path:
    return app_sqlite.db_path()


def _backup_sqlite(path: Path) -> Path:
    backup_dir = API_ROOT / "runtime" / "postgres_migration_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"{path.stem}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{path.suffix}"
    shutil.copy2(path, target)
    return target


def _connect_sqlite() -> sqlite3.Connection:
    app_sqlite.init_app_db()
    conn = sqlite3.connect(_sqlite_path())
    conn.row_factory = sqlite3.Row
    return conn


def _rows(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(f"SELECT * FROM {table}").fetchall()]  # nosec B608: table comes from fixed migration TABLES or explicit operator CLI selection.


async def _connect_postgres():
    try:
        import asyncpg
    except Exception as exc:
        raise RuntimeError("asyncpg is required for --execute/--verify against PostgreSQL") from exc
    url = os.getenv("APP_DATABASE_URL", "")
    if not url:
        raise RuntimeError("APP_DATABASE_URL is required")
    return await asyncpg.connect(url.replace("postgresql+asyncpg://", "postgresql://"))


async def _insert_rows(pg, table: str, rows: list[dict[str, Any]], batch_size: int) -> dict[str, Any]:
    if not rows:
        return {"inserted": 0, "conflicts": 0}
    columns = list(rows[0].keys())
    placeholders = ", ".join(f"${index}" for index in range(1, len(columns) + 1))
    column_sql = ", ".join(columns)
    primary_key = columns[0]
    sql = f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) ON CONFLICT ({primary_key}) DO NOTHING"  # nosec B608: table/columns are introspected from trusted SQLite schema before migration.
    inserted = 0
    for offset in range(0, len(rows), batch_size):
        batch = rows[offset: offset + batch_size]
        for row in batch:
            result = await pg.execute(sql, *[row.get(column) for column in columns])
            if result.endswith("1"):
                inserted += 1
    return {"inserted": inserted, "conflicts": len(rows) - inserted}


async def run(args: argparse.Namespace) -> dict[str, Any]:
    selected = [args.table] if args.table else TABLES
    sqlite_path = _sqlite_path()
    report: dict[str, Any] = {"status": "ok", "sqlite_path": str(sqlite_path), "tables": {}, "backup": "", "errors": []}
    if not sqlite_path.exists():
        return {**report, "status": "failed", "errors": ["SQLite database does not exist"]}
    with _connect_sqlite() as sqlite:
        for table in selected:
            try:
                rows = _rows(sqlite, table)
                report["tables"][table] = {"sqlite_count": len(rows), "postgres_inserted": 0, "conflicts": 0}
            except Exception as exc:
                report["errors"].append(f"{table}: {exc}")
    if args.dry_run and not args.execute:
        report["mode"] = "dry-run"
        report["status"] = "failed" if report["errors"] else "ok"
        return report
    if args.execute:
        report["backup"] = str(_backup_sqlite(sqlite_path))
        pg = await _connect_postgres()
        try:
            with _connect_sqlite() as sqlite:
                for table in selected:
                    rows = _rows(sqlite, table)
                    result = await _insert_rows(pg, table, rows, args.batch_size)
                    report["tables"][table].update({"postgres_inserted": result["inserted"], "conflicts": result["conflicts"]})
        finally:
            await pg.close()
    if args.verify:
        try:
            pg = await _connect_postgres()
            try:
                for table in selected:
                    count = await pg.fetchval(f"SELECT COUNT(*) FROM {table}")  # nosec B608: table comes from fixed migration TABLES or explicit operator CLI selection.
                    expected = report["tables"].get(table, {}).get("sqlite_count")
                    report["tables"].setdefault(table, {})["postgres_count"] = int(count)
                    if expected is not None and int(count) < int(expected):
                        report["errors"].append(f"{table}: postgres_count {count} < sqlite_count {expected}")
            finally:
                await pg.close()
        except Exception as exc:
            report["errors"].append(f"verify: {exc}")
    report["status"] = "failed" if report["errors"] else "ok"
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate APP SQLite data to PostgreSQL without deleting SQLite.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--table", choices=TABLES)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--json-report", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not (args.dry_run or args.execute or args.verify):
        args.dry_run = True
    report = asyncio.run(run(args))
    if args.json_report:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['status']}: sqlite={report['sqlite_path']} tables={len(report['tables'])} errors={len(report['errors'])}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
