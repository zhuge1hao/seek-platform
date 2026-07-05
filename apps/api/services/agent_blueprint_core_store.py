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
