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


def start_run(payload: AgentRunCreate, background_tasks: BackgroundTasks, user: dict[str, Any]) -> dict[str, str]:
    run = task_store.create_run(payload, user=user)
    conversation, _created = conversation_store.attach_run(run)
    run = task_store.update_run(run["run_id"], {"conversation_id": conversation["conversation_id"]}, run["user_id"]) or run
    schedule_run(run["run_id"], background_tasks, run["user_id"])
    return {"run_id": run["run_id"], "conversation_id": conversation["conversation_id"], "status": run["status"], "message": "任务已创建，正在执行"}


def schedule_run(run_id: str, background_tasks: BackgroundTasks, user_id: str) -> None:
    background_tasks.add_task(execute_run, run_id, user_id)


def _fail_unsupported(run_id: str, agent_type: str | None, user_id: str) -> None:
    task_store.append_log(run_id, "不支持的智能体类型", user_id)
    task_store.update_run(
        run_id,
        {
            "status": "failed",
            "progress": 100,
            "current_step": "执行失败",
            "result": None,
            "error": f"不支持的智能体类型：{agent_type}",
        }, user_id,
    )


def execute_run(run_id: str, user_id: str) -> None:
    run = task_store.get_run(run_id, user_id, include_legacy=False)
    if run is None:
        return

    agent_type = run.get("agent_type")
    task_store.append_log(run_id, f"当前 agent_type：{agent_type}", user_id)
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
        task_store.append_log(run_id, f"workflow 执行失败：{exc}", user_id)
        task_store.update_run(run_id, {"status": "failed", "progress": 100, "current_step": "执行失败", "result": None, "error": str(exc)}, user_id)
