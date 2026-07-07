from __future__ import annotations

from typing import Any

from services import app_sqlite
from services.agent_blueprint_core_store import BlueprintError, TEST_RUN_STATUSES, _json, _new_id, _now, _row_test_case, _row_test_run, _row_validation


def save_test_case(blueprint_id: str, payload: dict[str, Any], user_id: str, test_case_id: str | None = None) -> dict[str, Any]:
    now = _now()
    actual_id = test_case_id or str(payload.get("test_case_id") or _new_id("bpt"))
    existing = get_test_case(actual_id) if test_case_id else None
    created_at = existing["created_at"] if existing else now
    item = {
        "test_case_id": actual_id,
        "blueprint_id": blueprint_id,
        "version_id": payload.get("version_id"),
        "name": str(payload.get("name") or "Blueprint test").strip(),
        "description": str(payload.get("description") or ""),
        "input": payload.get("input") or payload.get("input_json") or {},
        "expected_status": str(payload.get("expected_status") or "completed"),
        "expected_result_rules": payload.get("expected_result_rules") or payload.get("expected_result_rules_json") or {},
        "expected_artifacts": payload.get("expected_artifacts") or payload.get("expected_artifacts_json") or {},
        "max_duration_seconds": payload.get("max_duration_seconds"),
        "requires_connector": bool(payload.get("requires_connector", False)),
        "is_enabled": bool(payload.get("is_enabled", True)),
        "created_by": existing["created_by"] if existing else user_id,
        "created_at": created_at,
        "updated_at": now,
        "last_run_id": existing.get("last_run_id") if existing else None,
        "last_result": existing.get("last_result") if existing else None,
        "metadata": payload.get("metadata") or (existing.get("metadata") if existing else {}) or {},
    }
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_blueprint_test_cases(test_case_id, blueprint_id, version_id, name, description, input_json,
              expected_status, expected_result_rules_json, expected_artifacts_json, max_duration_seconds, requires_connector,
              is_enabled, created_by, created_at, updated_at, last_run_id, last_result_json, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(test_case_id) DO UPDATE SET version_id=excluded.version_id, name=excluded.name, description=excluded.description,
              input_json=excluded.input_json, expected_status=excluded.expected_status, expected_result_rules_json=excluded.expected_result_rules_json,
              expected_artifacts_json=excluded.expected_artifacts_json, max_duration_seconds=excluded.max_duration_seconds,
              requires_connector=excluded.requires_connector, is_enabled=excluded.is_enabled, updated_at=excluded.updated_at,
              metadata_json=excluded.metadata_json
            """,
            (
                item["test_case_id"], item["blueprint_id"], item["version_id"], item["name"], item["description"],
                _json(item["input"]), item["expected_status"], _json(item["expected_result_rules"]), _json(item["expected_artifacts"]),
                item["max_duration_seconds"], 1 if item["requires_connector"] else 0, 1 if item["is_enabled"] else 0,
                item["created_by"], item["created_at"], item["updated_at"], item["last_run_id"], _json(item["last_result"]),
                _json(item["metadata"]),
            ),
        )
    return get_test_case(actual_id) or item


def list_test_cases(blueprint_id: str) -> list[dict[str, Any]]:
    with app_sqlite.connection() as conn:
        rows = conn.execute("SELECT * FROM agent_blueprint_test_cases WHERE blueprint_id=? ORDER BY created_at", (blueprint_id,)).fetchall()
    return [_row_test_case(row) for row in rows]


def get_test_case(test_case_id: str) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM agent_blueprint_test_cases WHERE test_case_id=?", (test_case_id,)).fetchone()
    return _row_test_case(row) if row else None


def get_test_case_by_run_id(run_id: str) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM agent_blueprint_test_cases WHERE last_run_id=?", (run_id,)).fetchone()
    return _row_test_case(row) if row else None


def set_test_case_run_result(test_case_id: str, run_id: str, result: dict[str, Any]) -> None:
    with app_sqlite.connection() as conn:
        conn.execute(
            "UPDATE agent_blueprint_test_cases SET last_run_id=?, last_result_json=?, updated_at=? WHERE test_case_id=?",
            (run_id, _json(result), _now(), test_case_id),
        )


def create_test_run(blueprint_id: str, version_id: str, test_case_id: str, user_id: str, expected_status: str = "", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    test_run_id = _new_id("bptr")
    now = _now()
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_blueprint_test_runs(test_run_id, blueprint_id, version_id, test_case_id, agent_run_id,
              status, expected_status, started_at, created_by, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (test_run_id, blueprint_id, version_id, test_case_id, None, "pending", expected_status, now, user_id, _json(metadata or {})),
        )
    return get_test_run(test_run_id) or {}


def update_test_run(test_run_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    existing = get_test_run(test_run_id)
    if not existing:
        return None
    item = {**existing, **updates}
    if item["status"] not in TEST_RUN_STATUSES:
        raise BlueprintError("invalid test run status")
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            UPDATE agent_blueprint_test_runs SET agent_run_id=?, status=?, expected_status=?, actual_status=?,
              completed_at=?, duration_ms=?, result_summary_json=?, validation_result_json=?,
              missing_result_fields_json=?, missing_artifacts_json=?, error_message=?, metadata_json=?
            WHERE test_run_id=?
            """,
            (
                item.get("agent_run_id"), item["status"], item.get("expected_status"), item.get("actual_status"),
                item.get("completed_at"), item.get("duration_ms"), _json(item.get("result_summary") or {}),
                _json(item.get("validation_result") or {}), _json(item.get("missing_result_fields") or []),
                _json(item.get("missing_artifacts") or []), item.get("error_message") or "",
                _json(item.get("metadata") or {}), test_run_id,
            ),
        )
    return get_test_run(test_run_id)


