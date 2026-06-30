import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from services import app_sqlite


LOGGER = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***REDACTED***" if any(token in str(key).lower() for token in ("password", "token", "secret", "api_key", "apikey")) else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def client_ip(request: Any) -> str:
    forwarded = request.headers.get("x-forwarded-for") if request else None
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request and request.client else "unknown"


def write_log(action: str, status: str, user: dict[str, Any] | None = None, target: str = "", detail: dict[str, Any] | None = None, ip: str = "unknown") -> None:
    entry = {
        "time": _now(),
        "user_id": (user or {}).get("user_id") or "anonymous",
        "username": (user or {}).get("username") or "anonymous",
        "role": (user or {}).get("role") or "anonymous",
        "action": action,
        "target": target,
        "status": status,
        "ip": ip,
        "detail": _redact(detail or {}),
    }
    try:
        with app_sqlite.connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs(audit_id, user_id, username, action, resource_type, resource_id, detail_json, ip, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (f"audit_{uuid.uuid4().hex}", entry["user_id"], entry["username"], action, "", target, app_sqlite.json_dump({**entry["detail"], "status": status, "role": entry["role"]}), ip, "", entry["time"]),
            )
    except Exception as exc:
        LOGGER.warning("audit log 写入失败: %s", exc)


def list_logs(action: str | None = None, user: str | None = None, status: str | None = None, start_time: str | None = None, end_time: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if action:
        clauses.append("action=?")
        params.append(action)
    if user:
        clauses.append("(user_id=? OR username=?)")
        params.extend([user, user])
    if start_time:
        clauses.append("created_at>=?")
        params.append(start_time)
    if end_time:
        clauses.append("created_at<=?")
        params.append(end_time)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with app_sqlite.connection() as conn:
        rows = conn.execute(f"SELECT * FROM audit_logs {where} ORDER BY created_at DESC LIMIT ?", (*params, max(1, min(limit, 500)))).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        detail = app_sqlite.json_load(row["detail_json"], {}) or {}
        item = {
            "time": row["created_at"],
            "user_id": row["user_id"],
            "username": row["username"],
            "role": detail.get("role") or "",
            "action": row["action"],
            "target": row["resource_id"],
            "status": detail.get("status") or "",
            "ip": row["ip"],
            "detail": {key: value for key, value in detail.items() if key not in {"status", "role"}},
        }
        if status and item["status"] != status:
            continue
        items.append(item)
    return items
