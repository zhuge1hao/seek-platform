from typing import Any

from services import qa_document_ingest_service, qa_embedding_service, qa_rag_store


def list_documents(user_id: str) -> list[dict[str, Any]]:
    return qa_rag_store.list_documents(user_id)


def get_document_detail(user_id: str, doc_id: str) -> dict[str, Any] | None:
    document = qa_rag_store.get_document(doc_id, user_id)
    if document is None:
        return None
    previews = [
        {
            "chunk_id": chunk.get("chunk_id"),
            "chunk_index": chunk.get("chunk_index"),
            "content_preview": str(chunk.get("content") or "")[:200],
            "created_at": chunk.get("created_at"),
        }
        for chunk in qa_rag_store.list_chunks(user_id)
        if chunk.get("doc_id") == doc_id
    ][:10]
    return {"document": document, "chunks_preview": previews}


def delete_document(user_id: str, doc_id: str) -> dict[str, Any] | None:
    return qa_rag_store.delete_document(user_id, doc_id)


def reindex_document(user_id: str, doc_id: str) -> dict[str, Any] | None:
    document = qa_rag_store.get_document(doc_id, user_id)
    if document is None:
        return None
    return qa_document_ingest_service.reindex(user_id, document)


def stats(user_id: str) -> dict[str, Any]:
    return {**qa_rag_store.get_stats(user_id), "embedding_model_path": qa_embedding_service.embedding_model_path()}
