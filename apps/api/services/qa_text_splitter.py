import os
import re


def _chunk_size() -> int:
    try:
        return max(100, int(os.getenv("RAG_CHUNK_SIZE", "700")))
    except ValueError:
        return 700


def _chunk_overlap() -> int:
    try:
        return max(0, min(int(os.getenv("RAG_CHUNK_OVERLAP", "100")), _chunk_size() // 2))
    except ValueError:
        return 100


def _paragraphs(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"\n\s*\n|\n(?=#{1,6}\s)|\n", text) if item.strip()]


def split_text(text: str, chunk_size: int | None = None, chunk_overlap: int | None = None) -> list[dict[str, int | str]]:
    size = chunk_size or _chunk_size()
    overlap = chunk_overlap if chunk_overlap is not None else _chunk_overlap()
    chunks: list[str] = []
    current = ""
    for paragraph in _paragraphs(text):
        if len(paragraph) > size:
            if current.strip():
                chunks.append(current.strip())
                current = ""
            start = 0
            while start < len(paragraph):
                chunks.append(paragraph[start:start + size].strip())
                start += max(1, size - overlap)
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= size:
            current = candidate
        else:
            if len(current.strip()) >= 20:
                chunks.append(current.strip())
            prefix = current[-overlap:] if overlap and current else ""
            current = f"{prefix}\n\n{paragraph}".strip()
    if current.strip():
        chunks.append(current.strip())
    if not chunks and text.strip():
        chunks = [text.strip()[:size]]
    return [{"chunk_index": index, "content": chunk, "char_count": len(chunk)} for index, chunk in enumerate(chunks) if len(chunk.strip()) >= 20 or len(chunks) == 1]
