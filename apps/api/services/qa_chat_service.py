import os
from typing import Any

from services import deepseek_client, qa_conversation_store, qa_rag_retriever, qa_rag_store
from services.qa_embedding_service import QAEmbeddingError


SYSTEM_MESSAGE = "你是 meizhaiseek 的 AI 问答助手。请优先基于本地知识库内容回答。如果知识库内容不足，请明确说明“本地知识库没有足够信息”，再基于通用知识给出谨慎回答。回答要简洁、清晰，适合电商运营和智能体平台使用场景。"


class QAChatError(RuntimeError):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


def _rag_block(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "无"
    return "\n".join(f"[{index}] {item.get('title') or '本地知识库'}\n{item.get('content') or ''}" for index, item in enumerate(sources, start=1))


def ask(user_id: str, question: str, conversation_id: str | None = None, use_rag: bool = True, top_k: int | None = None) -> dict[str, Any]:
    question = question.strip()
    if not question:
        raise QAChatError("请输入内容。", 400)
    conversation, _user_message = qa_conversation_store.append_user_message(user_id, conversation_id, question)
    warnings: list[str] = []
    sources: list[dict[str, Any]] = []
    if use_rag:
        try:
            if qa_rag_store.count_chunks(user_id) == 0:
                warnings.append("未检索到本地知识库内容，本次回答主要来自模型通用能力。")
            else:
                sources = qa_rag_retriever.search(question, user_id, top_k=top_k)
                if not sources:
                    warnings.append("未检索到本地知识库内容，本次回答主要来自模型通用能力。")
        except QAEmbeddingError:
            warnings.append("本地向量模型不可用，已跳过 RAG 检索。")
    else:
        warnings.append("已关闭 RAG 检索，本次回答主要来自模型通用能力。")

    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": f"用户问题：\n{question}\n\n本地知识库检索结果：\n{_rag_block(sources)}\n\n请基于以上内容回答。"},
    ]
    try:
        answer = deepseek_client.generate_answer(messages)
    except deepseek_client.DeepSeekError as exc:
        qa_conversation_store.append_assistant_message(user_id, conversation["conversation_id"], str(exc), sources=sources, warnings=warnings, status="failed")
        raise QAChatError(str(exc), 502) from exc
    message = qa_conversation_store.append_assistant_message(user_id, conversation["conversation_id"], answer, sources=sources, warnings=warnings, status="completed")
    return {
        "conversation_id": conversation["conversation_id"],
        "message_id": message["message_id"],
        "answer": answer,
        "sources": sources,
        "warnings": warnings,
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
    }


async def async_ask(user_id: str, question: str, conversation_id: str | None = None, use_rag: bool = True, top_k: int | None = None) -> dict[str, Any]:
    question = question.strip()
    if not question:
        raise QAChatError("请输入内容。", 400)
    conversation, _user_message = qa_conversation_store.append_user_message(user_id, conversation_id, question)
    warnings: list[str] = []
    sources: list[dict[str, Any]] = []
    if use_rag:
        try:
            if qa_rag_store.count_chunks(user_id) == 0:
                warnings.append("未检索到本地知识库内容，本次回答主要来自模型通用能力。")
            else:
                sources = qa_rag_retriever.search(question, user_id, top_k=top_k)
                if not sources:
                    warnings.append("未检索到本地知识库内容，本次回答主要来自模型通用能力。")
        except QAEmbeddingError:
            warnings.append("本地向量模型不可用，已跳过 RAG 检索。")
    else:
        warnings.append("已关闭 RAG 检索，本次回答主要来自模型通用能力。")

    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": f"用户问题：\n{question}\n\n本地知识库检索结果：\n{_rag_block(sources)}\n\n请基于以上内容回答。"},
    ]
    try:
        answer = await deepseek_client.async_generate_answer(messages)
    except deepseek_client.DeepSeekError as exc:
        qa_conversation_store.append_assistant_message(user_id, conversation["conversation_id"], str(exc), sources=sources, warnings=warnings, status="failed")
        raise QAChatError(str(exc), 502) from exc
    message = qa_conversation_store.append_assistant_message(user_id, conversation["conversation_id"], answer, sources=sources, warnings=warnings, status="completed")
    return {
        "conversation_id": conversation["conversation_id"],
        "message_id": message["message_id"],
        "answer": answer,
        "sources": sources,
        "warnings": warnings,
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
    }
