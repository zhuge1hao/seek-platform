from __future__ import annotations

import socket
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

from services import agent_connector_store


DEFAULT_START_HINT = "请在本地启动视频拆解 Agent 服务，确认监听 http://127.0.0.1:8001"


def check_status(timeout_seconds: float = 3.0) -> dict[str, Any]:
    connector = agent_connector_store.get_connector("video_script_agent")
    if connector is None:
        return {
            "status": "disconnected",
            "connector_id": "video_script_agent",
            "name": "视频拆解智能体",
            "base_url": "http://127.0.0.1:8001",
            "reachable": False,
            "latency_ms": None,
            "error": "视频拆解 connector 不存在",
            "message": "本地视频拆解 Agent 未配置",
            "start_hint": DEFAULT_START_HINT,
        }

    base_url = str(connector.get("base_url") or "http://127.0.0.1:8001").rstrip("/")
    mode = str(connector.get("mode") or "http").lower()
    name = connector.get("name") or "视频拆解智能体"
    if not connector.get("enabled", True):
        return {
            "status": "disabled",
            "connector_id": connector.get("connector_id"),
            "name": name,
            "base_url": base_url,
            "reachable": False,
            "latency_ms": None,
            "error": "视频拆解 connector 已禁用",
            "message": "本地视频拆解 Agent 连接器已禁用",
            "start_hint": "请在本地 Agent / Connector 管理中启用 video_script_agent",
        }
    if mode == "mock":
        return {
            "status": "mock",
            "connector_id": connector.get("connector_id"),
            "name": name,
            "base_url": base_url,
            "reachable": True,
            "latency_ms": 0,
            "message": "当前为 mock connector，不会调用真实本地视频拆解 Agent",
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
            "message": "当前 connector 使用 CLI 模式，提交任务时会调用本地命令",
            "start_hint": "",
        }

    parsed = urlparse(base_url if "://" in base_url else f"http://{base_url}")
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    started = perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            latency_ms = int((perf_counter() - started) * 1000)
            return {
                "status": "connected",
                "connector_id": connector.get("connector_id"),
                "name": name,
                "base_url": base_url,
                "reachable": True,
                "latency_ms": latency_ms,
                "message": "本地视频拆解 Agent 已连接",
                "start_hint": "",
            }
    except OSError as exc:
        return {
            "status": "disconnected",
            "connector_id": connector.get("connector_id"),
            "name": name,
            "base_url": base_url,
            "reachable": False,
            "latency_ms": int((perf_counter() - started) * 1000),
            "error": f"无法连接 {base_url}：{exc}",
            "message": "本地视频拆解 Agent 未启动，请先启动 8001 服务后再提交任务",
            "start_hint": DEFAULT_START_HINT,
        }
