import os
from typing import Any

from fastapi import BackgroundTasks

from services import redis_service, task_store


DEFAULT_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "general")
AGENT_QUEUE_BY_TYPE = {
    "video_script_breakdown": "video",
}
CALL_QUEUE_HINTS = {
    "dataset": "dataset",
    "document": "knowledge",
    "knowledge": "knowledge",
    "blueprint": "blueprint",
}


def backend() -> str:
    return os.getenv("TASK_QUEUE_BACKEND", "inline").lower()


def queue_names() -> list[str]:
    value = os.getenv("RQ_QUEUES") or os.getenv("RQ_QUEUE_NAME") or DEFAULT_QUEUE_NAME
    return [item.strip() for item in value.split(",") if item.strip()]


def _queue_for_agent_run(run_id: str, user_id: str) -> str:
    run = task_store.get_run(run_id, user_id, include_legacy=False) or {}
    return AGENT_QUEUE_BY_TYPE.get(str(run.get("agent_type") or ""), DEFAULT_QUEUE_NAME)


def _queue_for_agent_type(agent_type: str) -> str:
    return AGENT_QUEUE_BY_TYPE.get(agent_type, DEFAULT_QUEUE_NAME)


def _queue_for_call(func_path: str) -> str:
    lowered = func_path.lower()
    for hint, queue_name in CALL_QUEUE_HINTS.items():
        if hint in lowered:
            return queue_name
    return DEFAULT_QUEUE_NAME


def enqueue_agent_run(
    run_id: str,
    user_id: str,
    background_tasks: BackgroundTasks | None = None,
    job_id: str | None = None,
    agent_type: str | None = None,
) -> dict[str, Any]:
    job_id = job_id or f"agent-run-{run_id}"
    if backend() != "redis":
        if background_tasks is not None:
            from services.orchestrator import execute_run
            background_tasks.add_task(execute_run, run_id, user_id)
        else:
            from services.orchestrator import execute_run
            execute_run(run_id, user_id)
        return {"backend": "inline", "job_id": job_id}
    try:
        from rq import Queue
        from rq.job import Job
    except Exception as exc:  # pragma: no cover - dependency is optional in sqlite dev mode
        raise RuntimeError("RQ is required when TASK_QUEUE_BACKEND=redis") from exc
    connection = redis_service.binary_client()
    queue_name = _queue_for_agent_type(agent_type) if agent_type else _queue_for_agent_run(run_id, user_id)
    queue = Queue(queue_name, connection=connection)
    try:
        job = Job.fetch(job_id, connection=connection)
    except Exception:
        job = queue.enqueue("tasks.video_tasks.execute_agent_run", run_id, user_id, job_id=job_id, job_timeout=int(os.getenv("AGENT_RUN_JOB_TIMEOUT_SECONDS", "7200")))
    return {"backend": "redis", "job_id": job.id}


def enqueue_call(func_path: str, args: tuple[Any, ...], job_id: str, background_tasks: BackgroundTasks | None = None, timeout_seconds: int = 3600) -> dict[str, Any]:
    if backend() != "redis":
        module_name, func_name = func_path.rsplit(".", 1)
        def _run_inline() -> None:
            module = __import__(module_name, fromlist=[func_name])
            getattr(module, func_name)(*args)
        if background_tasks is not None:
            background_tasks.add_task(_run_inline)
        else:
            _run_inline()
        return {"backend": "inline", "job_id": job_id}
    try:
        from rq import Queue
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("RQ is required when TASK_QUEUE_BACKEND=redis") from exc
    connection = redis_service.binary_client()
    queue = Queue(_queue_for_call(func_path), connection=connection)
    try:
        from rq.job import Job
        job = Job.fetch(job_id, connection=connection)
    except Exception:
        job = queue.enqueue(func_path, *args, job_id=job_id, job_timeout=timeout_seconds)
    return {"backend": "redis", "job_id": job.id}


def health_check() -> dict[str, Any]:
    if backend() != "redis":
        return {"backend": "inline", "status": "ok", "pending_jobs": 0}
    try:
        from rq import Queue
        queues = [Queue(name, connection=redis_service.binary_client()) for name in ["general", "video", "dataset", "knowledge", "blueprint"]]
        depths = {queue.name: len(queue) for queue in queues}
        return {"backend": "redis", "status": "ok", "pending_jobs": sum(depths.values()), "queues": depths}
    except Exception as exc:
        return {"backend": "redis", "status": "failed", "pending_jobs": None, "error": str(exc)}
