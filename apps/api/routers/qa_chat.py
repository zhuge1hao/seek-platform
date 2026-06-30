from typing import Any

import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services import audit_log_service, deepseek_client, qa_chat_service, qa_conversation_store, qa_embedding_service, qa_model_diagnostic_service, qa_rag_store, qa_stream_service
from services.auth_service import require_operator_or_admin, require_viewer_or_above


router = APIRouter()


class QAConversationCreate(BaseModel):
    title: str = "新对话"


class QAChatRequest(BaseModel):
    conversation_id: str | None = None
    question: str = Field(..., min_length=1)
    use_rag: bool = True
    top_k: int | None = Field(default=None, ge=1, le=20)


class QAEmbeddingTestRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class QARetrievalTestRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class QADiagnoseRequest(BaseModel):
    question: str = "测试知识库检索"
    run_embedding_test: bool = True
    run_retrieval_test: bool = True
    run_deepseek_config_check: bool = True


@router.get("/qa/health")
def qa_health(_user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    qa_rag_store.init_db()
    return {
        "status": "ok",
        "rag_sqlite_exists": qa_rag_store.db_path().exists(),
        "rag_chunk_count": qa_rag_store.count_chunks(_user["user_id"]),
        "embedding_model_path": qa_embedding_service.embedding_model_path(),
        "deepseek_model": deepseek_client.model_name(),
        "deepseek_configured": deepseek_client.is_configured(),
    }


@router.get("/qa/model-status")
def qa_model_status(request: Request, include_load_check: bool = Query(default=False), user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    result = qa_model_diagnostic_service.model_status(user["user_id"], include_load_check)
    audit_log_service.write_log("qa.model_status.view", "success", user, "qa_model", {"model_path_exists": result["embedding_model"]["exists"], "chunk_count": result["rag"]["current_user_chunk_count"]}, audit_log_service.client_ip(request))
    return result


@router.post("/qa/test-embedding")
def qa_test_embedding(payload: QAEmbeddingTestRequest, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    result = qa_model_diagnostic_service.test_embedding(payload.text.strip())
    audit_log_service.write_log("qa.embedding.test", "success" if result["status"] == "success" else "failed", user, "qa_model", {"text_length": len(payload.text), "status": result["status"]}, audit_log_service.client_ip(request))
    return result


@router.post("/qa/test-retrieval")
def qa_test_retrieval(payload: QARetrievalTestRequest, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    result = qa_model_diagnostic_service.test_retrieval(user["user_id"], payload.question.strip(), payload.top_k)
    audit_log_service.write_log("qa.rag.test_retrieval", "success" if result["status"] == "success" else "failed", user, "qa_rag", {"question_length": len(payload.question), "source_count": result.get("source_count", 0), "status": result["status"]}, audit_log_service.client_ip(request))
    return result


@router.post("/qa/diagnose")
def qa_diagnose(payload: QADiagnoseRequest, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    question = (payload.question or "测试知识库检索").strip() or "测试知识库检索"
    result = qa_model_diagnostic_service.diagnose(user["user_id"], question, payload.run_embedding_test, payload.run_retrieval_test, payload.run_deepseek_config_check)
    audit_log_service.write_log("qa.diagnose", result["status"], user, "qa_diagnose", {"question_length": len(question), "status": result["status"], "check_count": len(result["checks"])}, audit_log_service.client_ip(request))
    return result


@router.get("/qa/conversations")
def list_qa_conversations(limit: int = Query(default=50, ge=1, le=200), user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    return {"conversations": qa_conversation_store.list_conversations(user["user_id"], limit)}


@router.get("/qa/conversations/{conversation_id}")
def get_qa_conversation(conversation_id: str, request: Request, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    conversation = qa_conversation_store.get_conversation(user["user_id"], conversation_id, touch=True)
    if conversation is None:
        raise HTTPException(status_code=404, detail="AI 对话不存在。")
    audit_log_service.write_log("qa.conversation.open", "success", user, conversation_id, {}, audit_log_service.client_ip(request))
    return {"conversation": conversation}


@router.post("/qa/conversations")
def create_qa_conversation(payload: QAConversationCreate, request: Request, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    conversation = qa_conversation_store.create_conversation(user["user_id"], payload.title)
    audit_log_service.write_log("qa.conversation.create", "success", user, conversation["conversation_id"], {}, audit_log_service.client_ip(request))
    return {"conversation_id": conversation["conversation_id"], "title": conversation["title"]}


@router.post("/qa/conversations/{conversation_id}/archive")
def archive_qa_conversation(conversation_id: str, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    conversation = qa_conversation_store.archive_conversation(user["user_id"], conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="AI 对话不存在。")
    audit_log_service.write_log("qa.conversation.archive", "success", user, conversation_id, {}, audit_log_service.client_ip(request))
    return {"conversation": conversation}


@router.post("/qa/chat")
def qa_chat(payload: QAChatRequest, request: Request, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    try:
        result = qa_chat_service.ask(user["user_id"], payload.question, payload.conversation_id, payload.use_rag, payload.top_k)
    except qa_chat_service.QAChatError as exc:
        audit_log_service.write_log("qa.chat.failed", "failed", user, payload.conversation_id or "new", {"question_length": len(payload.question), "model": deepseek_client.model_name()}, audit_log_service.client_ip(request))
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    audit_log_service.write_log("qa.rag.search", "success", user, result["conversation_id"], {"source_count": len(result["sources"])}, audit_log_service.client_ip(request))
    audit_log_service.write_log("qa.chat.ask", "success", user, result["conversation_id"], {"question_length": len(payload.question), "source_count": len(result["sources"]), "model": result["model"]}, audit_log_service.client_ip(request))
    return result


@router.post("/qa/chat/stream")
def qa_chat_stream(payload: QAChatRequest, request: Request, user: dict[str, Any] = Depends(require_viewer_or_above)) -> StreamingResponse:
    if os.getenv("QA_STREAM_ENABLED", "true").lower() not in {"1", "true", "yes", "on"}:
        raise HTTPException(status_code=400, detail="AI 对话流式输出已关闭，请使用非流式问答。")
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="请输入内容。")
    return StreamingResponse(
        qa_stream_service.stream_chat(user, question, payload.conversation_id, payload.use_rag, payload.top_k, audit_log_service.client_ip(request)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
