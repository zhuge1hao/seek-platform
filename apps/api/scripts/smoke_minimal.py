import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[3]
TEST_VIDEO_FILE = os.getenv("VIDEO_AGENT_TEST_VIDEO", r"E:\USE\codexhome\fenge\videos\test\1.mp4")
TEST_OUTPUT_DIR = os.getenv("VIDEO_AGENT_TEST_OUTPUT_DIR", r"E:\USE\codexhome\fenge\output\test")
API_ROOT = ROOT / "apps" / "api"


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


def request_json(method: str, path: str, token: str | None = None, timeout: int = 20, **kwargs: Any) -> Any:
    headers = dict(kwargs.pop("headers", {}) or {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    response = requests.request(method, f"{api_base_url}{path}", headers=headers, timeout=timeout, **kwargs)
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


def configured_expected_version(cli_value: str | None = None) -> str:
    if cli_value:
        return cli_value
    if os.getenv("APP_EXPECTED_VERSION"):
        return str(os.environ["APP_EXPECTED_VERSION"])
    sys.path.insert(0, str(API_ROOT))
    from services.runtime_health_service import VERSION
    if not VERSION:
        raise RuntimeError("expected runtime version is not configured")
    return VERSION


def configured_expected_model(cli_value: str | None = None) -> str:
    if cli_value:
        return cli_value
    if os.getenv("APP_EXPECTED_MODEL"):
        return str(os.environ["APP_EXPECTED_MODEL"])
    sys.path.insert(0, str(API_ROOT))
    from services.runtime_health_service import MODEL
    if not MODEL:
        raise RuntimeError("expected runtime model is not configured")
    return MODEL


def assert_runtime_identity(runtime: dict[str, Any], expected_version: str, expected_model: str) -> None:
    actual_version = runtime.get("version")
    actual_model = runtime.get("model")
    if not actual_version:
        raise AssertionError("runtime health version is missing")
    if actual_version != expected_version:
        raise AssertionError(f"runtime health version mismatch: expected {expected_version}, got {actual_version}")
    if actual_model != expected_model:
        raise AssertionError(f"runtime health model mismatch: expected {expected_model}, got {actual_model}")
    check(True, f"runtime health version is {expected_version}")
    check(True, f"runtime health model is {expected_model}")


def video_agent_available() -> bool:
    try:
        video_agent_url = os.getenv("VIDEO_AGENT_BASE_URL") or os.getenv("VIDEO_AGENT_URL") or "http://127.0.0.1:8001"
        video_agent_url = video_agent_url.rstrip("/")
        response = requests.get(f"{video_agent_url}/health", timeout=5)
        data = response.json()
        return response.ok and data.get("status") == "ok"
    except requests.RequestException:
        return False


def run_video_e2e(token: str) -> None:
    created = request_json(
        "POST",
        "/api/agent-runs",
        token,
        json={
            "agent_type": "video_script_breakdown",
            "mode": "shot_text_excel",
            "prompt": "smoke_test v1.7 video agent e2e",
            "video_path": TEST_VIDEO_FILE,
            "workflow_options": {
                "smoke_test": True,
                "output_dir": TEST_OUTPUT_DIR,
                "subtitle_region": "bottom",
                "ocr_workers": 6,
                "export_json": True,
                "keep_debug_payload": True,
            },
        },
    )
    run_id = created["run_id"]
    conversation_id = created["conversation_id"]
    deadline = time.time() + 1800
    summary = request_json("GET", f"/api/agent-runs/{run_id}/summary", token)
    while time.time() < deadline and summary.get("status") not in {"completed", "failed", "cancelled"}:
        time.sleep(5)
        summary = request_json("GET", f"/api/agent-runs/{run_id}/summary", token)
    check(summary.get("status") == "completed", "video-agent-e2e run completed")
    detail = request_json("GET", f"/api/agent-runs/{run_id}/result", token)
    result = detail.get("result") or {}
    summary_json = result.get("summary") or {}
    check(summary_json.get("status") == "completed", "video-agent-e2e summary completed")
    check(bool(summary_json.get("excel_path") or summary_json.get("shot_report_path")), "video-agent-e2e result has output paths")
    files = result.get("files") or []
    check(any((item.get("file_type") or item.get("type")) == "excel" for item in files), "video-agent-e2e registered Excel artifact")
    check(any(str(item.get("filename") or item.get("name") or "").endswith(".json") for item in files), "video-agent-e2e registered JSON artifact")
    check(any(item.get("download_url") for item in files), "video-agent-e2e artifact download URL exists")
    conversation = request_json("GET", f"/api/conversations/{conversation_id}", token).get("conversation") or {}
    assistant = [item for item in conversation.get("messages") or [] if item.get("role") == "assistant" and item.get("run_id") == run_id]
    check(bool(assistant and assistant[-1].get("status") == "completed"), "video-agent-e2e assistant message completed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-agent-e2e", action="store_true")
    parser.add_argument("--require-video-agent", action="store_true")
    parser.add_argument("--expected-version")
    parser.add_argument("--expected-model")
    args = parser.parse_args()
    load_env()
    expected_version = configured_expected_version(args.expected_version)
    expected_model = configured_expected_model(args.expected_model)
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
        assert_runtime_identity(runtime, expected_version, expected_model)
        check(runtime.get("legacy_json_fallback_enabled") is False, "legacy JSON fallback disabled by default")
        database_backend = str((runtime.get("database") or {}).get("backend") or "sqlite").lower()

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
                "mode": "mock",
                "prompt": "smoke_test v1.7 agent persistence",
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
            check(summary.get("status") in {"completed", "failed"}, "agent run has terminal backend status")

        detail = request_json("GET", f"/api/conversations/{conversation_id}", token)
        messages = detail.get("conversation", {}).get("messages") or []
        check(len(messages) >= 2, "conversation detail includes user and assistant messages")
        if database_backend == "sqlite":
            check(db_count("SELECT COUNT(*) FROM agent_runs WHERE run_id=?", (run_id,)) == 1, "agent_runs row persisted")
            check(db_count("SELECT COUNT(*) FROM agent_conversations WHERE conversation_id=?", (conversation_id,)) == 1, "agent_conversations row persisted")
            check(db_count("SELECT COUNT(*) FROM agent_messages WHERE conversation_id=?", (conversation_id,)) >= 2, "agent_messages rows persisted")
        else:
            check(True, "agent persistence verified through API on postgres")

        storage = request_json("GET", "/api/admin/storage/health", token)
        check(storage.get("status") in {"ok", "warning"}, "storage health is readable")

        model_status = request_json("GET", "/api/qa/model-status", token)
        check("rag" in model_status and "deepseek" in model_status, "qa model status is readable")

        if args.video_agent_e2e:
            if not video_agent_available():
                if args.require_video_agent:
                    raise RuntimeError("video agent 8001 is not reachable")
                print("SKIP video-agent-e2e: 8001 is not reachable")
            else:
                run_video_e2e(token)
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("PASS smoke_minimal completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

