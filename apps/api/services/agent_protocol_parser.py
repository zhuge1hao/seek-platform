import json
from typing import Any

from services.artifact_service import extract_files_from_text, normalize_artifact_files


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _merge_files(*groups: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    for group in groups:
        for file in group:
            path = file.get("path")
            if not path or path in seen:
                continue
            seen.add(path)
            merged.append(file)
    return merged


def _parse_json_text(text: str) -> Any:
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return text


def normalize_agent_protocol_response(raw_response: Any, output_dir: str | None = None) -> dict[str, Any]:
    raw = _parse_json_text(raw_response) if isinstance(raw_response, str) else raw_response

    if isinstance(raw, dict):
        answer = raw.get("answer") or raw.get("message") or raw.get("content") or raw.get("result") or ""
        answer_text = _stringify(answer)
        explicit_files = normalize_artifact_files(raw.get("files") or raw.get("file_path") or [])
        extracted_files = extract_files_from_text(answer_text)
        status = raw.get("status") or "success"

        return {
            "status": status,
            "answer": answer_text,
            "summary": raw.get("summary") or {},
            "files": _merge_files(explicit_files, extracted_files),
            "quality_warnings": raw.get("quality_warnings") or [],
            "skill_suggestions": raw.get("skill_suggestions") or [],
            "raw_response": raw,
        }

    answer_text = _stringify(raw)
    return {
        "status": "success",
        "answer": answer_text,
        "summary": {},
        "files": extract_files_from_text(answer_text),
        "quality_warnings": [],
        "skill_suggestions": [],
        "raw_response": raw,
    }
