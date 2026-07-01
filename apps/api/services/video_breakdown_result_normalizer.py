from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from services.artifact_service import normalize_artifact_file, normalize_artifact_files

SKIP_OUTPUT_SCAN_DIRS = {"node_modules", ".git", ".next", "__pycache__", "_artifact_qa", ".pnpm"}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _short_raw(value: Any, limit: int = 5000) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text[:limit] + ("..." if len(text) > limit else "")


def _int(*values: Any) -> int | None:
    for value in values:
        if value in (None, ""):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            match = re.search(r"\d+", str(value))
            if match:
                return int(match.group(0))
    return None


def _path(*values: Any) -> str:
    for value in values:
        if value:
            return str(value)
    return ""


def _lookup(source: dict[str, Any], *keys: str) -> Any:
    lowered = {str(key).lower().replace(" ", "_"): value for key, value in source.items()}
    for key in keys:
        value = lowered.get(key.lower().replace(" ", "_"))
        if value not in (None, ""):
            return value
    return None


def _int_from_text(text: str, *labels: str) -> int | None:
    for label in labels:
        pattern = label.replace(" ", r"\s*")
        match = re.search(rf"{pattern}\D+(\d+)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _path_from_text(text: str, suffix: str) -> str:
    match = re.search(rf"([A-Za-z]:\\[^\r\n]+?{re.escape(suffix)})", text)
    return match.group(1).strip() if match else ""


def _read_report(path_value: str, warnings: list[str]) -> dict[str, Any]:
    if not path_value:
        return {}
    try:
        path = Path(path_value)
        if not path.exists() or not path.is_file():
            warnings.append(f"shot_report not found: {path_value}")
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append(f"shot_report read failed: {exc}")
        return {}


def _target_stem(video_path: str | None) -> str:
    return Path(str(video_path or "")).stem


def _matches_target(path: Path, root: Path, target_stem: str) -> bool:
    if not target_stem:
        return True
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    target = target_stem.lower()
    lowered_parts = [part.lower() for part in parts]
    name = path.name.lower()
    stem = path.stem.lower()
    return (
        target in lowered_parts
        or stem == target
        or name.startswith(f"{target}_")
        or name.startswith(f"{target}.")
        or stem.startswith(f"{target}_")
        or stem.startswith(f"{target}-")
    )


def _files_from_output_dir(output_dir: str, video_path: str | None) -> list[dict[str, Any]]:
    if not output_dir:
        return []
    root = Path(output_dir)
    if not root.exists() or not root.is_dir():
        return []
    allowed = {".xlsx", ".json", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp"}
    target_stem = _target_stem(video_path)
    files: list[dict[str, Any]] = [{
        "name": "folder_manifest.json",
        "path": str(root),
        "type": "folder_manifest",
        "file_type": "folder_manifest",
        "metadata": {"source": "local_video_agent", "original_path": str(root), "target_stem": target_stem},
    }]
    def is_scannable(path: Path) -> bool:
        lowered = [part.lower() for part in path.parts]
        return not any(part in SKIP_OUTPUT_SCAN_DIRS or part.startswith(".") for part in lowered)

    files.extend(
        normalize_artifact_file(str(path))
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in allowed and is_scannable(path) and _matches_target(path, root, target_stem)
    )
    return files


def _timeline_from_report(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _as_list(report.get("timeline") or report.get("shots") or report.get("optimized_shots")) if isinstance(item, dict)]


def _proof_frames_from_timeline(timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for item in timeline:
        frame = item.get("evidence_frame") or item.get("frame_path")
        if frame:
            frames.append({"shot_id": item.get("shot_id"), "time": item.get("representative_time"), "path": frame, "preview_url": normalize_artifact_file(str(frame)).get("download_url")})
    return frames


def normalize_video_breakdown_result(raw_response: Any, run: dict[str, Any], output_dir: str, files: list[dict[str, Any]]) -> dict[str, Any]:
    raw_text = str(raw_response) if not isinstance(raw_response, dict) else ""
    raw = raw_response if isinstance(raw_response, dict) else {"text": raw_text}
    data = _as_dict(raw.get("data"))
    shot_result = _as_dict(data.get("shot_result"))
    excel_result = _as_dict(data.get("excel_result"))
    explicit_files = normalize_artifact_files(raw.get("artifacts") or raw.get("files") or [])

    excel_path = _path(data.get("excel_file"), excel_result.get("excel"), _lookup(raw, "excel_path", "Excel", "xlsx path"), _path_from_text(raw_text, ".xlsx"))
    shot_report_path = _path(data.get("shot_report"), excel_result.get("report"), shot_result.get("model_optimized_shot_report"), _lookup(raw, "shot_report", "report_path", "shot_report_path"), _path_from_text(raw_text, "model_optimized_shot_report.json"))
    warnings = [str(item) for item in _as_list(raw.get("warnings"))]
    report = _read_report(shot_report_path, warnings)
    timeline = _timeline_from_report(report)
    proof_frames = _proof_frames_from_timeline(timeline)

    merged: dict[str, dict[str, Any]] = {}
    video_path = data.get("video_file") or run.get("video_path")
    for item in [*files, *explicit_files, *_files_from_output_dir(data.get("output_dir") or output_dir, video_path)]:
        path = item.get("path")
        if path:
            merged[str(path)] = item
    if excel_path:
        merged.setdefault(excel_path, normalize_artifact_file(excel_path, file_type="excel"))
    if shot_report_path:
        merged.setdefault(shot_report_path, normalize_artifact_file(shot_report_path, file_type="json", name=Path(shot_report_path).name))
    normalized_files = list(merged.values())

    summary = {
        "video_name": Path(str(video_path or "")).name or None,
        "video_path": video_path,
        "status": raw.get("status") or "completed",
        "raw_shot_count": _int(report.get("source_candidate_count"), shot_result.get("shot_count"), shot_result.get("raw_shot_count"), _lookup(raw, "raw_shot_count", "raw shot count", "rawShotCount"), _int_from_text(raw_text, "raw shot count")),
        "model_optimized_shot_count": _int(report.get("optimized_shot_count"), data.get("model_optimized_shots"), _lookup(raw, "model_optimized_shots", "optimized_shots", "model optimized shots"), excel_result.get("columns"), _int_from_text(raw_text, "model optimized shots", "optimized shots"), len(timeline) if timeline else None),
        "excel_column_count": _int(excel_result.get("columns"), _lookup(raw, "excel_column_count", "Excel columns"), _int_from_text(raw_text, "Excel columns")),
        "excel_image_count": _int(excel_result.get("images"), _lookup(raw, "excel_image_count", "Excel images"), _int_from_text(raw_text, "images")),
        "artifact_count": len(normalized_files),
        "excel_path": excel_path,
        "shot_report_path": shot_report_path,
        "execution_mode": "mock" if data.get("mode") == "mock" or raw.get("summary") == "mock run completed" else "real",
    }
    missing = [key for key in ("excel_path", "shot_report_path") if not summary.get(key)]
    if missing:
        warnings.append(f"missing fields: {', '.join(missing)}")

    return {
        "answer": raw.get("summary") or ("mock run completed" if summary["execution_mode"] == "mock" else "video breakdown completed"),
        "summary": summary,
        "timeline": timeline,
        "subtitles": _as_list(report.get("subtitles") or report.get("ocr_text")),
        "selling_points": [],
        "proof_frames": proof_frames,
        "quality_warnings": [*warnings, *[str(item) for item in _as_list(report.get("warnings"))]],
        "skill_suggestions": [],
        "files": normalized_files,
        "raw_preview": _short_raw(raw),
        "normalization_warnings": warnings,
        "raw_response": raw,
        "error": raw.get("error"),
    }


if __name__ == "__main__":
    result = normalize_video_breakdown_result({"status": "completed", "data": {"excel_result": {"columns": 45, "images": 45}}}, {"video_path": "1.mp4"}, "", [])
    assert result["summary"]["excel_column_count"] == 45
