from __future__ import annotations

from time import perf_counter
from typing import Any

import requests

from services import agent_connector_store


DEFAULT_START_HINT = "Start local video agent: cd E:\\USE\\codexhome\\fenge && .\\start_agent_8001.bat"


def _health_url(connector: dict[str, Any]) -> str:
    base_url = str(connector.get("base_url") or "http://127.0.0.1:8001").rstrip("/")
    path = str(connector.get("health_path") or "/health")
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base_url}{path}"


def check_status(timeout_seconds: float = 3.0) -> dict[str, Any]:
    connector = agent_connector_store.get_connector("video_script_agent")
    if connector is None:
        return {
            "status": "disconnected",
            "connector_id": "video_script_agent",
            "name": "video_script_agent",
            "base_url": "http://127.0.0.1:8001",
            "reachable": False,
            "latency_ms": None,
            "error": "video_script_agent connector not found",
            "message": "Local video agent connector is not configured.",
            "start_hint": DEFAULT_START_HINT,
        }

    base_url = str(connector.get("base_url") or "http://127.0.0.1:8001").rstrip("/")
    mode = str(connector.get("mode") or "http").lower()
    name = connector.get("name") or "video_script_agent"
    if not connector.get("enabled", True):
        return {
            "status": "disabled",
            "connector_id": connector.get("connector_id"),
            "name": name,
            "base_url": base_url,
            "reachable": False,
            "latency_ms": None,
            "error": "video_script_agent connector is disabled",
            "message": "Local video agent connector is disabled.",
            "start_hint": "Enable video_script_agent in Connector management.",
        }
    if mode == "mock":
        return {
            "status": "mock",
            "connector_id": connector.get("connector_id"),
            "name": name,
            "base_url": base_url,
            "reachable": True,
            "latency_ms": 0,
            "health_status": "mock",
            "message": "Current connector is mock and will not call the real local video agent.",
            "start_hint": "",
        }
    if mode != "http":
        return {
            "status": "connected",
            "connector_id": connector.get("connector_id"),
            "name": name,
            "base_url": base_url,
            "reachable": True,
            "latency_ms": None,
            "health_status": "cli",
            "message": "Current connector uses CLI mode.",
            "start_hint": "",
        }

    started = perf_counter()
    try:
        response = requests.get(_health_url(connector), timeout=timeout_seconds)
        latency_ms = int((perf_counter() - started) * 1000)
        response.raise_for_status()
        payload = response.json()
        health_status = str(payload.get("status") or "").lower()
        connected = health_status == "ok"
        return {
            "status": "connected" if connected else "disconnected",
            "connector_id": connector.get("connector_id"),
            "name": name,
            "base_url": base_url,
            "reachable": connected,
            "latency_ms": latency_ms,
            "health_status": payload.get("status"),
            "service": payload.get("service"),
            "version": payload.get("version"),
            "model_version": payload.get("model_version") or payload.get("model"),
            "project_root": payload.get("project_root"),
            "message": "Local video agent connected." if connected else "Local video agent health is not ok.",
            "start_hint": "" if connected else DEFAULT_START_HINT,
            "error": None if connected else str(payload),
        }
    except Exception as exc:
        return {
            "status": "disconnected",
            "connector_id": connector.get("connector_id"),
            "name": name,
            "base_url": base_url,
            "reachable": False,
            "latency_ms": int((perf_counter() - started) * 1000),
            "error": f"Cannot reach {_health_url(connector)}: {exc}",
            "message": "Local video agent is disconnected.",
            "start_hint": DEFAULT_START_HINT,
        }
