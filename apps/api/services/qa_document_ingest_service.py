import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from services import qa_document_parser, qa_rag_store, qa_text_splitter
from services.config_backup_service import resolve_runtime_path
from services.qa_embedding_service import QAEmbeddingError, embed_texts
from services.user_context import safe_user_id


class QAIngestError(RuntimeError):
    pass


def _allowed_extensions() -> set[str]:
    raw = os.getenv("RAG_ALLOWED_EXTENSIONS", ".txt,.md,.docx")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _max_bytes() -> int:
    try:
        return max(1, int(os.getenv("RAG_MAX_UPLOAD_MB", "20"))) * 1024 * 1024
    except ValueError:
        return 20 * 1024 * 1024


def _root() -> Path:
    return resolve_runtime_path(os.getenv("RAG_KNOWLEDGE_UPLOAD_DIR", "apps/api/runtime/users"))


def _new_doc_id() -> str:
    return f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "document"
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)


def _save_upload(file: UploadFile, user_id: str, doc_id: str) -> Path:
    safe_name = _safe_filename(file.filename or "document")
    extension = Path(safe_name).suffix.lower()
    if extension not in _allowed_extensions():
        raise QAIngestError("仅支持 txt、md、docx 文档入库。")
    target_dir = _root() / safe_user_id(user_id) / "qa_knowledge" / "uploads" / doc_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"source{extension}"
    total = 0
    try:
        with target.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                total += len(chunk)
                if total > _max_bytes():
                    output.close()
                    target.unlink(missing_ok=True)
                    raise QAIngestError(f"文件超过大小限制，请上传 {os.getenv('RAG_MAX_UPLOAD_MB', '20')}MB 以内的文档。")
                output.write(chunk)
    finally:
        file.file.close()
    return target


def _metadata(file: UploadFile, source_path: Path, chunk_size: int, chunk_overlap: int, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "original_filename": file.filename or source_path.name,
        "file_size": source_path.stat().st_size if source_path.exists() else 0,
        "content_type": file.content_type or "",
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        **(extra or {}),
    }


def ingest_upload(user_id: str, file: UploadFile, title: str | None = None) -> dict[str, Any]:
    doc_id = _new_doc_id()
    source_path = _save_upload(file, user_id, doc_id)
    source_type = source_path.suffix.lower()
    doc_title = (title or Path(file.filename or source_path.name).stem or "知识库文档").strip()[:80]
    chunks: list[dict[str, Any]] = []
    metadata = _metadata(file, source_path, int(os.getenv("RAG_CHUNK_SIZE", "700")), int(os.getenv("RAG_CHUNK_OVERLAP", "100")))
    qa_rag_store.create_document(user_id, doc_id, doc_title, str(source_path), source_type, metadata)
    try:
        text, parser = qa_document_parser.parse_document(source_path)
        chunks = qa_text_splitter.split_text(text)
        embeddings = embed_texts([str(chunk["content"]) for chunk in chunks])
        qa_rag_store.delete_chunks_by_doc(user_id, doc_id)
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = f"chunk_{doc_id}_{chunk['chunk_index']}"
            qa_rag_store.add_chunk(chunk_id, doc_id, int(chunk["chunk_index"]), str(chunk["content"]), embedding, {"user_id": user_id, "parser": parser}, user_id=user_id)
        qa_rag_store.update_document_status(user_id, doc_id, "ready", chunk_count=len(chunks), metadata={"parser": parser})
        return {"doc_id": doc_id, "title": doc_title, "status": "ready", "chunk_count": len(chunks), "message": "文档入库完成"}
    except (QAIngestError, qa_document_parser.QADocumentParseError, QAEmbeddingError, Exception) as exc:
        qa_rag_store.delete_chunks_by_doc(user_id, doc_id)
        qa_rag_store.update_document_status(user_id, doc_id, "failed", chunk_count=0, metadata={"error": str(exc)})
        if isinstance(exc, QAEmbeddingError):
            raise QAIngestError(str(exc)) from exc
        if isinstance(exc, qa_document_parser.QADocumentParseError):
            raise QAIngestError(str(exc)) from exc
        if isinstance(exc, QAIngestError):
            raise
        raise QAIngestError(f"文档入库失败：{exc}") from exc


def reindex(user_id: str, document: dict[str, Any]) -> dict[str, Any]:
    source_path = Path(str(document.get("source_path") or ""))
    if not source_path.exists():
        qa_rag_store.update_document_status(user_id, document["doc_id"], "failed", chunk_count=0, metadata={"error": "源文件不存在，无法重新索引。"})
        raise QAIngestError("源文件不存在，无法重新索引。")
    qa_rag_store.update_document_status(user_id, document["doc_id"], "indexing", chunk_count=0)
    try:
        text, parser = qa_document_parser.parse_document(source_path)
        chunks = qa_text_splitter.split_text(text)
        embeddings = embed_texts([str(chunk["content"]) for chunk in chunks])
        qa_rag_store.delete_chunks_by_doc(user_id, document["doc_id"])
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = f"chunk_{document['doc_id']}_{chunk['chunk_index']}"
            qa_rag_store.add_chunk(chunk_id, document["doc_id"], int(chunk["chunk_index"]), str(chunk["content"]), embedding, {"user_id": user_id, "parser": parser}, user_id=user_id)
        qa_rag_store.update_document_status(user_id, document["doc_id"], "ready", chunk_count=len(chunks), metadata={"parser": parser, "error": ""})
        return {"doc_id": document["doc_id"], "title": document["title"], "status": "ready", "chunk_count": len(chunks), "message": "文档重新索引完成"}
    except Exception as exc:
        qa_rag_store.delete_chunks_by_doc(user_id, document["doc_id"])
        qa_rag_store.update_document_status(user_id, document["doc_id"], "failed", chunk_count=0, metadata={"error": str(exc)})
        raise QAIngestError(str(exc)) from exc
