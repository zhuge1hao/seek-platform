import os
from typing import Any

from services import deepseek_client, qa_embedding_service, qa_rag_retriever, qa_rag_store
from services.qa_embedding_service import QAEmbeddingError


SETUP_HINT = "请将模型放到 ./models/bge-small-zh 或修改 .env 中的 BGE_SMALL_ZH_MODEL_PATH。"


def model_status(user_id: str, include_load_check: bool = False) -> dict[str, Any]:
    embedding = qa_embedding_service.get_model_status(include_load_check)
    sqlite_exists = qa_rag_store.db_path().exists()
    stats = qa_rag_store.get_stats(user_id) if sqlite_exists else {"document_count": 0, "chunk_count": 0, "ready_count": 0, "failed_count": 0}
    deepseek_configured = deepseek_client.is_configured()
    return {
        "status": "ok",
        "embedding_model": embedding,
        "rag": {
            "sqlite_path": os.getenv("RAG_SQLITE_PATH", "apps/api/runtime/rag/rag.sqlite3"),
            "sqlite_exists": sqlite_exists,
            "document_count": stats["document_count"],
            "chunk_count": stats["chunk_count"],
            "ready_document_count": stats["ready_count"],
            "failed_document_count": stats["failed_count"],
            "current_user_document_count": stats["document_count"],
            "current_user_chunk_count": stats["chunk_count"],
        },
        "deepseek": {
            "configured": deepseek_configured,
            "model": deepseek_client.model_name(),
            "base_url_configured": bool(os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()),
            "error": "" if deepseek_configured else "DeepSeek API Key 未配置",
        },
        "warnings": [item for item in [embedding.get("error"), "" if deepseek_configured else "DeepSeek API Key 未配置"] if item],
    }


def test_embedding(text: str) -> dict[str, Any]:
    try:
        return qa_embedding_service.test_embedding(text)
    except QAEmbeddingError as exc:
        return {"status": "failed", "error": str(exc), "setup_hint": SETUP_HINT}


def test_retrieval(user_id: str, question: str, top_k: int = 5) -> dict[str, Any]:
    if qa_rag_store.count_chunks(user_id) == 0:
        return {"status": "success", "question": question, "source_count": 0, "sources": [], "warnings": ["当前知识库没有可检索内容"]}
    try:
        sources = qa_rag_retriever.search(question, user_id, top_k=top_k)
    except QAEmbeddingError as exc:
        return {"status": "failed", "question": question, "source_count": 0, "sources": [], "warnings": [], "error": str(exc), "setup_hint": SETUP_HINT}
    return {
        "status": "success",
        "question": question,
        "source_count": len(sources),
        "sources": [{key: item.get(key) for key in ("doc_id", "chunk_id", "title", "score", "content_preview")} for item in sources],
        "warnings": [] if sources else ["未检索到匹配的本地知识库内容"],
    }


def _check(key: str, label: str, status: str, message: str, suggestion: str = "") -> dict[str, str]:
    return {"key": key, "label": label, "status": status, "message": message, "suggestion": suggestion}


def diagnose(user_id: str, question: str, run_embedding_test: bool = True, run_retrieval_test: bool = True, run_deepseek_config_check: bool = True) -> dict[str, Any]:
    status = model_status(user_id, include_load_check=False)
    embedding = status["embedding_model"]
    rag = status["rag"]
    deepseek = status["deepseek"]
    checks: list[dict[str, str]] = []
    checks.append(_check("embedding_model_path", "bge-small-zh 模型路径", "success" if embedding["exists"] else "failed", "模型目录存在" if embedding["exists"] else "模型目录不存在", "" if embedding["exists"] else SETUP_HINT))
    if run_embedding_test and embedding["exists"]:
        result = test_embedding("测试中文向量生成")
        checks.append(_check("embedding", "Embedding 生成", "success" if result["status"] == "success" else "failed", f"Embedding 维度 {result.get('dimension')}" if result["status"] == "success" else str(result.get("error") or "Embedding 失败"), result.get("setup_hint", "")))
    checks.append(_check("sqlite", "SQLite RAG 数据库", "success" if rag["sqlite_exists"] else "warning", "SQLite 可访问" if rag["sqlite_exists"] else "SQLite 文件尚未创建", "上传知识库文档后会自动创建 SQLite。"))
    checks.append(_check("rag_chunks", "知识库 Chunk", "success" if rag["current_user_chunk_count"] > 0 else "warning", f"当前用户知识库 chunk 数为 {rag['current_user_chunk_count']}", "" if rag["current_user_chunk_count"] else "请先上传 txt/md/docx 文档并完成入库。"))
    if run_retrieval_test:
        retrieval = test_retrieval(user_id, question)
        checks.append(_check("retrieval", "RAG 检索", "success" if retrieval["status"] == "success" and retrieval["source_count"] > 0 else ("failed" if retrieval["status"] == "failed" else "warning"), f"检索返回 {retrieval.get('source_count', 0)} 条 sources" if retrieval["status"] == "success" else str(retrieval.get("error") or "检索失败"), retrieval.get("setup_hint", "") or ("" if retrieval.get("source_count") else "请先确认模型可用并完成知识库入库。")))
    if run_deepseek_config_check:
        checks.append(_check("deepseek", "DeepSeek 配置", "success" if deepseek["configured"] else "warning", "DeepSeek API Key 已配置" if deepseek["configured"] else "DeepSeek API Key 未配置", "" if deepseek["configured"] else "请在 .env 中设置 DEEPSEEK_API_KEY。"))
    final = "success"
    if any(item["status"] == "failed" for item in checks):
        final = "failed"
    elif any(item["status"] == "warning" for item in checks):
        final = "warning"
    problems = [item["message"] for item in checks if item["status"] != "success"]
    summary = "当前 RAG 状态正常。" if final == "success" else f"当前 RAG 需要处理：{'，'.join(problems)}。"
    return {"status": final, "summary": summary, "checks": checks}
