from __future__ import annotations

import argparse
import json
import os
import queue
import secrets
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[3]
API_DIR = ROOT / "apps" / "api"


def load_env() -> dict[str, str]:
    env = dict(os.environ)
    path = ROOT / ".env"
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env.setdefault(key.strip().lstrip("\ufeff"), value.strip().strip('"').strip("'"))
    if env.get("APP_DATABASE_URL"):
        env["APP_DB_BACKEND"] = env.get("APP_DB_BACKEND", "postgres")
        env["APP_DATABASE_URL"] = env["APP_DATABASE_URL"].replace("@postgres:", "@127.0.0.1:").replace("@postgres/", "@127.0.0.1/")
    if env.get("REDIS_URL"):
        env["REDIS_URL"] = env["REDIS_URL"].replace("://redis:", "://127.0.0.1:").replace("://redis/", "://127.0.0.1/")
    os.environ.update(env)
    return env


load_env()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import conversation_store, task_store, token_service, user_admin_service, user_store  # noqa: E402


def run_cmd(args: list[str], timeout: int = 60) -> str:
    env = dict(os.environ)
    for key in ("APP_DATABASE_URL", "REDIS_URL", "RAG_DATABASE_URL"):
        env.pop(key, None)
    result = subprocess.run(args, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def redis_container() -> str:
    return run_cmd(["docker", "compose", "-f", "docker-compose.prod.yml", "ps", "-q", "redis"])


def create_token() -> tuple[str, str]:
    username = f"v184_p1_redis_{int(time.time())}_{secrets.token_hex(3)}"
    password = f"V184-{secrets.token_urlsafe(18)}"
    user_admin_service.create_user(username, password, "admin", True, "v1.8.4 P1 Redis recovery validation")
    user = user_store.get_user(username)
    if user is None:
        raise RuntimeError("validation user missing")
    token, _expires = token_service.create_token(user)
    return username, token


def new_run(user_id: str, prompt: str) -> dict[str, Any]:
    run = task_store.create_run_from_payload(
        {"user_id": user_id, "username": user_id, "role": "admin", "agent_type": "acceptance_redis", "mode": "acceptance", "prompt": prompt}
    )
    conversation, _created = conversation_store.attach_run(run)
    task_store.update_run(run["run_id"], {"conversation_id": conversation["conversation_id"]}, user_id)
    return task_store.get_run(run["run_id"], user_id, include_legacy=False) or run


def request_json(api: str, path: str, token: str | None = None) -> Any:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.get(f"{api.rstrip('/')}{path}", headers=headers, timeout=10)
    try:
        data = response.json()
    except ValueError:
        data = response.text
    if not response.ok:
        raise RuntimeError(f"GET {path} failed {response.status_code}: {data}")
    return data


def wait_api(api: str, timeout: int = 45) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if request_json(api, "/health").get("status") == "ok":
                return
        except Exception:
            time.sleep(1)
    raise TimeoutError(f"{api} did not become healthy")


def start_api_b(env: dict[str, str], port: int) -> subprocess.Popen:
    next_env = dict(env)
    next_env["PYTHONPATH"] = str(API_DIR)
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=API_DIR,
        env=next_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def collect_sse(api: str, run_id: str, token: str, out: queue.Queue[dict[str, Any]]) -> None:
    headers = {"Authorization": f"Bearer {token}", "Accept": "text/event-stream"}
    try:
        with requests.get(f"{api}/api/agent-runs/{run_id}/events", headers=headers, stream=True, timeout=(10, 90)) as response:
            response.raise_for_status()
            event = "message"
            data_lines: list[str] = []
            for raw_line in response.iter_lines(decode_unicode=True):
                line = raw_line or ""
                if line.startswith("event: "):
                    event = line[7:]
                elif line.startswith("data: "):
                    data_lines.append(line[6:])
                elif line == "" and data_lines:
                    payload = json.loads("\n".join(data_lines))
                    out.put({"event": event, "payload": payload, "received_at": time.time()})
                    if payload.get("status") in {"completed", "failed", "cancelled"}:
                        break
                    event = "message"
                    data_lines = []
    except Exception as exc:
        out.put({"event": "sse_error", "error": type(exc).__name__, "message": str(exc)[:200], "received_at": time.time()})


def drain(q: queue.Queue[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    while not q.empty():
        items.append(q.get())
    return items


def assistant_count(run_id: str) -> int:
    from services import app_sqlite

    with app_sqlite.connection() as conn:
        return int(conn.execute("SELECT COUNT(*) AS count FROM agent_messages WHERE run_id=? AND role='assistant'", (run_id,)).fetchone()["count"])


def leak_free(events: list[dict[str, Any]]) -> bool:
    text = json.dumps(events, ensure_ascii=False).lower()
    return not any(token in text for token in ("raw_response", "workflow_options", "authorization", "bearer ", "api_key", "secret", "token"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-a", default="http://127.0.0.1:8000")
    parser.add_argument("--api-b-port", type=int, default=8002)
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()
    env = load_env()
    username, token = create_token()
    api_b = f"http://127.0.0.1:{args.api_b_port}"
    process = start_api_b(env, args.api_b_port)
    redis_id = redis_container()
    paused = False
    try:
        wait_api(api_b)
        run = new_run(username, "v1.8.4 Redis pause recovery")
        events_q: queue.Queue[dict[str, Any]] = queue.Queue()
        thread = threading.Thread(target=collect_sse, args=(api_b, run["run_id"], token, events_q), daemon=True)
        thread.start()
        time.sleep(1)
        task_store.update_run(run["run_id"], {"status": "running", "progress": 33, "current_step": "before redis pause"}, username)
        time.sleep(2)
        pause_started = time.time()
        run_cmd(["docker", "pause", redis_id], timeout=60)
        paused = True
        task_store.update_run(run["run_id"], {"status": "running", "progress": 66, "current_step": "redis paused db truth"}, username)
        fallback_summary = request_json(api_b, f"/api/agent-runs/{run['run_id']}/summary", token)
        task_store.update_run(
            run["run_id"],
            {"status": "completed", "progress": 100, "current_step": "redis recovery completed", "result": {"answer": "redis recovery completed", "files": []}, "error": None},
            username,
        )
        thread.join(timeout=45)
        run_cmd(["docker", "unpause", redis_id], timeout=60)
        paused = False
        recovered_at = time.time()
        events = drain(events_q)

        post = new_run(username, "v1.8.4 Redis post recovery")
        post_q: queue.Queue[dict[str, Any]] = queue.Queue()
        post_thread = threading.Thread(target=collect_sse, args=(api_b, post["run_id"], token, post_q), daemon=True)
        post_thread.start()
        time.sleep(1)
        task_store.update_run(
            post["run_id"],
            {"status": "completed", "progress": 100, "current_step": "post recovery completed", "result": {"answer": "post recovery completed", "files": []}},
            username,
        )
        post_thread.join(timeout=20)
        post_events = drain(post_q)
        terminal_events = [item for item in events if (item.get("payload") or {}).get("status") in {"completed", "failed", "cancelled"}]
        event_times = [item["received_at"] for item in events if item.get("received_at")]
        p95 = None
        if len(event_times) >= 2:
            deltas = sorted(event_times[index] - event_times[index - 1] for index in range(1, len(event_times)))
            p95 = round(deltas[min(len(deltas) - 1, int(len(deltas) * 0.95))], 3)
        report = {
            "run_id": run["run_id"],
            "post_recovery_run_id": post["run_id"],
            "redis_pause_seconds": round(recovered_at - pause_started, 3),
            "redis_recovery_seconds": 0,
            "fallback_summary_status": fallback_summary.get("status"),
            "fallback_summary_progress": fallback_summary.get("progress"),
            "events": [{"event": item.get("event"), "status": (item.get("payload") or {}).get("status"), "progress": (item.get("payload") or {}).get("progress")} for item in events],
            "post_recovery_events": [{"event": item.get("event"), "status": (item.get("payload") or {}).get("status")} for item in post_events],
            "event_p95_seconds": p95,
            "duplicate_terminal": len(terminal_events) > 1,
            "assistant_messages": assistant_count(run["run_id"]),
            "post_recovery_assistant_messages": assistant_count(post["run_id"]),
            "sensitive_leak": not leak_free(events + post_events),
        }
        report["passed"] = (
            fallback_summary.get("progress") == 66
            and any((item.get("payload") or {}).get("status") == "completed" for item in events)
            and any((item.get("payload") or {}).get("status") == "completed" for item in post_events)
            and not report["duplicate_terminal"]
            and report["assistant_messages"] == 1
            and report["post_recovery_assistant_messages"] == 1
            and not report["sensitive_leak"]
        )
        print(json.dumps(report, ensure_ascii=False, indent=2 if args.json_report else None))
        return 0 if report["passed"] else 1
    finally:
        if paused:
            try:
                run_cmd(["docker", "unpause", redis_id], timeout=60)
            except Exception:
                pass
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
