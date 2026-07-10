import json
import os
import time
from typing import Any, Iterator

from services import audit_log_service, deepseek_client, qa_conversation_store, qa_rag_retriever, qa_rag_store
from services.qa_embedding_service import QAEmbeddingError


SYSTEM_MESSAGE = (
    "你是 meizhaiseek 的 AI 问答助手。请优先基于本地知识库内容回答。"
    "如果知识库内容不足，请明确说明“本地知识库没有足够信息”，再基于通用知识给出谨慎回答。"
    "回答要简洁、清晰，适合电商运营和智能体平台使用场景。"
)


def _event(name: str, data: dict[str, Any]) -> str:
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _rag_block(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "无"
    return "\n".join(
        f"[{index}] {item.get('title') or '本地知识库'}\n{item.get('content') or item.get('content_preview') or ''}"
        for index, item in enumerate(sources, start=1)
    )


def _messages(question: str, sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {
            "role": "user",
            "content": (
                f"用户问题：\n{question}\n\n"
                f"本地知识库检索结果：\n{_rag_block(sources)}\n\n"
                "请基于以上内容回答。"
            ),
        },
    ]


def stream_chat(
    user: dict[str, Any],
    question: str,
    conversation_id: str | None = None,
    use_rag: bool = True,
    top_k: int | None = None,
    client_ip: str = "",
) -> Iterator[str]:
    question = question.strip()
    conversation, _user_message = qa_conversation_store.append_user_message(user["user_id"], conversation_id, question)
    conversation_id = str(conversation["conversation_id"])
    assistant = qa_conversation_store.create_assistant_message(user["user_id"], conversation_id, "streaming")
    message_id = str(assistant["message_id"])
    answer_parts: list[str] = []
    sources: list[dict[str, Any]] = []
    warnings: list[str] = []
    completed = False
    started_at = time.monotonic()
    try:
        audit_log_service.write_log(
            "qa.chat.stream.start",
            "success",
            user,
            conversation_id,
            {"question_length": len(question), "model": deepseek_client.model_name()},
            client_ip,
        )
        yield _event("start", {"conversation_id": conversation_id, "message_id": message_id})
        yield _event("retrieval_start", {"message": "正在检索本地知识库"})

        if use_rag:
            try:
                if qa_rag_store.count_chunks(user["user_id"]) == 0:
                    warnings.append("未检索到本地知识库内容，本次回答主要来自模型通用能力。")
                else:
                    sources = qa_rag_retriever.search(question, user["user_id"], top_k=top_k)
                    if not sources:
                        warnings.append("未检索到本地知识库内容，本次回答主要来自模型通用能力。")
            except QAEmbeddingError:
                warnings.append("本地向量模型不可用，已跳过 RAG 检索。")
        else:
            warnings.append("已关闭 RAG 检索，本次回答主要来自模型通用能力。")

        qa_conversation_store.update_assistant_message(user["user_id"], conversation_id, message_id, sources=sources, warnings=warnings, status="streaming")
        yield _event("sources", {"sources": sources, "warnings": warnings})

        max_seconds = max(1, int(os.getenv("QA_STREAM_MAX_SECONDS", "120") or "120"))
        for delta in deepseek_client.stream_answer(_messages(question, sources)):
            if time.monotonic() - started_at > max_seconds:
                raise deepseek_client.DeepSeekError("流式回答超时，请稍后重试。")
            answer_parts.append(delta)
            yield _event("delta", {"text": delta})

        answer = "".join(answer_parts).strip()
        qa_conversation_store.update_assistant_message(user["user_id"], conversation_id, message_id, content=answer, sources=sources, warnings=warnings, status="completed")
        audit_log_service.write_log(
            "qa.chat.stream.done",
            "success",
            user,
            conversation_id,
            {"question_length": len(question), "source_count": len(sources), "model": deepseek_client.model_name(), "status": "completed"},
            client_ip,
        )
        completed = True
        yield _event("done", {"answer": answer, "conversation_id": conversation_id, "message_id": message_id})
    except GeneratorExit:
        partial = "".join(answer_parts).strip()
        qa_conversation_store.update_assistant_message(user["user_id"], conversation_id, message_id, content=partial, sources=sources, warnings=warnings, status="stopped", error="用户已停止生成。")
        audit_log_service.write_log("qa.chat.stream.stopped", "stopped", user, conversation_id, {"source_count": len(sources), "status": "stopped"}, client_ip)
        raise
    except Exception as exc:
        error = str(exc)
        partial = "".join(answer_parts).strip() or error
        qa_conversation_store.update_assistant_message(user["user_id"], conversation_id, message_id, content=partial, sources=sources, warnings=warnings, status="failed", error=error)
        audit_log_service.write_log(
            "qa.chat.stream.failed",
            "failed",
            user,
            conversation_id,
            {"question_length": len(question), "source_count": len(sources), "model": deepseek_client.model_name(), "status": "failed"},
            client_ip,
        )
        yield _event("error", {"error": error, "conversation_id": conversation_id, "message_id": message_id})
    finally:
        if not completed and answer_parts:
            pass
