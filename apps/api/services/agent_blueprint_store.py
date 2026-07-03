from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from services import app_sqlite


STATUSES = {"draft", "testing", "published", "disabled", "deprecated"}
RELEASE_ACTIONS = {"publish", "rollback", "disable", "enable", "deprecate"}
TEST_RUN_STATUSES = {"pending", "running", "passed", "failed", "error", "cancelled"}


class BlueprintError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _json(value: Any) -> str:
    return app_sqlite.json_dump(value if value is not None else {})


def _load_json(value: str | None, default: Any) -> Any:
    return app_sqlite.json_load(value, default) if value else default


def _row_blueprint(row: Any) -> dict[str, Any]:
    return {
        "blueprint_id": row["blueprint_id"],
        "agent_id": row["agent_id"],
        "name": row["name"],
        "display_name": row["display_name"],
        "description": row["description"] or "",
        "category": row["category"] or "",
        "icon": row["icon"] or "",
        "status": row["status"],
        "current_version_id": row["current_version_id"],
        "published_version_id": row["published_version_id"],
        "created_by": row["created_by"],
        "updated_by": row["updated_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "metadata": _load_json(row["metadata_json"], {}),
    }


def _row_version(row: Any, include_prompt: bool = True) -> dict[str, Any]:
    item = {
        "version_id": row["version_id"],
        "blueprint_id": row["blueprint_id"],
        "version_number": row["version_number"],
        "version_name": row["version_name"] or "",
        "change_summary": row["change_summary"] or "",
        "input_schema": _load_json(row["input_schema_json"], {}),
        "methodology": _load_json(row["methodology_json"], {}),
        "prompt_config": _load_json(row["prompt_config_json"], {}) if include_prompt else None,
        "execution_config": _load_json(row["execution_config_json"], {}),
        "output_schema": _load_json(row["output_schema_json"], {}),
        "result_ui_config": _load_json(row["result_ui_config_json"], {}),
        "acceptance_rules": _load_json(row["acceptance_rules_json"], {}),
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "is_published": bool(row["is_published"]),
        "parent_version_id": row["parent_version_id"],
        "metadata": _load_json(row["metadata_json"], {}),
    }
    if not include_prompt:
        item.pop("prompt_config", None)
    return item


def _row_test_case(row: Any) -> dict[str, Any]:
    return {
        "test_case_id": row["test_case_id"],
        "blueprint_id": row["blueprint_id"],
        "version_id": row["version_id"],
        "name": row["name"],
        "description": row["description"] or "",
        "input": _load_json(row["input_json"], {}),
        "expected_status": row["expected_status"] or "",
        "expected_result_rules": _load_json(row["expected_result_rules_json"], {}),
        "expected_artifacts": _load_json(row["expected_artifacts_json"], {}),
        "max_duration_seconds": row["max_duration_seconds"],
        "requires_connector": bool(row["requires_connector"]),
        "is_enabled": bool(row["is_enabled"]),
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_run_id": row["last_run_id"],
        "last_result": _load_json(row["last_result_json"], None),
        "metadata": _load_json(row["metadata_json"], {}),
    }


def _row_release(row: Any) -> dict[str, Any]:
    return {
        "release_id": row["release_id"],
        "blueprint_id": row["blueprint_id"],
        "version_id": row["version_id"],
        "action": row["action"],
        "from_version_id": row["from_version_id"],
        "to_version_id": row["to_version_id"],
        "operator_user_id": row["operator_user_id"],
        "note": row["note"] or "",
        "created_at": row["created_at"],
        "metadata": _load_json(row["metadata_json"], {}),
    }


def _row_test_run(row: Any) -> dict[str, Any]:
    return {
        "test_run_id": row["test_run_id"],
        "blueprint_id": row["blueprint_id"],
        "version_id": row["version_id"],
        "test_case_id": row["test_case_id"],
        "agent_run_id": row["agent_run_id"],
        "status": row["status"],
        "expected_status": row["expected_status"],
        "actual_status": row["actual_status"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
        "duration_ms": row["duration_ms"],
        "result_summary": _load_json(row["result_summary_json"], {}),
        "validation_result": _load_json(row["validation_result_json"], {}),
        "missing_result_fields": _load_json(row["missing_result_fields_json"], []),
        "missing_artifacts": _load_json(row["missing_artifacts_json"], []),
        "error_message": row["error_message"] or "",
        "created_by": row["created_by"],
        "metadata": _load_json(row["metadata_json"], {}),
    }


def _row_validation(row: Any) -> dict[str, Any]:
    return {
        "validation_id": row["validation_id"],
        "blueprint_id": row["blueprint_id"],
        "version_id": row["version_id"],
        "is_valid": bool(row["is_valid"]),
        "valid": bool(row["is_valid"]),
        "error_count": row["error_count"],
        "warning_count": row["warning_count"],
        "errors": _load_json(row["errors_json"], []),
        "warnings": _load_json(row["warnings_json"], []),
        "checked_at": row["checked_at"],
        "checked_by": row["checked_by"],
        "validator_version": row["validator_version"] or "",
        "metadata": _load_json(row["metadata_json"], {}),
    }


def list_blueprints(include_unpublished: bool = True) -> list[dict[str, Any]]:
    clause = "" if include_unpublished else "WHERE status='published'"
    with app_sqlite.connection() as conn:
        rows = conn.execute(f"SELECT * FROM agent_blueprints {clause} ORDER BY updated_at DESC").fetchall()
    return [_row_blueprint(row) for row in rows]


def get_blueprint(blueprint_id: str) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM agent_blueprints WHERE blueprint_id=?", (blueprint_id,)).fetchone()
    return _row_blueprint(row) if row else None


def get_blueprint_by_agent(agent_id: str) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM agent_blueprints WHERE agent_id=? ORDER BY updated_at DESC LIMIT 1", (agent_id,)).fetchone()
    return _row_blueprint(row) if row else None


def create_blueprint(payload: dict[str, Any], user_id: str) -> dict[str, Any]:
    now = _now()
    blueprint_id = str(payload.get("blueprint_id") or _new_id("bp"))
    status = str(payload.get("status") or "draft")
    if status not in STATUSES:
        raise BlueprintError("invalid blueprint status")
    item = {
        "blueprint_id": blueprint_id,
        "agent_id": str(payload.get("agent_id") or "").strip() or None,
        "name": str(payload.get("name") or payload.get("display_name") or blueprint_id).strip(),
        "display_name": str(payload.get("display_name") or payload.get("name") or blueprint_id).strip(),
        "description": str(payload.get("description") or ""),
        "category": str(payload.get("category") or ""),
        "icon": str(payload.get("icon") or ""),
        "status": status,
        "current_version_id": payload.get("current_version_id"),
        "published_version_id": payload.get("published_version_id"),
        "created_by": user_id,
        "updated_by": user_id,
        "created_at": now,
        "updated_at": now,
        "metadata": payload.get("metadata") or {},
    }
    with app_sqlite.connection() as conn:
        exists = conn.execute("SELECT 1 FROM agent_blueprints WHERE blueprint_id=?", (blueprint_id,)).fetchone()
        if exists:
            raise BlueprintError("blueprint already exists")
        conn.execute(
            """
            INSERT INTO agent_blueprints(blueprint_id, agent_id, name, display_name, description, category, icon, status,
              current_version_id, published_version_id, created_by, updated_by, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["blueprint_id"], item["agent_id"], item["name"], item["display_name"], item["description"],
                item["category"], item["icon"], item["status"], item["current_version_id"], item["published_version_id"],
                item["created_by"], item["updated_by"], item["created_at"], item["updated_at"], _json(item["metadata"]),
            ),
        )
    return item


def update_blueprint(blueprint_id: str, updates: dict[str, Any], user_id: str) -> dict[str, Any] | None:
    existing = get_blueprint(blueprint_id)
    if not existing:
        return None
    allowed = {"agent_id", "name", "display_name", "description", "category", "icon", "status", "current_version_id", "published_version_id", "metadata"}
    next_item = {**existing, **{key: value for key, value in updates.items() if key in allowed}}
    if next_item["status"] not in STATUSES:
        raise BlueprintError("invalid blueprint status")
    next_item["updated_by"] = user_id
    next_item["updated_at"] = _now()
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            UPDATE agent_blueprints SET agent_id=?, name=?, display_name=?, description=?, category=?, icon=?, status=?,
              current_version_id=?, published_version_id=?, updated_by=?, updated_at=?, metadata_json=?
            WHERE blueprint_id=?
            """,
            (
                next_item.get("agent_id"), next_item["name"], next_item["display_name"], next_item.get("description"),
                next_item.get("category"), next_item.get("icon"), next_item["status"], next_item.get("current_version_id"),
                next_item.get("published_version_id"), user_id, next_item["updated_at"], _json(next_item.get("metadata") or {}),
                blueprint_id,
            ),
        )
    return get_blueprint(blueprint_id)


def delete_blueprint(blueprint_id: str) -> bool:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT published_version_id FROM agent_blueprints WHERE blueprint_id=?", (blueprint_id,)).fetchone()
        if not row or row["published_version_id"]:
            return False
        conn.execute("DELETE FROM agent_blueprint_validation_results WHERE blueprint_id=?", (blueprint_id,))
        conn.execute("DELETE FROM agent_blueprint_test_runs WHERE blueprint_id=?", (blueprint_id,))
        conn.execute("DELETE FROM agent_blueprint_releases WHERE blueprint_id=?", (blueprint_id,))
        conn.execute("DELETE FROM agent_blueprint_test_cases WHERE blueprint_id=?", (blueprint_id,))
        conn.execute("DELETE FROM agent_blueprint_versions WHERE blueprint_id=?", (blueprint_id,))
        conn.execute("DELETE FROM agent_blueprints WHERE blueprint_id=?", (blueprint_id,))
    return True


def next_version_number(blueprint_id: str) -> int:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT COALESCE(MAX(version_number), 0) + 1 AS next_number FROM agent_blueprint_versions WHERE blueprint_id=?", (blueprint_id,)).fetchone()
    return int(row["next_number"])


def create_version(blueprint_id: str, payload: dict[str, Any], user_id: str) -> dict[str, Any]:
    if not get_blueprint(blueprint_id):
        raise BlueprintError("blueprint not found")
    version_id = str(payload.get("version_id") or _new_id("bpv"))
    number = int(payload.get("version_number") or next_version_number(blueprint_id))
    now = _now()
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_blueprint_versions(version_id, blueprint_id, version_number, version_name, change_summary,
              input_schema_json, methodology_json, prompt_config_json, execution_config_json, output_schema_json,
              result_ui_config_json, acceptance_rules_json, created_by, created_at, is_published, parent_version_id, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id, blueprint_id, number, payload.get("version_name") or f"v{number}",
                payload.get("change_summary") or "", _json(payload.get("input_schema") or {}),
                _json(payload.get("methodology") or {}), _json(payload.get("prompt_config") or {}),
                _json(payload.get("execution_config") or {}), _json(payload.get("output_schema") or {}),
                _json(payload.get("result_ui_config") or {}), _json(payload.get("acceptance_rules") or {}),
                user_id, now, 1 if payload.get("is_published") else 0, payload.get("parent_version_id"), _json(payload.get("metadata") or {}),
            ),
        )
    update_blueprint(blueprint_id, {"current_version_id": version_id}, user_id)
    return get_version(version_id) or {}


def list_versions(blueprint_id: str, include_prompt: bool = True) -> list[dict[str, Any]]:
    with app_sqlite.connection() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_blueprint_versions WHERE blueprint_id=? ORDER BY version_number DESC",
            (blueprint_id,),
        ).fetchall()
    return [_row_version(row, include_prompt=include_prompt) for row in rows]


