import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from schemas.agent_runs import DEFAULT_VIDEO_SCRIPT_SESSION_ID
from services import app_sqlite
from services.config_backup_service import backup_file, move_to_corrupted, resolve_runtime_path


CONNECTOR_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
VALID_MODES = {"http", "cli", "mock"}
VALID_PAYLOAD_STYLES = {"protocol", "legacy"}


class ConnectorStoreError(RuntimeError):
    pass


class ConnectorConflictError(ConnectorStoreError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _store_path() -> Path:
    path = resolve_runtime_path(os.getenv("AGENT_CONNECTOR_STORE_PATH", "runtime/connectors/agent_connectors.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connector(connector_id: str, name: str, agent_type: str, enabled: bool, mode: str = "mock", description: str = "") -> dict[str, Any]:
    now = _now()
    is_video = connector_id == "video_script_agent"
    return {
        "connector_id": connector_id,
        "name": name,
        "agent_type": agent_type,
        "mode": "http" if is_video else mode,
        "base_url": "http://127.0.0.1:8001" if is_video else "http://localhost:8001",
        "health_path": "/health",
        "endpoint": "/run" if is_video else "/api/agent/run",
        "cli_command": "",
        "session_id": DEFAULT_VIDEO_SCRIPT_SESSION_ID if is_video else "",
        "timeout_seconds": 1800,
        "payload_style": "protocol",
        "enabled": enabled,
        "description": description,
        "created_at": now,
        "updated_at": now,
    }


def _repair_video_connector_defaults(connector: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if connector.get("connector_id") != "video_script_agent":
        return connector, False
    repaired = dict(connector)
    changed = False
    if repaired.get("base_url") == "http://localhost:8001":
        repaired["base_url"] = "http://127.0.0.1:8001"
        changed = True
    if repaired.get("endpoint") == "/api/agent/run":
        repaired["endpoint"] = "/run"
        changed = True
    if not repaired.get("health_path"):
        repaired["health_path"] = "/health"
        changed = True
    if repaired.get("payload_style") != "protocol":
        repaired["payload_style"] = "protocol"
        changed = True
    if changed:
        repaired["updated_at"] = _now()
    return repaired, changed


def default_connectors() -> dict[str, dict[str, Any]]:
    items = [
        _connector("video_script_agent", "视频脚本拆解本地 Agent", "video_script_breakdown", True, description="用于视频脚本拆解的本地 agent"),
        _connector("smart_selection_agent", "智能选款本地 Agent", "smart_selection", False, description="后续用于智能选款"),
        _connector("competitor_analysis_agent", "竞品分析本地 Agent", "competitor_analysis", False, description="后续用于竞品分析"),
        _connector("detail_page_agent", "详情页策划本地 Agent", "detail_page_planning", False, description="后续用于详情页策划"),
        _connector("main_image_breakdown_agent", "主图拆解本地 Agent", "hot_main_image_breakdown", False, description="后续用于主图拆解"),
    ]
    return {item["connector_id"]: item for item in items}


def _document(connectors: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {"schema_version": "1.0", "updated_at": _now(), "connectors": connectors}


def _validate(payload: dict[str, Any], connector_id: str | None = None) -> dict[str, Any]:
    value = dict(payload)
    actual_id = connector_id or str(value.get("connector_id") or "").strip()
    if not CONNECTOR_ID_PATTERN.fullmatch(actual_id):
        raise ConnectorStoreError("connector_id 只能包含字母、数字、下划线和短横线。")
    mode = str(value.get("mode") or "mock").lower()
    if mode not in VALID_MODES:
        raise ConnectorStoreError("mode 只支持 http、cli、mock。")
    payload_style = str(value.get("payload_style") or "protocol").lower()
    if payload_style not in VALID_PAYLOAD_STYLES:
        raise ConnectorStoreError("payload_style 只支持 protocol、legacy。")
    try:
        timeout = int(value.get("timeout_seconds") or 1800)
    except (TypeError, ValueError) as exc:
        raise ConnectorStoreError("timeout_seconds 必须为正整数。") from exc
    if timeout <= 0:
        raise ConnectorStoreError("timeout_seconds 必须为正整数。")
    now = _now()
    normalized = {
        "connector_id": actual_id,
        "name": str(value.get("name") or actual_id).strip() or actual_id,
        "agent_type": str(value.get("agent_type") or "").strip(),
        "mode": mode,
        "base_url": str(value.get("base_url") or "").strip(),
        "health_path": str(value.get("health_path") or "/health").strip(),
        "endpoint": str(value.get("endpoint") or "/api/agent/run").strip(),
        "cli_command": str(value.get("cli_command") or "").strip(),
        "session_id": str(value.get("session_id") or "").strip(),
        "timeout_seconds": timeout,
        "payload_style": payload_style,
        "enabled": bool(value.get("enabled", True)),
        "description": str(value.get("description") or "").strip(),
        "created_at": str(value.get("created_at") or now),
        "updated_at": str(value.get("updated_at") or now),
    }
    if actual_id == "video_script_agent" and not normalized["session_id"]:
        normalized["session_id"] = DEFAULT_VIDEO_SCRIPT_SESSION_ID
    return normalized


def _write(connectors: dict[str, dict[str, Any]]) -> None:
    with app_sqlite.connection() as conn:
        for connector in connectors.values():
            conn.execute(
                """
                INSERT INTO local_agent_connectors(connector_id, name, connector_type, enabled, base_url, command, timeout_seconds, created_by, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(connector_id) DO UPDATE SET name=excluded.name, connector_type=excluded.connector_type, enabled=excluded.enabled,
                  base_url=excluded.base_url, command=excluded.command, timeout_seconds=excluded.timeout_seconds, updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
                """,
                (
                    connector["connector_id"], connector.get("name") or connector["connector_id"], connector.get("mode"),
                    1 if connector.get("enabled", True) else 0, connector.get("base_url"), connector.get("cli_command"),
                    connector.get("timeout_seconds"), connector.get("created_by"), connector.get("created_at"),
                    connector.get("updated_at"), app_sqlite.json_dump(connector),
                ),
            )


def _load() -> dict[str, dict[str, Any]]:
    with app_sqlite.connection() as conn:
        rows = conn.execute("SELECT * FROM local_agent_connectors").fetchall()
    if rows:
        loaded: dict[str, dict[str, Any]] = {}
        for row in rows:
            metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
            connector = _validate({
                **metadata,
                "connector_id": row["connector_id"],
                "name": row["name"],
                "mode": row["connector_type"],
                "enabled": bool(row["enabled"]),
                "base_url": row["base_url"],
                "cli_command": row["command"],
                "timeout_seconds": row["timeout_seconds"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }, row["connector_id"])
            connector, _ = _repair_video_connector_defaults(connector)
            loaded[row["connector_id"]] = connector
        for connector_id, item in default_connectors().items():
            loaded.setdefault(connector_id, item)
        if len(loaded) > len(rows) or any(
            row["connector_id"] == "video_script_agent"
            and (row["base_url"] == "http://localhost:8001" or (app_sqlite.json_load(row["metadata_json"], {}) or {}).get("endpoint") == "/api/agent/run")
            for row in rows
        ):
            _write(loaded)
        return loaded
    path = _store_path()
    if not path.exists():
        defaults = default_connectors()
        _write(defaults)
        return defaults
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        source = raw.get("connectors", raw) if isinstance(raw, dict) else None
        if not isinstance(source, dict):
            raise ValueError("连接器配置结构无效")
        defaults = default_connectors()
        normalized: dict[str, dict[str, Any]] = {}
        for connector_id, item in source.items():
            if isinstance(item, dict):
                normalized[connector_id] = _validate(item, connector_id)
        for connector_id, item in defaults.items():
            normalized.setdefault(connector_id, item)
        if raw.get("schema_version") != "1.0" or source != normalized:
            backup_file(path, "before_connector_migration")
            _write(normalized)
        return normalized
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, ConnectorStoreError) as exc:
        move_to_corrupted(path, "invalid_connector_config")
        defaults = default_connectors()
        _write(defaults)
        return defaults


def list_connectors(enabled_only: bool = False) -> list[dict[str, Any]]:
    items = list(_load().values())
    if enabled_only:
        items = [item for item in items if item.get("enabled")]
    return sorted(items, key=lambda item: (not item.get("enabled", False), item.get("name", "")))


def get_connector(connector_id: str) -> dict[str, Any] | None:
    return _load().get(connector_id)


def create_connector(payload: dict[str, Any]) -> dict[str, Any]:
    connectors = _load()
    connector = _validate(payload)
    connector_id = connector["connector_id"]
    if connector_id in connectors:
        raise ConnectorConflictError(f"连接器已存在：{connector_id}")
    connectors[connector_id] = connector
    _write(connectors)
    return connector


def update_connector(connector_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    connectors = _load()
    existing = connectors.get(connector_id)
    if existing is None:
        return None
    allowed = {"name", "agent_type", "mode", "base_url", "health_path", "endpoint", "cli_command", "session_id", "timeout_seconds", "payload_style", "enabled", "description"}
    merged = {**existing, **{key: value for key, value in updates.items() if key in allowed}}
    merged["created_at"] = existing.get("created_at")
    merged["updated_at"] = _now()
    connector = _validate(merged, connector_id)
    connectors[connector_id] = connector
    _write(connectors)
    return connector


def disable_connector(connector_id: str) -> dict[str, Any] | None:
    return update_connector(connector_id, {"enabled": False})