def list_test_runs(blueprint_id: str, limit: int = 20, test_case_id: str | None = None, version_id: str | None = None) -> list[dict[str, Any]]:
    clauses = ["blueprint_id=?"]
    params: list[Any] = [blueprint_id]
    if test_case_id:
        clauses.append("test_case_id=?")
        params.append(test_case_id)
    if version_id:
        clauses.append("version_id=?")
        params.append(version_id)
    safe_limit = max(1, min(int(limit or 20), 100))
    with app_sqlite.connection() as conn:
        rows = conn.execute(  # nosec B608: clauses are fixed predicates, values are parameterized.
            f"SELECT * FROM agent_blueprint_test_runs WHERE {' AND '.join(clauses)} ORDER BY started_at DESC LIMIT ?",  # nosec B608
            (*params, safe_limit),
        ).fetchall()
    return [_row_test_run(row) for row in rows]


def get_test_run(test_run_id: str) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM agent_blueprint_test_runs WHERE test_run_id=?", (test_run_id,)).fetchone()
    return _row_test_run(row) if row else None


def get_test_run_by_agent_run_id(agent_run_id: str) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM agent_blueprint_test_runs WHERE agent_run_id=? ORDER BY started_at DESC LIMIT 1", (agent_run_id,)).fetchone()
    return _row_test_run(row) if row else None


def latest_test_run_for_version(blueprint_id: str, version_id: str) -> dict[str, Any] | None:
    items = list_test_runs(blueprint_id, limit=1, version_id=version_id)
    return items[0] if items else None


def create_validation_result(blueprint_id: str, version_id: str, result: dict[str, Any], user_id: str, validator_version: str = "v1") -> dict[str, Any]:
    validation_id = _new_id("bpval")
    now = _now()
    errors = result.get("errors") or []
    warnings = result.get("warnings") or []
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_blueprint_validation_results(validation_id, blueprint_id, version_id, is_valid,
              error_count, warning_count, errors_json, warnings_json, checked_at, checked_by, validator_version, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (validation_id, blueprint_id, version_id, 1 if result.get("valid") else 0, len(errors), len(warnings), _json(errors), _json(warnings), now, user_id, validator_version, _json(result.get("metadata") or {})),
        )
    return get_validation_result(validation_id) or {}


def list_validation_results(blueprint_id: str, limit: int = 50) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit or 50), 200))
    with app_sqlite.connection() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_blueprint_validation_results WHERE blueprint_id=? ORDER BY checked_at DESC LIMIT ?",
            (blueprint_id, safe_limit),
        ).fetchall()
    return [_row_validation(row) for row in rows]


def get_validation_result(validation_id: str) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM agent_blueprint_validation_results WHERE validation_id=?", (validation_id,)).fetchone()
    return _row_validation(row) if row else None


def latest_validation_for_version(blueprint_id: str, version_id: str) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute(
            "SELECT * FROM agent_blueprint_validation_results WHERE blueprint_id=? AND version_id=? ORDER BY checked_at DESC LIMIT 1",
            (blueprint_id, version_id),
        ).fetchone()
    return _row_validation(row) if row else None
