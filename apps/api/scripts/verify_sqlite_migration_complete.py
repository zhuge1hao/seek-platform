from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = API_ROOT.parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from services import app_sqlite, legacy_json_fallback, user_store  # noqa: E402


REQUIRED_TABLES = {
    "users",
    "audit_logs",
    "qa_conversations",
    "qa_messages",
    "agent_conversations",
    "agent_messages",
    "agent_runs",
    "local_agent_connectors",
    "debug_payloads",
    "files",
    "artifacts",
    "datasets",
    "dataset_files",
    "dataset_jobs",
    "agent_blueprints",
    "agent_blueprint_versions",
    "agent_blueprint_test_cases",
    "agent_blueprint_releases",
    "agent_blueprint_test_runs",
    "agent_blueprint_validation_results",
    "app_kv",
    "schema_migrations",
}

REQUIRED_INDEXES = {
    "idx_agent_runs_user_created",
    "idx_agent_conversations_user_updated",
    "idx_datasets_user_updated",
    "idx_blueprint_versions_blueprint_number",
    "idx_blueprint_test_runs_version_status",
    "idx_blueprint_validations_version_checked",
}

CURRENT_SQLITE_TABLES = {
    "Agent Run": "agent_runs",
    "Conversation": "agent_conversations",
    "Dataset": "datasets",
    "Connector": "local_agent_connectors",
    "Debug Payload": "debug_payloads",
    "Artifact": "artifacts",
}

LEGACY_PROBES = {
    "agent_runs": ("users/*/agent_runs/*.json", "runtime/agent_runs/*.json"),
    "agent_conversations": ("users/*/conversations/*.json", "users/*/agent_conversations/*.json"),
    "qa_conversations": ("users/*/qa_conversations/*.json",),
    "datasets": ("users/*/datasets/datasets.json",),
    "files": ("users/*/files/*.json",),
}


def _runtime_root() -> Path:
    return app_sqlite.db_path().parents[1]


def _object_names(conn: sqlite3.Connection, kind: str) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type=?", (kind,)).fetchall()
    return {str(row["name"]) for row in rows}


def _legacy_counts(root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table, patterns in LEGACY_PROBES.items():
        total = 0
        for pattern in patterns:
            total += sum(1 for path in root.glob(pattern) if path.is_file())
        counts[table] = total
    return counts


def build_report() -> dict[str, Any]:
    app_sqlite.run_migrations()
    user_store.load_users()
    report: dict[str, Any] = {
        "status": "PASS",
        "sqlite_path": str(app_sqlite.db_path()),
        "checks": [],
        "warnings": [],
        "failures": [],
        "legacy_json_fallback_enabled": legacy_json_fallback.enabled(),
    }

    with app_sqlite.connection() as conn:
        tables = _object_names(conn, "table")
        indexes = _object_names(conn, "index")
        missing_tables = sorted(REQUIRED_TABLES - tables)
        missing_indexes = sorted(REQUIRED_INDEXES - indexes)
        table_counts = {table: int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]) for table in sorted(REQUIRED_TABLES & tables)}  # nosec B608: table names are intersected with REQUIRED_TABLES whitelist.

    if missing_tables:
        report["failures"].append({"check": "required_tables", "missing": missing_tables})
    else:
        report["checks"].append({"check": "required_tables", "status": "PASS", "count": len(REQUIRED_TABLES)})

    if missing_indexes:
        report["failures"].append({"check": "required_indexes", "missing": missing_indexes})
    else:
        report["checks"].append({"check": "required_indexes", "status": "PASS", "count": len(REQUIRED_INDEXES)})

    if table_counts.get("users", 0) <= 0:
        report["failures"].append({"check": "users_present", "message": "SQLite users table is empty"})
    else:
        report["checks"].append({"check": "users_present", "status": "PASS", "count": table_counts["users"]})

    for label, table in CURRENT_SQLITE_TABLES.items():
        if table not in tables:
            report["failures"].append({"check": "sqlite_read_path", "surface": label, "table": table, "message": "table missing"})
        else:
            report["checks"].append({"check": "sqlite_read_path", "surface": label, "table": table, "status": "PASS", "rows": table_counts.get(table, 0)})

    legacy_counts = _legacy_counts(_runtime_root())
    report["legacy_json_files"] = legacy_counts
    for table, count in legacy_counts.items():
        if count and table_counts.get(table, 0) == 0:
            report["warnings"].append({"check": "legacy_json_unmigrated", "table": table, "legacy_files": count, "message": "legacy JSON files exist while SQLite table is empty"})

    if legacy_json_fallback.enabled():
        report["warnings"].append({"check": "legacy_json_fallback", "message": "APP_LEGACY_JSON_FALLBACK is enabled; production should keep it false"})

    if report["failures"]:
        report["status"] = "FAIL"
    elif report["warnings"]:
        report["status"] = "WARNING"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify APP SQLite migration completeness without reading legacy JSON contents.")
    parser.add_argument("--json", action="store_true", dest="json_output", help="emit a machine-readable JSON report")
    args = parser.parse_args()
    report = build_report()
    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['status']}: APP SQLite migration check")
        print(f"sqlite_path={report['sqlite_path']}")
        for check in report["checks"]:
            print(f"PASS {check['check']}: {json.dumps(check, ensure_ascii=False)}")
        for warning in report["warnings"]:
            print(f"WARNING {warning['check']}: {json.dumps(warning, ensure_ascii=False)}")
        for failure in report["failures"]:
            print(f"FAIL {failure['check']}: {json.dumps(failure, ensure_ascii=False)}")
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
