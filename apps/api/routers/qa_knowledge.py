from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile

from services import audit_log_service, qa_document_ingest_service, qa_knowledge_service
from services.auth_service import require_operator_or_admin, require_viewer_or_above
from tasks.queue import backend as queue_backend, enqueue_call


router = APIRouter()


def _summary(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "doc_id": document.get("doc_id"),
        "title": document.get("title"),
        "source_type": document.get("source_type"),
        "status": document.get("status"),
        "chunk_count": document.get("chunk_count") or 0,
        "created_at": document.get("created_at"),
        "updated_at": document.get("updated_at"),
    }


@router.post("/qa/knowledge/upload")
def upload_knowledge_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    user: dict[str, Any] = Depends(require_operator_or_admin),
) -> dict[str, Any]:
    try:
        if queue_backend() == "redis":
            document = qa_document_ingest_service.prepare_upload(user["user_id"], file, title)
            doc_id = document["doc_id"]
            enqueue_call(
                "tasks.knowledge_tasks.execute_document_ingest",
                (doc_id, user["user_id"]),
                job_id=f"document_ingest:{doc_id}",
                background_tasks=background_tasks,
                timeout_seconds=1800,
            )
            audit_log_service.write_log(
                "qa.knowledge.enqueue",
                "success",
                user,
                doc_id,
                {"title": document["title"], "status": "pending"},
                audit_log_service.client_ip(request),
            )
            return {**document, "status": "pending", "job_id": f"document_ingest:{doc_id}"}
        result = qa_document_ingest_service.ingest_upload(user["user_id"], file, title)
    except qa_document_ingest_service.QAIngestError as exc:
        audit_log_service.write_log("qa.knowledge.failed", "failed", user, "upload", {"title": title or file.filename, "status": "failed"}, audit_log_service.client_ip(request))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit_log_service.write_log("qa.knowledge.upload", "success", user, result["doc_id"], {"title": result["title"], "chunk_count": result["chunk_count"], "status": result["status"]}, audit_log_service.client_ip(request))
    return result


@router.get("/qa/knowledge/documents")
def list_knowledge_documents(user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    return {"documents": [_summary(item) for item in qa_knowledge_service.list_documents(user["user_id"])]}


@router.get("/qa/knowledge/documents/{doc_id}")
def get_knowledge_document(doc_id: str, request: Request, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    detail = qa_knowledge_service.get_document_detail(user["user_id"], doc_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="knowledge document not found")
    audit_log_service.write_log("qa.knowledge.view", "success", user, doc_id, {}, audit_log_service.client_ip(request))
    detail["document"] = _summary(detail["document"])
    return detail


@router.delete("/qa/knowledge/documents/{doc_id}")
def delete_knowledge_document(doc_id: str, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    document = qa_knowledge_service.delete_document(user["user_id"], doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="knowledge document not found")
    audit_log_service.write_log("qa.knowledge.delete", "success", user, doc_id, {"title": document.get("title"), "status": "deleted"}, audit_log_service.client_ip(request))
    return {"status": "deleted", "document": _summary(document)}


@router.post("/qa/knowledge/documents/{doc_id}/reindex")
def reindex_knowledge_document(doc_id: str, request: Request, background_tasks: BackgroundTasks, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        if queue_backend() == "redis":
            document = qa_knowledge_service.get_document_detail(user["user_id"], doc_id)
            if document is None:
                raise HTTPException(status_code=404, detail="knowledge document not found")
            from services import qa_rag_store

            qa_rag_store.update_document_status(user["user_id"], doc_id, "pending", chunk_count=0)
            job_id = f"document_reindex:{doc_id}"
            enqueue_call(
                "tasks.knowledge_tasks.execute_document_ingest",
                (doc_id, user["user_id"]),
                job_id=job_id,
                background_tasks=background_tasks,
                timeout_seconds=1800,
            )
            audit_log_service.write_log("qa.knowledge.reindex.enqueue", "success", user, doc_id, {"status": "pending", "job_id": job_id}, audit_log_service.client_ip(request))
            return {"doc_id": doc_id, "status": "pending", "job_id": job_id}
        result = qa_knowledge_service.reindex_document(user["user_id"], doc_id)
    except qa_document_ingest_service.QAIngestError as exc:
        audit_log_service.write_log("qa.knowledge.failed", "failed", user, doc_id, {"status": "failed"}, audit_log_service.client_ip(request))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="knowledge document not found")
    audit_log_service.write_log("qa.knowledge.reindex", "success", user, doc_id, {"title": result["title"], "chunk_count": result["chunk_count"], "status": result["status"]}, audit_log_service.client_ip(request))
    return result


@router.get("/qa/knowledge/stats")
def knowledge_stats(user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    return qa_knowledge_service.stats(user["user_id"])
