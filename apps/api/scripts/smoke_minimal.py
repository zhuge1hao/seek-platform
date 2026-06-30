import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[3]


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip().lstrip("\ufeff"), value.strip().strip('"').strip("'"))


def request_json(method: str, path: str, token: str | None = None, **kwargs: Any) -> Any:
    headers = dict(kwargs.pop("headers", {}) or {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{os.getenv('API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')}{path}"
    response = requests.request(method, url, headers=headers, timeout=20, **kwargs)
    try:
        data = response.json()
    except ValueError:
        data = response.text
    if not response.ok:
        raise RuntimeError(f"{method} {path} failed: {response.status_code} {data}")
    return data


def db_path() -> Path:
    configured = os.getenv("APP_SQLITE_PATH", "apps/api/runtime/app/meizhaiseek.sqlite3")
    path = Path(configured)
    return path if path.is_absolute() else ROOT / path


def db_count(sql: str, params: tuple[Any, ...]) -> int:
    with sqlite3.connect(db_path()) as conn:
        return int(conn.execute(sql, params).fetchone()[0])


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def main() -> int:
    load_env()
    username = os.getenv("SMOKE_ADMIN_USERNAME") or os.getenv("MEIZHAISEEK_ADMIN_USERNAME")
    password = os.getenv("SMOKE_ADMIN_PASSWORD") or os.getenv("MEIZHAISEEK_ADMIN_INITIAL_PASSWORD")
    if not username or not password:
        print("FAIL admin credentials missing. Set SMOKE_ADMIN_USERNAME/SMOKE_ADMIN_PASSWORD or MEIZHAISEEK_ADMIN_USERNAME/MEIZHAISEEK_ADMIN_INITIAL_PASSWORD.", file=sys.stderr)
        return 2

    try:
        health = request_json("GET", "/health")
        check(health.get("service") == "meizhaiseek-api", "/health returns meizhaiseek-api")

        login = request_json("POST", "/api/auth/login", json={"username": username, "password": password})
        token = login["token"]
        check(bool(token), "admin login returns token")

        runtime = request_json("GET", "/api/admin/runtime/health", token)
        check(runtime.get("version") == "v1.6.3", "runtime health version is v1.6.3")

        conversations = request_json("GET", "/api/conversations", token)
        check(isinstance(conversations.get("conversations"), list), "agent conversations list is readable")

        video_status = request_json("GET", "/api/agents/video-script/status", token)
        expect_failed = video_status.get("status") in {"disconnected", "disabled"}

        created = request_json(
            "POST",
            "/api/agent-runs",
            token,
            json={
                "agent_type": "video_script_breakdown",
                "mode": "standard_breakdown",
                "prompt": "smoke_test v1.6.3 agent persistence",
                "video_url": "https://example.com/smoke-v163.mp4",
                "workflow_options": {"smoke_test": True, "export_json": False, "keep_debug_payload": True},
            },
        )
        run_id = created.get("run_id")
        conversation_id = created.get("conversation_id")
        check(bool(run_id and conversation_id), "agent run returns run_id and conversation_id")

        summary = request_json("GET", f"/api/agent-runs/{run_id}/summary", token)
        for _ in range(12):
            if summary.get("status") in {"completed", "failed", "cancelled"}:
                break
            time.sleep(1)
            summary = request_json("GET", f"/api/agent-runs/{run_id}/summary", token)
        if expect_failed:
            check(summary.get("status") == "failed", "8001 disconnected task is truly failed")
        else:
            check(summary.get("status") in {"running", "completed", "failed"}, "agent run has real backend status")

        detail = request_json("GET", f"/api/conversations/{conversation_id}", token)
        messages = detail.get("conversation", {}).get("messages") or []
        check(len(messages) >= 2, "conversation detail includes user and assistant messages")
        check(db_count("SELECT COUNT(*) FROM agent_runs WHERE run_id=?", (run_id,)) == 1, "agent_runs row persisted")
        check(db_count("SELECT COUNT(*) FROM agent_conversations WHERE conversation_id=?", (conversation_id,)) == 1, "agent_conversations row persisted")
        check(db_count("SELECT COUNT(*) FROM agent_messages WHERE conversation_id=?", (conversation_id,)) >= 2, "agent_messages rows persisted")

        storage = request_json("GET", "/api/admin/storage/health", token)
        check(storage.get("status") in {"ok", "warning"}, "storage health is readable")

        model_status = request_json("GET", "/api/qa/model-status", token)
        check("rag" in model_status and "deepseek" in model_status, "qa model status is readable")
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("PASS smoke_minimal completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
