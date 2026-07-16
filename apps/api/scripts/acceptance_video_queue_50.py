from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[3]
COMPOSE = ["docker", "compose", "-f", "docker-compose.prod.yml"]
VIDEO_PATH = r"E:\USE\codexhome\fenge\videos\test\1.mp4"


def load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for raw in env.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip().lstrip("\ufeff"), value.strip().strip('"').strip("'"))
    if os.getenv("APP_DATABASE_URL"):
        os.environ["APP_DB_BACKEND"] = os.getenv("APP_DB_BACKEND", "postgres")
        os.environ["APP_DATABASE_URL"] = (
            os.environ["APP_DATABASE_URL"].replace("@postgres:", "@127.0.0.1:").replace("@postgres/", "@127.0.0.1/")
        )
    if os.getenv("REDIS_URL"):
        os.environ["REDIS_URL"] = os.environ["REDIS_URL"].replace("://redis:", "://127.0.0.1:").replace("://redis/", "://127.0.0.1/")


load_env()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import redis_service, task_store, token_service, user_admin_service, user_store  # noqa: E402


def run_cmd(args: list[str], timeout: int = 120) -> str:
    env = dict(os.environ)
    for key in ("APP_DATABASE_URL", "REDIS_URL", "RAG_DATABASE_URL"):
        env.pop(key, None)
    result = subprocess.run(args, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def worker_video_containers() -> list[str]:
    out = run_cmd([*COMPOSE, "ps", "-q", "worker-video"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def pause_workers(ids: list[str]) -> None:
    if ids:
        run_cmd(["docker", "pause", *ids], timeout=60)


def unpause_workers(ids: list[str]) -> None:
    if ids:
        run_cmd(["docker", "unpause", *ids], timeout=60)


def queue_depths() -> dict[str, dict[str, int]]:
    from rq import Queue
    from rq.registry import StartedJobRegistry

    result: dict[str, dict[str, int]] = {}
    for name in ("general", "video", "dataset", "knowledge", "blueprint"):
        queue = Queue(name, connection=redis_service.binary_client())
        result[name] = {"queued": len(queue), "started": len(StartedJobRegistry(queue=queue))}
    return result


def create_token() -> tuple[str, str]:
    username = f"v184_p1_queue_{int(time.time())}_{secrets.token_hex(3)}"
    password = f"V184-{secrets.token_urlsafe(18)}"
    user_admin_service.create_user(username, password, "admin", True, "v1.8.4 P1 video queue validation")
    user = user_store.get_user(username)
    if user is None:
        raise RuntimeError("validation user missing")
    token, _expires = token_service.create_token(user)
    return username, token


def request_json(method: str, api: str, path: str, token: str | None = None, **kwargs: Any) -> Any:
    headers = dict(kwargs.pop("headers", {}) or {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, f"{api.rstrip('/')}{path}", headers=headers, timeout=30, **kwargs)
    try:
        data = response.json()
    except ValueError:
        data = response.text
    if not response.ok:
        raise RuntimeError(f"{method} {path} failed {response.status_code}: {data}")
    return data


def enqueue_controlled_video(index: int, user_id: str, sleep_seconds: int) -> tuple[str, str]:
    from rq import Queue

    run = task_store.create_run_from_payload(
        {
            "user_id": user_id,
            "username": user_id,
            "role": "admin",
            "agent_type": "video_script_breakdown",
            "mode": "mock",
            "prompt": f"v1.8.4 P1 controlled mock video job {index}",
            "workflow_options": {"acceptance": "video_queue_50", "mock": True},
        }
    )
    job_id = f"acceptance-video-50-{run['run_id']}"
    Queue("video", connection=redis_service.binary_client()).enqueue(
        "tasks.acceptance_tasks.controlled_run",
        run["run_id"],
        user_id,
        sleep_seconds,
        "completed",
        job_id=job_id,
        job_timeout=300,
    )
    task_store.update_run(run["run_id"], {"job_id": job_id}, user_id)
    return run["run_id"], job_id


def video_agent_available() -> bool:
    try:
        return requests.get("http://127.0.0.1:8001/health", timeout=5).json().get("status") == "ok"
    except Exception:
        return False


def submit_real_video(api: str, token: str, index: int, stamp: str) -> dict[str, Any]:
    output_dir = ROOT / "apps" / "api" / "runtime" / "video-queue-50" / stamp / f"real-{index}"
    return request_json(
        "POST",
        api,
        "/api/agent-runs",
        token,
        json={
            "agent_type": "video_script_breakdown",
            "mode": "shot_text_excel",
            "prompt": f"v1.8.4 P1 real video queue job {index}",
            "video_path": VIDEO_PATH,
            "workflow_options": {
                "output_dir": str(output_dir),
                "subtitle_region": "bottom",
                "subtitle_regions": ["bottom"],
                "ocr_workers": 6,
                "ocr_threads": 6,
                "export_json": True,
                "export_excel": True,
                "export_keyframes": True,
                "keep_debug_payload": True,
            },
        },
    )


def parse_time(value: str | None) -> float | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt).timestamp()
        except ValueError:
            pass
    return None


def status_counts(run_ids: list[str]) -> dict[str, int]:
    counts = {"completed": 0, "failed": 0, "cancelled": 0, "running": 0, "queued": 0}
    for run_id in run_ids:
        run = task_store.get_run(run_id, include_legacy=False) or {}
        status = str(run.get("status") or "queued")
        counts[status] = counts.get(status, 0) + 1
    return counts


def timing(run_ids: list[str]) -> dict[str, float | None]:
    waits: list[float] = []
    durations: list[float] = []
    for run_id in run_ids:
        run = task_store.get_run(run_id, include_legacy=False) or {}
        created = parse_time(run.get("created_at"))
        started = parse_time(run.get("started_at"))
        completed = parse_time(run.get("completed_at"))
        if created and started:
            waits.append(max(0.0, started - created))
        if started and completed:
            durations.append(max(0.0, completed - started))
    return {
        "avg_wait_seconds": round(sum(waits) / len(waits), 3) if waits else None,
        "max_wait_seconds": round(max(waits), 3) if waits else None,
        "avg_exec_seconds": round(sum(durations) / len(durations), 3) if durations else None,
        "max_exec_seconds": round(max(durations), 3) if durations else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--mock-count", type=int, default=48)
    parser.add_argument("--include-real-video", action="store_true")
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()
    load_env()
    username, token = create_token()
    stamp = str(int(time.time()))
    containers = worker_video_containers()
    run_ids: list[str] = []
    jobs: list[dict[str, Any]] = []
    real_available = args.include_real_video and video_agent_available()
    started = datetime.now().isoformat()
    pause_workers(containers)
    try:
        for index in range(args.mock_count):
            run_id, job_id = enqueue_controlled_video(index + 1, username, 3)
            run_ids.append(run_id)
            jobs.append({"kind": "mock", "run_id": run_id, "job_id": job_id})
        if run_ids:
            task_store.cancel_run(run_ids[-1], username)
        if real_available:
            for index in range(2):
                created = submit_real_video(args.api_base, token, index + 1, stamp)
                run_ids.append(created["run_id"])
                jobs.append({"kind": "real", "run_id": created["run_id"], "job_id": created.get("queue_job_id")})
        health_during_queue = {
            "health": request_json("GET", args.api_base, "/health"),
            "agents_readable": isinstance(request_json("GET", args.api_base, "/api/agents", token).get("agents"), list),
            "login_token_created": bool(token),
            "queue_depths": queue_depths(),
        }
    finally:
        unpause_workers(containers)
    max_queued = int(health_during_queue.get("health", {}).get("queue_depths", {}).get("video", {}).get("queued", 0) or 0)
    max_executing = 0
    deadline = time.monotonic() + 2100
    while time.monotonic() < deadline:
        depths = queue_depths()
        max_queued = max(max_queued, depths["video"]["queued"])
        max_executing = max(max_executing, depths["video"]["started"])
        counts = status_counts(run_ids)
        if counts.get("running", 0) == 0 and counts.get("queued", 0) == 0 and depths["video"]["queued"] == 0 and depths["video"]["started"] == 0:
            break
        time.sleep(2)
    final_counts = status_counts(run_ids)
    final_depths = queue_depths()
    report = {
        "started_at": started,
        "completed_at": datetime.now().isoformat(),
        "submitted": len(run_ids),
        "mock_video_jobs": args.mock_count,
        "real_video_jobs": 2 if real_available else 0,
        "real_video_jobs_status": "passed" if real_available else "not_run",
        "cancelled_run_id": run_ids[args.mock_count - 1] if run_ids else None,
        "counts": final_counts,
        "max_queued": max_queued,
        "max_executing": max_executing,
        "timing": timing(run_ids),
        "health_during_queue": health_during_queue,
        "final_queue_depths": final_depths,
        "other_queues_blocked": any(final_depths[name]["queued"] or final_depths[name]["started"] for name in ("general", "dataset", "knowledge", "blueprint")),
        "jobs_sample": jobs[:5],
    }
    report["passed"] = (
        report["submitted"] == args.mock_count + (2 if real_available else 0)
        and final_counts.get("queued", 0) == 0
        and final_counts.get("running", 0) == 0
        and final_depths["video"]["queued"] == 0
        and final_depths["video"]["started"] == 0
        and max_executing <= 2
        and not report["other_queues_blocked"]
        and final_counts.get("cancelled", 0) >= 1
        and final_counts.get("failed", 0) == 0
    )
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.json_report else None))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
