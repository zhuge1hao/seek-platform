import json
import math
import os
from typing import Any

from services import qa_rag_store
from services.qa_embedding_service import embed_text


def _top_k(value: int | None = None) -> int:
    return max(1, min(int(value or os.getenv("RAG_TOP_K", "5")), 20))


def _threshold() -> float:
    try:
        return float(os.getenv("RAG_SCORE_THRESHOLD", "0.25"))
    except ValueError:
        return 0.25


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _embedding(value: str | None) -> list[float] | None:
    try:
        data = json.loads(value or "[]")
    except json.JSONDecodeError:
        return None
    return [float(item) for item in data] if isinstance(data, list) else None


def search(question: str, user_id: str, top_k: int | None = None, score_threshold: float | None = None) -> list[dict[str, Any]]:
    chunks = qa_rag_store.list_chunks(user_id)
    if not chunks:
        return []
    query = embed_text(question)
    threshold = _threshold() if score_threshold is None else score_threshold
    scored: list[dict[str, Any]] = []
    for chunk in chunks:
        embedding = _embedding(chunk.get("embedding_json"))
        if not embedding:
            continue
        score = _cosine(query, embedding)
        if score < threshold:
            continue
        content = str(chunk.get("content") or "")
        scored.append({
            "chunk_id": chunk.get("chunk_id"),
            "doc_id": chunk.get("doc_id"),
            "title": chunk.get("title") or "本地知识库",
            "content": content[:1200],
            "content_preview": content[:300],
            "score": round(score, 4),
            "metadata": chunk.get("metadata") or {},
        })
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[: _top_k(top_k)]
