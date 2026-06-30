from time import perf_counter
from typing import Any

from services.local_agent_client import run_generic_agent_protocol, run_video_script_breakdown_protocol


def test_connector(connector: dict[str, Any], prompt: str, extra_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "session_id": connector.get("session_id") or "",
        "agent_type": connector.get("agent_type") or "connector_test",
        "agent_name": connector.get("name") or connector.get("connector_id"),
        "mode": "test",
        "prompt": prompt or "测试连接",
        "output_dir": "",
        "options": {},
        **(extra_payload or {}),
    }
    started = perf_counter()
    if payload["agent_type"] == "video_script_breakdown":
        result = run_video_script_breakdown_protocol(payload, connector=connector)
    else:
        result = run_generic_agent_protocol(payload, connector=connector)
    duration_ms = int((perf_counter() - started) * 1000)
    return {
        "status": "success" if result.get("ok") else "failed",
        "connector_id": connector.get("connector_id"),
        "mode": connector.get("mode"),
        "duration_ms": duration_ms,
        "http_status": result.get("http_status"),
        "response_preview": {"answer": result.get("answer"), "summary": result.get("summary"), "files": result.get("files")} if result.get("ok") else None,
        "error": result.get("error"),
    }
