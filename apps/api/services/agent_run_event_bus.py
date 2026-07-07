import json
import os
import time
from typing import Any

from services import redis_service, task_store


def backend() -> str:
    return os.getenv("EVENT_BACKEND", "memory").lower()


def _channel(run_id: str) -> str:
    return redis_service.key("events", "agent_run", run_id)


def _summary(run: dict[str, Any]) -> dict[str, Any]:
    return task_store.summarize_run(run) or {"run_id": run.get("run_id"), "status": run.get("status")}


def publish_run_event(run: dict[str, Any]) -> None:
    if backend() != "redis":
        return
    payload = _summary(run)
    redis_service.client().publish(_channel(str(run.get("run_id") or "")), json.dumps(payload, ensure_ascii=False))


def wait_for_event(run_id: str, timeout: float = 2.0) -> dict[str, Any] | None:
    if backend() != "redis":
        return None
    pubsub = redis_service.client().pubsub()
    pubsub.subscribe(_channel(run_id))
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            message = pubsub.get_message(timeout=0.2)
            if message and message.get("type") == "message":
                return json.loads(message.get("data") or "{}")
        return None
    finally:
        pubsub.close()


def health_check() -> dict[str, Any]:
    if backend() != "redis":
        return {"backend": "memory", "status": "ok"}
    redis = redis_service.health_check()
    return {"backend": "redis", "status": redis.get("status", "failed")}
