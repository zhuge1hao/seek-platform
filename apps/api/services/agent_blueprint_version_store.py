from __future__ import annotations

from typing import Any

from services import app_sqlite
from services.agent_blueprint_core_store import BlueprintError, _json, _new_id, _now, _row_version, get_blueprint, update_blueprint


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
