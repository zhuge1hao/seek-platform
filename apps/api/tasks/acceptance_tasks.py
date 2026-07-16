from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from services import task_store


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def controlled_run(run_id: str, user_id: str, sleep_seconds: int = 10, final_status: str = "completed") -> None:
    run = task_store.get_run(run_id, user_id, include_legacy=False)
    if run is None or run.get("status") == "cancelled":
        return
    task_store.update_run(run_id, {"status": "running", "progress": 25, "current_step": "acceptance task running", "started_at": _now()}, user_id)
    deadline = time.monotonic() + max(0, int(sleep_seconds))
    while time.monotonic() < deadline:
        current = task_store.get_run(run_id, user_id, include_legacy=False)
        if current is None or current.get("status") == "cancelled":
            return
        time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))
    current = task_store.get_run(run_id, user_id, include_legacy=False)
    if current is None or current.get("status") == "cancelled":
        return
    if final_status == "failed":
        task_store.update_run(
            run_id,
            {"status": "failed", "progress": 100, "current_step": "acceptance task failed", "error": "acceptance controlled failure", "completed_at": _now()},
            user_id,
        )
        return
    result: dict[str, Any] = {"answer": "acceptance controlled run completed", "summary": {"status": "completed"}, "files": []}
    task_store.update_run(
        run_id,
        {"status": "completed", "progress": 100, "current_step": "acceptance task completed", "result": result, "error": None, "completed_at": _now()},
        user_id,
    )
