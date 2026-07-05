from __future__ import annotations

from typing import Any

from services import app_sqlite
from services.agent_blueprint_core_store import BlueprintError, RELEASE_ACTIONS, _json, _new_id, _now, _row_release


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
