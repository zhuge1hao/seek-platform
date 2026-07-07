import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services import app_sqlite
from services.config_backup_service import resolve_runtime_path
from services.user_context import debug_payload_dir


_RUN_OWNERS: dict[str, str] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _debug_root() -> Path:
    path = resolve_runtime_path(os.getenv("DEBUG_PAYLOAD_DIR", "runtime/debug_payloads"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _run_dir(run_id: str, user_id: str | None = None) -> Path:
    user_id = user_id or _RUN_OWNERS.get(run_id)
    if not user_id:
        users_root = Path(__file__).resolve().parents[1] / "runtime" / "users"
        existing = next((path for path in users_root.glob(f"*/debug_payloads/{run_id}") if path.is_dir()), None) if users_root.exists() else None
        if existing:
            return existing
    return debug_payload_dir(user_id, run_id) if user_id else _debug_root() / run_id


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in ("api_key", "apikey", "token", "secret", "password")):
                result[key] = "***REDACTED***"
            else:
                result[key] = _redact(item)
        return result
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _row_to_payload(row: Any) -> dict[str, Any]:
    metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
    error = metadata.get("error")
    return {
        "run_id": row["payload_id"],
        "request_exists": bool(row["request_json"]),
        "response_exists": bool(row["response_json"]),
        "error_exists": bool(error),
        "request": app_sqlite.json_load(row["request_json"], None),
        "response": app_sqlite.json_load(row["response_json"], None),
        "error": error,
        "metadata": metadata,
    }


def _upsert(run_id: str, user_id: str | None, request: Any = None, response: Any = None, metadata: dict[str, Any] | None = None, status: str = "running") -> None:
    existing = read_debug_payload(run_id) if run_id else None
    merged_meta = {**((existing or {}).get("metadata") or {}), **_redact(metadata or {})}
    merged_meta.setdefault("created_at", _now())
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            INSERT INTO debug_payloads(payload_id, user_id, connector_id, agent_id, request_json, response_json, status, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(payload_id) DO UPDATE SET user_id=excluded.user_id, connector_id=excluded.connector_id, agent_id=excluded.agent_id,
              request_json=COALESCE(excluded.request_json, debug_payloads.request_json),
              response_json=COALESCE(excluded.response_json, debug_payloads.response_json),
              status=excluded.status, updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
            """,
            (
                run_id, user_id or merged_meta.get("user_id"), merged_meta.get("connector_id"), merged_meta.get("agent_type"),
                app_sqlite.json_dump(_redact(request)) if request is not None else None,
                app_sqlite.json_dump(_redact(response)) if response is not None else None,
                status, merged_meta.get("created_at"), _now(), app_sqlite.json_dump(merged_meta),
            ),
        )


def save_request(run_id: str | None, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> None:
    if not run_id:
        return
    user_id = str(payload.get("user_id") or (metadata or {}).get("user_id") or "").strip() or None
    if user_id:
        _RUN_OWNERS[run_id] = user_id
    _upsert(run_id, user_id, request=payload, metadata={**(metadata or {}), "user_id": user_id}, status="running")


def save_response(run_id: str | None, response: Any, metadata: dict[str, Any] | None = None) -> None:
    if not run_id:
        return
    _upsert(run_id, _RUN_OWNERS.get(run_id), response=response, metadata=metadata, status="success")


def save_error(run_id: str | None, error: str) -> None:
    if not run_id:
        return
    _upsert(run_id, _RUN_OWNERS.get(run_id), metadata={"error": error}, status="failed")


def _legacy_debug_payload(run_id: str) -> dict[str, Any]:
    directory = _run_dir(run_id)
    request_path = directory / "request.json"
    response_path = directory / "response.json"
    error_path = directory / "error.txt"
    metadata_path = directory / "metadata.json"

    def read_json(path: Path) -> Any:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    return {
        "run_id": run_id,
        "request_exists": request_path.exists(),
        "response_exists": response_path.exists(),
        "error_exists": error_path.exists(),
        "request": read_json(request_path),
        "response": read_json(response_path),
        "error": error_path.read_text(encoding="utf-8") if error_path.exists() else None,
        "metadata": read_json(metadata_path),
    }


def read_debug_payload(run_id: str) -> dict[str, Any]:
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM debug_payloads WHERE payload_id=?", (run_id,)).fetchone()
    return _row_to_payload(row) if row else _legacy_debug_payload(run_id)


def list_debug_payloads(limit: int = 50, agent_type: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("status=?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with app_sqlite.connection() as conn:
        rows = conn.execute(f"SELECT * FROM debug_payloads {where} ORDER BY created_at DESC LIMIT ?", (*params, max(1, min(limit, 200)))).fetchall()  # nosec B608: where is built from fixed predicates; values are parameterized.
    items: list[dict[str, Any]] = []
    for row in rows:
        metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
        item = {
            "run_id": row["payload_id"],
            "agent_type": metadata.get("agent_type") or row["agent_id"],
            "connector_id": row["connector_id"],
            "mode": metadata.get("mode"),
            "status": row["status"] or "unknown",
            "has_request": bool(row["request_json"]),
            "has_response": bool(row["response_json"]),
            "has_error": bool(metadata.get("error")),
            "created_at": row["created_at"],
        }
        if agent_type and item["agent_type"] != agent_type:
            continue
        items.append(item)
    return items
