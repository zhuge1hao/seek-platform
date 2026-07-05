from __future__ import annotations

import asyncio
import threading
import time
from typing import Any


_CONDITION = threading.Condition()
_LATEST: dict[str, tuple[int, dict[str, Any]]] = {}
_SEQUENCE = 0


def publish_run_event(run: dict[str, Any]) -> None:
    run_id = str(run.get("run_id") or "")
    if not run_id:
        return
    event = {
        "run_id": run_id,
        "status": run.get("status"),
        "progress": run.get("progress"),
        "current_step": run.get("current_step"),
        "updated_at": run.get("updated_at"),
    }
    global _SEQUENCE
    with _CONDITION:
        _SEQUENCE += 1
        _LATEST[run_id] = (_SEQUENCE, event)
        _CONDITION.notify_all()


def latest_sequence(run_id: str) -> int:
    with _CONDITION:
        item = _LATEST.get(run_id)
        return int(item[0]) if item else 0


def _wait_for_event(run_id: str, after_sequence: int, timeout: float) -> tuple[int, dict[str, Any]] | None:
    deadline = time.monotonic() + max(0.0, timeout)
    with _CONDITION:
        while True:
            item = _LATEST.get(run_id)
            if item and item[0] > after_sequence:
                return item
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            _CONDITION.wait(remaining)


async def wait_for_event(run_id: str, after_sequence: int, timeout: float = 2.0) -> tuple[int, dict[str, Any]] | None:
    return await asyncio.to_thread(_wait_for_event, run_id, after_sequence, timeout)


def clear_for_test() -> None:
    global _SEQUENCE
    with _CONDITION:
        _LATEST.clear()
        _SEQUENCE = 0
        _CONDITION.notify_all()
