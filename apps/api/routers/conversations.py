from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from schemas.conversations import ConversationCreate, ConversationRename
from services import audit_log_service, conversation_store, task_store
from services.auth_service import require_operator_or_admin, require_viewer_or_above


router = APIRouter()


def _summarize_message(message: dict[str, Any]) -> dict[str, Any]:
    result = message.get("result")
    next_message = dict(message)
    next_message["logs"] = list(message.get("logs") or [])[-5:]
    if isinstance(result, dict):
        fake_run = {
            "run_id": message.get("run_id"),
            "agent_type": "",
            "status": message.get("status"),
            "progress": message.get("progress") or 0,
            "current_step": message.get("current_step") or "",
            "result": result,
            "error": message.get("error"),
            "logs": next_message["logs"],
        }
        summary = task_store.summarize_run(fake_run) or {}
        next_message["result"] = summary.get("result")
        next_message["result_has_more"] = summary.get("result_has_more", False)
    return next_message


@router.get("/conversations")
def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    include_archived: bool = Query(default=False),
    user: dict[str, Any] = Depends(require_viewer_or_above),
) -> dict[str, Any]:
    return {"conversations": conversation_store.list_conversations(user["user_id"], limit, include_archived)}


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    conversation = conversation_store.get_conversation(conversation_id, user["user_id"], include_archived=False, touch=True)
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在或已归档。")
    conversation = dict(conversation)
    messages = [_summarize_message(message) for message in conversation.get("messages") or []]
    conversation["messages"] = messages
    conversation["message_count"] = len(messages)
    warnings: list[str] = []
    runs: list[dict[str, Any]] = []
    for run_id in conversation.get("run_ids") or []:
        run = task_store.get_run(str(run_id), user["user_id"], include_legacy=False)
        if run is not None:
            runs.append(task_store.summarize_run(run) or {})
        else:
            warnings.append(f"任务记录 {run_id} 缺少运行数据。")
    latest_run_id = conversation.get("latest_run_id")
    latest_run = next((run for run in runs if run.get("run_id") == latest_run_id), None)
    if latest_run_id and latest_run is None and not any(str(latest_run_id) in warning for warning in warnings):
        warnings.append("该任务记录缺少运行数据，可重新提交。")
    return {"conversation": conversation, "latest_run": latest_run, "runs": runs, "warnings": warnings}


@router.post("/conversations")
def create_conversation(payload: ConversationCreate, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    conversation = conversation_store.create_conversation(user["user_id"], payload.agent_type.strip(), title=payload.title)
    audit_log_service.write_log("conversation.create", "success", user, conversation["conversation_id"], {}, audit_log_service.client_ip(request))
    return {"conversation": conversation}


@router.post("/conversations/{conversation_id}/rename")
def rename_conversation(conversation_id: str, payload: ConversationRename, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    conversation = conversation_store.rename_conversation(conversation_id, user["user_id"], payload.title)
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在。")
    audit_log_service.write_log("conversation.rename", "success", user, conversation_id, {}, audit_log_service.client_ip(request))
    return {"conversation": conversation}


@router.post("/conversations/{conversation_id}/archive")
def archive_conversation(conversation_id: str, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    conversation = conversation_store.archive_conversation(conversation_id, user["user_id"])
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在。")
    audit_log_service.write_log("conversation.archive", "success", user, conversation_id, {}, audit_log_service.client_ip(request))
    return {"conversation": conversation}
