import asyncio
import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from schemas.agent_runs import (
    DEFAULT_VIDEO_SCRIPT_MODE,
    AgentRunCreate,
    AgentRunCreateResponse,
    default_generic_session_id,
    default_video_script_session_id,
)
from services import async_store_utils, audit_log_service, conversation_store, dataset_store, orchestrator, payload_preview_service, task_store
from services.agent_config_store import get_config
from services.agent_registry import get_agent_by_type
from services.auth_service import require_admin, require_operator_or_admin, require_viewer_or_above
from services.user_context import can_access_owner


router = APIRouter()


@router.post("/agent-runs/preview-payload")
def preview_agent_run_payload(payload: AgentRunCreate, request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        result = payload_preview_service.build_payload(payload.model_dump(), user)
    except payload_preview_service.PayloadPreviewError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    audit_log_service.write_log("payload.preview", "success", user, payload.agent_type, {"connector_id": result.get("connector_id")}, audit_log_service.client_ip(request))
    return {"connector_id": result.get("connector_id"), "payload": result["payload"]}


@router.post("/agent-runs", response_model=AgentRunCreateResponse)
def create_agent_run(payload: AgentRunCreate, background_tasks: BackgroundTasks, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, str]:
    agent = get_agent_by_type(payload.agent_type)
    config = get_config(payload.agent_type)
    if agent is None and config is None:
        raise HTTPException(status_code=400, detail=f"不支持的智能体类型：{payload.agent_type}")

    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="prompt 不能为空。")
    dataset_ids = payload.dataset_ids or []
    if payload.agent_type == "video_script_breakdown" and dataset_ids:
        raise HTTPException(status_code=422, detail="视频脚本拆解不支持 dataset_ids，请使用视频或链接输入。")
    try:
        dataset_store.build_dataset_context(dataset_ids, user["user_id"], include_all_users=user.get("role") == "admin")
    except dataset_store.DatasetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if payload.conversation_id and conversation_store.get_conversation(payload.conversation_id, user["user_id"]) is None:
        raise HTTPException(status_code=404, detail="会话不存在。")

    default_mode = (config or agent or {}).get("default_mode") or "default"
    session_id = payload.session_id
    if payload.agent_type == "video_script_breakdown":
        session_id = session_id or default_video_script_session_id()
        default_mode = DEFAULT_VIDEO_SCRIPT_MODE
    else:
        session_id = session_id or (config or {}).get("session_id") or default_generic_session_id()

    normalized_payload = payload.model_copy(
        update={
            "mode": payload.mode or default_mode,
            "prompt": prompt,
            "selected_skill_ids": payload.selected_skill_ids or [],
            "link": payload.link.strip() if payload.link else None,
            "file_ids": payload.file_ids or [],
            "dataset_ids": dataset_ids,
            "image_paths": payload.image_paths or [],
            "video_path": payload.video_path.strip() if payload.video_path else None,
            "video_url": payload.video_url.strip() if payload.video_url else None,
            "session_id": session_id,
            "workflow_options": payload.workflow_options or (config or agent or {}).get("default_options") or {},
        }
    )
    result = orchestrator.start_run(normalized_payload, background_tasks, user)
    if not payload.conversation_id:
        audit_log_service.write_log("conversation.create", "success", user, result["conversation_id"], {"agent_type": payload.agent_type}, audit_log_service.client_ip(request))
    audit_log_service.write_log("conversation.attach_run", "success", user, result["conversation_id"], {"run_id": result["run_id"]}, audit_log_service.client_ip(request))
    audit_log_service.write_log("agent_run.create", "success", user, payload.agent_type, {"run_id": result["run_id"], "dataset_ids": dataset_ids}, audit_log_service.client_ip(request))
    if dataset_ids:
        audit_log_service.write_log("agent_run.use_dataset", "success", user, result["run_id"], {"dataset_ids": dataset_ids}, audit_log_service.client_ip(request))
    if payload.agent_type == "video_script_breakdown":
        audit_log_service.write_log("agent.video.submit", "success", user, result["run_id"], {"mode": normalized_payload.mode, "conversation_id": result["conversation_id"]}, audit_log_service.client_ip(request))
    return result


@router.get("/agent-runs")
def list_agent_runs(limit: int = 20, include_legacy: bool = Query(default=False), user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, list[dict]]:
    is_admin = user.get("role") == "admin"
    return {"items": task_store.list_runs(limit, user_id=user["user_id"], include_legacy=bool(include_legacy and is_admin), include_all_users=is_admin)}


