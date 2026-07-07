from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CRITICAL_COLUMNS = {
    "agent_runs": {"run_id", "user_id", "status", "row_version"},
    "datasets": {"dataset_id", "user_id", "status"},
    "dataset_files": {"file_id", "dataset_id", "user_id"},
    "dataset_jobs": {"job_id", "dataset_id", "user_id", "status"},
    "agent_blueprints": {"blueprint_id", "agent_id", "status"},
    "agent_blueprint_versions": {"version_id", "blueprint_id", "version_number"},
    "agent_blueprint_test_cases": {"test_case_id", "blueprint_id"},
    "agent_blueprint_releases": {"release_id", "blueprint_id", "version_id"},
    "agent_blueprint_test_runs": {"test_run_id", "blueprint_id", "version_id", "agent_run_id"},
    "agent_blueprint_validation_results": {"validation_id", "blueprint_id", "version_id"},
}


def _sqlite_schema() -> dict[str, set[str]]:
    from services import app_sqlite

    app_sqlite.init_app_db()
    with app_sqlite.connection() as conn:
        tables = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        return {
            table: {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}  # nosec B608: table names come from sqlite_master.
            for table in tables
        }


def _metadata_schema() -> dict[str, set[str]]:
    from sqlalchemy import MetaData
    from db.models import define_tables

    metadata = MetaData()
    define_tables(metadata)
    return {name: {column.name for column in table.columns} for name, table in metadata.tables.items()}


def verify() -> dict[str, Any]:
    sqlite = _sqlite_schema()
    metadata = _metadata_schema()
    missing_tables = sorted(set(CRITICAL_COLUMNS) - set(sqlite) | set(CRITICAL_COLUMNS) - set(metadata))
    column_mismatches = []
    for table, required in CRITICAL_COLUMNS.items():
        sqlite_missing = sorted(required - sqlite.get(table, set()))
        metadata_missing = sorted(required - metadata.get(table, set()))
        if sqlite_missing or metadata_missing:
            column_mismatches.append(
                {"table": table, "sqlite_missing": sqlite_missing, "metadata_missing": metadata_missing}
            )
    return {
        "status": "passed" if not missing_tables and not column_mismatches else "failed",
        "missing_tables": missing_tables,
        "column_mismatches": column_mismatches,
        "sqlite_table_count": len(sqlite),
        "metadata_table_count": len(metadata),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()
    result = verify()
    if args.json_report:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"])
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
