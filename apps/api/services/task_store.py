import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from schemas.agent_runs import AgentRunCreate
from services import app_sqlite, legacy_json_fallback, service_events
from services.config_guard import guard_agent_run_file
from services.user_context import agent_runs_dir


API_ROOT = Path(__file__).resolve().parents[1]
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}
LOGGER = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _legacy_store_dir() -> Path:
    path = API_ROOT / "runtime" / "agent_runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _new_run_id() -> str:
    return f"run_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _base_run(payload: dict[str, Any], logs: list[str] | None = None) -> dict[str, Any]:
    now = _now()
    return {
        "run_id": _new_run_id(),
        "user_id": payload.get("user_id") or "admin",
        "username": payload.get("username") or payload.get("user_id") or "admin",
        "role": payload.get("role") or "admin",
        "agent_type": payload["agent_type"],
        "mode": payload.get("mode") or "default",
        "status": "running",
        "progress": 10,
        "current_step": "任务已创建",
        "prompt": payload["prompt"],
        "selected_skill_ids": payload.get("selected_skill_ids") or [],
        "link": payload.get("link"),
        "file_ids": payload.get("file_ids") or [],
        "dataset_ids": payload.get("dataset_ids") or [],
        "image_paths": payload.get("image_paths") or [],
        "video_path": payload.get("video_path"),
        "video_url": payload.get("video_url"),
        "session_id": payload.get("session_id"),
        "workflow_options": payload.get("workflow_options") or {},
        "conversation_id": payload.get("conversation_id"),
        "output_dir": payload.get("output_dir"),
        "logs": logs or ["任务已创建"],
        "result": None,
        "error": None,
        "row_version": 1,
        "created_at": now,
        "updated_at": now,
    }


