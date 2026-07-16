from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
COMPOSE = ["docker", "compose", "-f", "docker-compose.prod.yml"]
QUEUES = ("general", "video", "knowledge", "dataset", "blueprint")


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

from services import agent_run_maintenance, app_sqlite, redis_service, task_store  # noqa: E402


def run_cmd(args: list[str], timeout: int = 120) -> str:
    env = dict(os.environ)
    for key in ("APP_DATABASE_URL", "REDIS_URL", "RAG_DATABASE_URL"):
        env.pop(key, None)
    result = subprocess.run(args, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def service_for_queue(queue: str) -> str:
    return "worker-video" if queue == "video" else "worker-general"


def scale(service: str, count: int) -> None:
    run_cmd([*COMPOSE, "up", "-d", "--scale", f"{service}={count}", service], timeout=240)


def containers(service: str) -> list[str]:
    out = run_cmd([*COMPOSE, "ps", "-q", service])
    return [line.strip() for line in out.splitlines() if line.strip()]


def queue_depth(queue_name: str) -> dict[str, int]:
    from rq import Queue
    from rq.registry import StartedJobRegistry

    queue = Queue(queue_name, connection=redis_service.binary_client())
    return {"queued": len(queue), "started": len(StartedJobRegistry(queue=queue))}


def cleanup_acceptance_started(queue_name: str) -> int:
    from rq import Queue
    from rq.registry import StartedJobRegistry

    queue = Queue(queue_name, connection=redis_service.binary_client())
    registry = StartedJobRegistry(queue=queue)
    removed = 0
    for job_id in registry.get_job_ids(cleanup=False):
        if str(job_id).startswith("acceptance-worker-"):
            registry.remove(job_id, delete_job=False)
            removed += 1
    return removed


def enqueue(queue_name: str, run_id: str, user_id: str, sleep_seconds: int) -> str:
    from rq import Queue

    job_id = f"acceptance-worker-{queue_name}-{run_id}"
    queue = Queue(queue_name, connection=redis_service.binary_client())
    queue.enqueue("tasks.acceptance_tasks.controlled_run", run_id, user_id, sleep_seconds, "completed", job_id=job_id, job_timeout=300)
    task_store.update_run(run_id, {"job_id": job_id}, user_id)
    return job_id


def new_run(queue_name: str) -> dict[str, Any]:
    return task_store.create_run_from_payload(
        {
            "user_id": "v184_p1_acceptance",
            "username": "v184_p1_acceptance",
            "role": "admin",
            "agent_type": f"acceptance_{queue_name}",
            "mode": "acceptance",
            "prompt": f"v1.8.4 P1 worker recovery {queue_name}",
            "workflow_options": {"queue": queue_name},
        }
    )


def wait_running(run_id: str, user_id: str, timeout: int = 45) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        run = task_store.get_run(run_id, user_id, include_legacy=False)
        if run and run.get("status") == "running" and int(run.get("progress") or 0) >= 25:
            return run
        time.sleep(0.5)
    raise TimeoutError(f"{run_id} did not enter running")


def artifact_count(run_id: str) -> int:
    with app_sqlite.connection() as conn:
        return int(conn.execute("SELECT COUNT(*) AS count FROM artifacts WHERE run_id=?", (run_id,)).fetchone()["count"])


def make_stale(run_id: str) -> None:
    with app_sqlite.connection() as conn:
        conn.execute("UPDATE agent_runs SET updated_at=? WHERE run_id=?", ("2000-01-01 00:00:00", run_id))


def crash_recovery(queue_name: str) -> dict[str, Any]:
    service = service_for_queue(queue_name)
    expected_note = "standalone worker not configured; worker-general consumes this queue" if queue_name in {"knowledge", "dataset", "blueprint"} else ""
    scale(service, 1)
    run = new_run(queue_name)
    job_id = enqueue(queue_name, run["run_id"], run["user_id"], 180)
    running = wait_running(run["run_id"], run["user_id"])
    worker_id = containers(service)[0]
    stopped_at = datetime.now().isoformat()
    run_cmd(["docker", "kill", worker_id], timeout=30)
    make_stale(run["run_id"])
    repaired = agent_run_maintenance.repair_stale(timeout_minutes=1)
    scale(service, 1)
    restored_at = datetime.now().isoformat()
    final = task_store.get_run(run["run_id"], run["user_id"], include_legacy=False) or {}
    started_removed = cleanup_acceptance_started(queue_name)
    depth = queue_depth(queue_name)
    artifacts = artifact_count(run["run_id"])
    return {
        "queue": queue_name,
        "consumer": service,
        "note": expected_note,
        "run_id": run["run_id"],
        "job_id": job_id,
        "stopped_worker": worker_id[:12],
        "stopped_at": stopped_at,
        "restored_at": restored_at,
        "initial_row_version": running.get("row_version"),
        "final_row_version": final.get("row_version"),
        "final_status": final.get("status"),
        "error_queryable": bool(final.get("error")),
        "artifact_count": artifacts,
        "queue_depth": depth,
        "acceptance_started_removed": started_removed,
        "repair_result": repaired,
        "passed": final.get("status") == "failed" and artifacts == 0 and depth == {"queued": 0, "started": 0},
    }


def zombie_recovery() -> dict[str, Any]:
    stale = new_run("zombie_stale")
    active = new_run("zombie_active")
    completed = new_run("zombie_completed")
    failed = new_run("zombie_failed")
    cancelled = new_run("zombie_cancelled")
    task_store.update_run(completed["run_id"], {"status": "completed", "progress": 100, "result": {"answer": "done", "files": []}}, completed["user_id"])
    task_store.update_run(failed["run_id"], {"status": "failed", "progress": 100, "error": "already failed"}, failed["user_id"])
    task_store.cancel_run(cancelled["run_id"], cancelled["user_id"])
    make_stale(stale["run_id"])
    repaired = agent_run_maintenance.repair_stale(timeout_minutes=1)
    rows = {name: task_store.get_run(run["run_id"], run["user_id"], include_legacy=False) for name, run in {
        "stale": stale,
        "active": active,
        "completed": completed,
        "failed": failed,
        "cancelled": cancelled,
    }.items()}
    statuses = {key: (value or {}).get("status") for key, value in rows.items()}
    return {
        "stale_run_id": stale["run_id"],
        "active_run_id": active["run_id"],
        "repaired": repaired,
        "statuses": statuses,
        "passed": statuses["stale"] == "failed"
        and statuses["active"] == "running"
        and statuses["completed"] == "completed"
        and statuses["failed"] == "failed"
        and statuses["cancelled"] == "cancelled",
    }


def terminal_protection() -> dict[str, Any]:
    run = new_run("terminal_protection")
    task_store.cancel_run(run["run_id"], run["user_id"])
    after_cancel = task_store.update_run(run["run_id"], {"status": "completed", "result": {"answer": "late", "files": []}}, run["user_id"])
    failed = task_store.create_run_from_payload({**run, "run_id": None, "prompt": "terminal failed protection"})
    task_store.update_run(failed["run_id"], {"status": "failed", "error": "terminal"}, failed["user_id"])
    after_failed = task_store.update_run(failed["run_id"], {"status": "running", "progress": 33}, failed["user_id"])
    return {
        "cancelled_run_id": run["run_id"],
        "failed_run_id": failed["run_id"],
        "cancelled_final": (after_cancel or {}).get("status"),
        "failed_final": (after_failed or {}).get("status"),
        "passed": (after_cancel or {}).get("status") == "cancelled" and (after_failed or {}).get("status") == "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()
    load_env()
    started = datetime.now().isoformat()
    original = {"worker-general": len(containers("worker-general")), "worker-video": len(containers("worker-video"))}
    results: list[dict[str, Any]] = []
    try:
        for queue_name in QUEUES:
            results.append(crash_recovery(queue_name))
    finally:
        scale("worker-general", max(4, original.get("worker-general") or 4))
        scale("worker-video", max(2, original.get("worker-video") or 2))
    zombie = zombie_recovery()
    terminal = terminal_protection()
    cleanup_removed = {queue: cleanup_acceptance_started(queue) for queue in QUEUES}
    report = {
        "started_at": started,
        "completed_at": datetime.now().isoformat(),
        "worker_recovery": results,
        "zombie_recovery": zombie,
        "terminal_protection": terminal,
        "acceptance_started_cleanup": cleanup_removed,
        "final_queue_depths": {queue: queue_depth(queue) for queue in QUEUES},
        "passed": all(item["passed"] for item in results) and zombie["passed"] and terminal["passed"],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.json_report else None))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