def get_version(version_id: str, include_prompt: bool = True) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM agent_blueprint_versions WHERE version_id=?", (version_id,)).fetchone()
    return _row_version(row, include_prompt=include_prompt) if row else None


def get_version_for_blueprint(blueprint_id: str, version_id: str, include_prompt: bool = True) -> dict[str, Any] | None:
    version = get_version(version_id, include_prompt=include_prompt)
    return version if version and version["blueprint_id"] == blueprint_id else None


def mark_version_published(blueprint_id: str, version_id: str) -> None:
    with app_sqlite.connection() as conn:
        conn.execute("UPDATE agent_blueprint_versions SET is_published=1 WHERE blueprint_id=? AND version_id=?", (blueprint_id, version_id))


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
        rows = conn.execute(
            f"SELECT * FROM agent_blueprint_test_runs WHERE {' AND '.join(clauses)} ORDER BY started_at DESC LIMIT ?",
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


def create_release(blueprint_id: str, version_id: str, action: str, user_id: str, note: str = "", from_version_id: str | None = None, to_version_id: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if action not in RELEASE_ACTIONS:
        raise BlueprintError("invalid release action")
    release_id = _new_id("bpr")
    now = _now()
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_blueprint_releases(release_id, blueprint_id, version_id, action, from_version_id, to_version_id,
              operator_user_id, note, created_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (release_id, blueprint_id, version_id, action, from_version_id, to_version_id, user_id, note, now, _json(metadata or {})),
        )
    return get_release(release_id) or {}


def get_release(release_id: str) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM agent_blueprint_releases WHERE release_id=?", (release_id,)).fetchone()
    return _row_release(row) if row else None


def list_releases(blueprint_id: str) -> list[dict[str, Any]]:
    with app_sqlite.connection() as conn:
        rows = conn.execute("SELECT * FROM agent_blueprint_releases WHERE blueprint_id=? ORDER BY created_at DESC", (blueprint_id,)).fetchall()
    return [_row_release(row) for row in rows]