def _row_to_run(row: Any) -> dict[str, Any]:
    metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
    run = {
        **metadata,
        "run_id": row["run_id"],
        "user_id": row["user_id"],
        "conversation_id": row["conversation_id"],
        "agent_type": row["agent_type"],
        "status": row["status"],
        "mode": row["mode"],
        "result": app_sqlite.json_load(row["result_json"], None),
        "error": row["error"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "row_version": int((row["row_version"] if "row_version" in row.keys() else metadata.get("row_version")) or 1),
    }
    run.setdefault("workflow_options", app_sqlite.json_load(row["workflow_options_json"], {}) or {})
    run.setdefault("logs", [])
    run.setdefault("progress", 0)
    run.setdefault("current_step", "")
    return run


def _short_text(value: Any, limit: int = 1200) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text[:limit] + ("..." if len(text) > limit else "")


def _limited_list(value: Any, limit: int) -> list[Any]:
    return value[:limit] if isinstance(value, list) else []


def summarize_run(run: dict[str, Any] | None) -> dict[str, Any] | None:
    if run is None:
        return None
    raw_result = run.get("result")
    result: dict[str, Any] = raw_result if isinstance(raw_result, dict) else {}
    files = _limited_list(result.get("files"), 30)
    steps = _limited_list(result.get("steps") or run.get("steps"), 20)
    has_more = False
    if isinstance(result, dict):
        has_more = any(result.get(key) for key in ("raw_response", "timeline", "subtitles", "selling_points", "proof_frames"))
        has_more = has_more or len(json.dumps(result, ensure_ascii=False)) > 8000
    preview = None if not result else {
        "answer": _short_text(result.get("answer", ""), 2000) if result.get("answer") else "",
        "summary": result.get("summary") or {},
        "files": files,
        "quality_warnings": _limited_list(result.get("quality_warnings"), 20),
        "skill_suggestions": _limited_list(result.get("skill_suggestions"), 20),
        "steps": steps,
    }
    return {
        "run_id": run.get("run_id"),
        "user_id": run.get("user_id"),
        "conversation_id": run.get("conversation_id"),
        "agent_type": run.get("agent_type"),
        "mode": run.get("mode"),
        "status": run.get("status"),
        "progress": run.get("progress", 0),
        "current_step": run.get("current_step") or "",
        "logs": _limited_list(run.get("logs"), 5),
        "steps": steps,
        "result": preview,
        "result_preview": preview,
        "result_has_more": has_more,
        "error": run.get("error"),
        "artifact_count": len(result.get("files") or []) if isinstance(result.get("files"), list) else 0,
        "step_count": len(result.get("steps") or run.get("steps") or []) if isinstance(result.get("steps") or run.get("steps"), list) else 0,
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
    }


def _write_run(run: dict[str, Any]) -> dict[str, Any]:
    artifacts = (run.get("result") or {}).get("files") if isinstance(run.get("result"), dict) else []
    run["row_version"] = int(run.get("row_version") or 1)
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_runs(run_id, user_id, conversation_id, agent_id, agent_type, status, mode, input_json, workflow_options_json, result_json, error, artifacts_json, created_at, updated_at, started_at, completed_at, metadata_json, row_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET user_id=excluded.user_id, conversation_id=excluded.conversation_id, agent_type=excluded.agent_type,
              status=excluded.status, mode=excluded.mode, input_json=excluded.input_json, workflow_options_json=excluded.workflow_options_json,
              result_json=excluded.result_json, error=excluded.error, artifacts_json=excluded.artifacts_json, updated_at=excluded.updated_at,
              completed_at=excluded.completed_at, metadata_json=excluded.metadata_json, row_version=excluded.row_version
            """,
            (
                run["run_id"], run.get("user_id") or "admin", run.get("conversation_id"), run.get("agent_id"),
                run.get("agent_type"), run.get("status"), run.get("mode"), app_sqlite.json_dump(run),
                app_sqlite.json_dump(run.get("workflow_options") or {}), app_sqlite.json_dump(run.get("result")),
                run.get("error"), app_sqlite.json_dump(artifacts or []), run.get("created_at"), run.get("updated_at"),
                run.get("started_at"), run.get("completed_at"), app_sqlite.json_dump(run), run["row_version"],
            ),
        )
    if run.get("conversation_id"):
        service_events.emit_run_updated(run)
        try:
            from services import conversation_store
            conversation_store.sync_run_to_conversation(run)
        except Exception as exc:
            LOGGER.warning("conversation_sync_failed operation=sync_run_to_conversation run_id=%s error_type=%s", run.get("run_id"), type(exc).__name__)
    from services import agent_run_event_hub
    agent_run_event_hub.publish_run_event(run)
    try:
        from services import agent_run_event_bus
        agent_run_event_bus.publish_run_event(run)
    except Exception as exc:
        LOGGER.warning("distributed_event_publish_failed operation=publish_run_event run_id=%s error_type=%s", run.get("run_id"), type(exc).__name__)
    return run


def create_run(payload: AgentRunCreate, user: dict[str, Any] | None = None) -> dict[str, Any]:
    data = payload.model_dump()
    if user:
        data.update({"user_id": user["user_id"], "username": user["username"], "role": user["role"]})
    return _write_run(_base_run(data))


def create_run_from_payload(payload: dict[str, Any], logs: list[str] | None = None) -> dict[str, Any]:
    return _write_run(_base_run(payload, logs=logs))


def _legacy_run(run_id: str, user_id: str | None = None, include_legacy: bool = True) -> dict[str, Any] | None:
    if not legacy_json_fallback.enabled():
        return None
    legacy_json_fallback.warn_once("agent_runs")
    paths: list[Path] = []
    if user_id:
        paths.append(agent_runs_dir(user_id) / f"{run_id}.json")
    else:
        users_root = API_ROOT / "runtime" / "users"
        paths.extend(users_root.glob(f"*/agent_runs/{run_id}.json") if users_root.exists() else [])
    if include_legacy:
        paths.append(_legacy_store_dir() / f"{run_id}.json")
    path = next((item for item in paths if item.exists()), None)
    return guard_agent_run_file(path) if path else None


def get_run(run_id: str, user_id: str | None = None, include_legacy: bool = True) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        if user_id:
            row = conn.execute("SELECT * FROM agent_runs WHERE run_id=? AND user_id=?", (run_id, user_id)).fetchone()
        else:
            row = conn.execute("SELECT * FROM agent_runs WHERE run_id=?", (run_id,)).fetchone()
    if row:
        return _row_to_run(row)
    legacy = _legacy_run(run_id, user_id, include_legacy)
    return _write_run(legacy) if legacy else None


def _legacy_runs(user_id: str | None, include_legacy: bool, include_all_users: bool) -> list[dict[str, Any]]:
    if not legacy_json_fallback.enabled():
        return []
    legacy_json_fallback.warn_once("agent_runs")
    paths: list[Path] = []
    users_root = API_ROOT / "runtime" / "users"
    if include_all_users and users_root.exists():
        paths.extend(users_root.glob("*/agent_runs/*.json"))
    elif user_id:
        paths.extend(agent_runs_dir(user_id).glob("*.json"))
    if include_legacy:
        paths.extend(_legacy_store_dir().glob("*.json"))
    runs: list[dict[str, Any]] = []
    for path in paths:
        run = guard_agent_run_file(path)
        if run:
            runs.append(run)
    return runs


def list_runs(limit: int = 20, user_id: str | None = None, include_legacy: bool = False, include_all_users: bool = False, status: str | None = None, agent_type: str | None = None) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 100000))
    clauses: list[str] = []
    params: list[Any] = []
    if user_id and not include_all_users:
        clauses.append("user_id=?")
        params.append(user_id)
    if status:
        clauses.append("status=?")
        params.append(status)
    if agent_type:
        clauses.append("agent_type=?")
        params.append(agent_type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with app_sqlite.connection() as conn:
        rows = conn.execute(f"SELECT * FROM agent_runs {where} ORDER BY updated_at DESC, created_at DESC LIMIT ?", (*params, safe_limit)).fetchall()  # nosec B608: where is built from fixed predicates; values are parameterized.
    runs = [_row_to_run(row) for row in rows]
    if include_legacy and len(runs) < safe_limit:
        known = {item["run_id"] for item in runs}
        for run in _legacy_runs(user_id, include_legacy, include_all_users):
            if run.get("run_id") in known:
                continue
            if status and run.get("status") != status:
                continue
            if agent_type and run.get("agent_type") != agent_type:
                continue
            runs.append(run)
    runs.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    fields = ("run_id", "user_id", "username", "role", "agent_type", "mode", "status", "progress", "current_step", "created_at", "updated_at", "error")
    return [{key: run.get(key) for key in fields} for run in runs[:safe_limit]]


def update_run(run_id: str, updates: dict[str, Any], user_id: str | None = None) -> dict[str, Any] | None:
    run = get_run(run_id, user_id)
    if run is None:
        return None
    old_status = str(run.get("status") or "")
    new_status = str(updates.get("status") or old_status)
    if old_status in TERMINAL_STATUSES and new_status not in {old_status, *TERMINAL_STATUSES}:
        run.setdefault("logs", []).append(f"ignored stale status update {new_status} after {old_status}")
        blocked = {"status", "progress", "current_step", "result", "error", "completed_at", "started_at"}
        updates = {key: value for key, value in updates.items() if key not in blocked}
    if old_status == "cancelled" and new_status == "completed":
        run.setdefault("logs", []).append("ignored completed update after cancelled")
        updates = {key: value for key, value in updates.items() if key not in {"status", "result", "error", "completed_at"}}
    run.update(updates)
    run["row_version"] = int(run.get("row_version") or 1) + 1
    run["updated_at"] = _now()
    return _write_run(run)


def append_log(run_id: str, log_message: str, user_id: str | None = None) -> dict[str, Any] | None:
    run = get_run(run_id, user_id)
    if run is None:
        return None
    run.setdefault("logs", []).append(log_message)
    run["updated_at"] = _now()
    return _write_run(run)


def cancel_run(run_id: str, user_id: str | None = None) -> tuple[dict[str, Any] | None, str | None]:
    run = get_run(run_id, user_id)
    if run is None:
        return None, "not_found"
    if run.get("status") == "cancelled":
        return run, None
    if run.get("status") in {"completed", "failed"}:
        return run, "finished"
    run.setdefault("logs", []).append("用户取消了任务")
    run.update({"status": "cancelled", "progress": 100, "current_step": "任务已取消", "error": None, "updated_at": _now()})
    return _write_run(run), None


def clone_run_for_retry(old_run_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    old_run = get_run(old_run_id, user_id)
    if old_run is None:
        return None
    payload = {key: old_run.get(key) for key in ("user_id", "username", "role", "agent_type", "mode", "prompt", "selected_skill_ids", "link", "file_ids", "dataset_ids", "image_paths", "video_path", "video_url", "session_id", "workflow_options", "conversation_id")}
    return create_run_from_payload(payload, logs=["任务已创建", f"从任务 {old_run_id} 重试创建"])
