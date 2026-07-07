import logging
import os
import time
from typing import Any

from fastapi import BackgroundTasks

from schemas.agent_runs import AgentRunCreate
from services import conversation_store, task_store
from services.agent_config_store import get_config
from services.agent_registry import get_agent_by_type
from workflows import (
    competitor_analysis_workflow,
    detail_page_planning_workflow,
    generic_agent_workflow,
    main_image_breakdown_workflow,
    smart_selection_workflow,
    video_script_workflow,
)


logger = logging.getLogger(__name__)


def _submit_timing_enabled() -> bool:
    return os.getenv("AGENT_RUN_SUBMIT_TIMING", "true").lower() in {"1", "true", "yes", "on"}


def start_run(payload: AgentRunCreate, background_tasks: BackgroundTasks, user: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    run = task_store.create_run(payload, user=user)
    after_run_insert = time.perf_counter()
    conversation, _created = conversation_store.attach_run(run)
    after_conversation = time.perf_counter()
    run = task_store.update_run(run["run_id"], {"conversation_id": conversation["conversation_id"]}, run["user_id"]) or run
    after_run_update = time.perf_counter()
    try:
        queue_result = schedule_run(run["run_id"], background_tasks, run["user_id"]) or {}
    except Exception:
        task_store.update_run(
            run["run_id"],
            {"status": "failed", "progress": 100, "current_step": "enqueue failed", "result": None, "error": "task enqueue failed"},
            run["user_id"],
        )
        raise
    after_enqueue = time.perf_counter()
    if _submit_timing_enabled():
        logger.info(
            "agent_run_orchestrator_timing",
            extra={
                "agent_type": payload.agent_type,
                "run_id": run.get("run_id"),
                "conversation_id": conversation.get("conversation_id"),
                "queue_job_id": queue_result.get("job_id"),
                "run_insert_ms": round((after_run_insert - started) * 1000, 3),
                "conversation_attach_ms": round((after_conversation - after_run_insert) * 1000, 3),
                "run_update_ms": round((after_run_update - after_conversation) * 1000, 3),
                "queue_enqueue_ms": round((after_enqueue - after_run_update) * 1000, 3),
                "total_ms": round((after_enqueue - started) * 1000, 3),
            },
        )
    return {
        "run_id": run["run_id"],
        "conversation_id": conversation["conversation_id"],
        "status": run["status"],
        "message": "task created",
        "queue_job_id": queue_result.get("job_id"),
    }


def schedule_run(run_id: str, background_tasks: BackgroundTasks, user_id: str) -> dict[str, Any]:
    from tasks.queue import enqueue_agent_run

    return enqueue_agent_run(run_id, user_id, background_tasks)


def _fail_unsupported(run_id: str, agent_type: str | None, user_id: str) -> None:
    task_store.append_log(run_id, f"unsupported agent_type: {agent_type}", user_id)
    task_store.update_run(
        run_id,
        {
            "status": "failed",
            "progress": 100,
            "current_step": "failed",
            "result": None,
            "error": f"unsupported agent_type: {agent_type}",
        },
        user_id,
    )


def execute_run(run_id: str, user_id: str) -> None:
    run = task_store.get_run(run_id, user_id, include_legacy=False)
    if run is None:
        return

    agent_type = run.get("agent_type")
    task_store.append_log(run_id, f"agent_type: {agent_type}", user_id)
    if get_agent_by_type(agent_type or "") is None and get_config(agent_type or "") is None:
        _fail_unsupported(run_id, agent_type, user_id)
        return

    try:
        if agent_type == "video_script_breakdown":
            video_script_workflow.run(run_id, user_id)
        elif agent_type == "competitor_analysis":
            competitor_analysis_workflow.run(run_id, user_id)
        elif agent_type == "smart_selection":
            smart_selection_workflow.run(run_id, user_id)
        elif agent_type in {"detail_page_planning", "brand_detail_page_planning"}:
            detail_page_planning_workflow.run(run_id, user_id)
        elif agent_type in {"hot_main_image_breakdown", "search_main_image", "main_image_planning"}:
            main_image_breakdown_workflow.run(run_id, user_id)
        else:
            generic_agent_workflow.run(run_id, user_id)
    except Exception as exc:
        task_store.append_log(run_id, f"workflow failed: {type(exc).__name__}", user_id)
        task_store.update_run(run_id, {"status": "failed", "progress": 100, "current_step": "failed", "result": None, "error": str(exc)}, user_id)