def _read_run_or_404(run_id: str, user: dict[str, Any]) -> dict[str, Any]:
    run = task_store.get_run(run_id) if user.get("role") == "admin" else task_store.get_run(run_id, user["user_id"], include_legacy=False)
    if run is None:
        raise HTTPException(status_code=404, detail="任务不存在。")
    if not can_access_owner(user, run.get("user_id")):
        raise HTTPException(status_code=403, detail="当前账号无权访问该任务。")
    return run


async def _async_read_run_or_404(run_id: str, user: dict[str, Any]) -> dict[str, Any]:
    run = await async_store_utils.async_get_run(run_id) if user.get("role") == "admin" else await async_store_utils.async_get_run(run_id, user["user_id"], False)
    if run is None:
        raise HTTPException(status_code=404, detail="任务不存在。")
    if not can_access_owner(user, run.get("user_id")):
        raise HTTPException(status_code=403, detail="当前账号无权访问该任务。")
    return run


@router.get("/agent-runs/{run_id}/summary")
async def get_agent_run_summary(run_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    return await async_store_utils.async_summarize_run(await _async_read_run_or_404(run_id, user)) or {}


@router.get("/agent-runs/{run_id}/result")
async def get_agent_run_result(run_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    run = await _async_read_run_or_404(run_id, user)
    return {
        "run_id": run.get("run_id"),
        "conversation_id": run.get("conversation_id"),
        "agent_type": run.get("agent_type"),
        "status": run.get("status"),
        "result": run.get("result"),
        "error": run.get("error"),
        "artifacts": (run.get("result") or {}).get("files") if isinstance(run.get("result"), dict) else [],
        "updated_at": run.get("updated_at"),
    }


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/agent-runs/{run_id}/events")
async def get_agent_run_events(run_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> StreamingResponse:
    await _async_read_run_or_404(run_id, user)

    async def stream():
        last_payload = ""
        heartbeat_count = 0
        while True:
            run = await _async_read_run_or_404(run_id, user)
            summary = await async_store_utils.async_summarize_run(run) or {}
            payload = json.dumps(summary, ensure_ascii=False, sort_keys=True)
            status = str(summary.get("status") or "")
            if payload != last_payload:
                last_payload = payload
                event = status if status in {"completed", "failed", "cancelled"} else "status"
                yield _sse(event, summary)
                if status in {"completed", "failed", "cancelled"}:
                    break
            else:
                heartbeat_count += 1
                if heartbeat_count >= 8:
                    heartbeat_count = 0
                    yield _sse("heartbeat", {"run_id": run_id, "status": status})
            await asyncio.sleep(2)

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/agent-runs/{run_id}")
def get_agent_run(run_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict:
    return _read_run_or_404(run_id, user)


@router.post("/agent-runs/{run_id}/cancel")
def cancel_agent_run(run_id: str, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict:
    existing = task_store.get_run(run_id) if user.get("role") == "admin" else task_store.get_run(run_id, user["user_id"], include_legacy=False)
    if existing is None or not can_access_owner(user, existing.get("user_id")):
        raise HTTPException(status_code=404, detail="任务不存在。")
    run, error = task_store.cancel_run(run_id, existing.get("user_id"))
    if error == "not_found" or run is None:
        raise HTTPException(status_code=404, detail="任务不存在。")
    if error == "finished":
        raise HTTPException(status_code=400, detail="当前任务已结束，无法取消。")
    audit_log_service.write_log("agent_run.cancel", "success", user, run_id, {}, audit_log_service.client_ip(request))
    return run


@router.post("/agent-runs/{run_id}/retry", response_model=AgentRunCreateResponse)
def retry_agent_run(run_id: str, background_tasks: BackgroundTasks, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, str]:
    existing = task_store.get_run(run_id) if user.get("role") == "admin" else task_store.get_run(run_id, user["user_id"], include_legacy=False)
    if existing is None or not can_access_owner(user, existing.get("user_id")):
        raise HTTPException(status_code=404, detail="任务不存在。")
    run = task_store.clone_run_for_retry(run_id, existing.get("user_id"))
    if run is None:
        raise HTTPException(status_code=404, detail="任务不存在。")
    conversation, _created = conversation_store.attach_run(run, include_user_message=True)
    orchestrator.schedule_run(run["run_id"], background_tasks, run["user_id"])
    audit_log_service.write_log("agent_run.retry", "success", user, run_id, {"new_run_id": run["run_id"]}, audit_log_service.client_ip(request))
    audit_log_service.write_log("conversation.attach_run", "success", user, conversation["conversation_id"], {"run_id": run["run_id"], "retry_of": run_id}, audit_log_service.client_ip(request))
    return {"run_id": run["run_id"], "conversation_id": conversation["conversation_id"], "status": run["status"], "message": "重试任务已创建，正在执行"}
