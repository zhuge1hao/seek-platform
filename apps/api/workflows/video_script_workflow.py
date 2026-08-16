from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from services import audit_log_service, debug_payload_service, task_store, video_agent_status_service
from services.artifact_service import allow_artifact_root, register_run_artifacts
from services.local_agent_client import run_video_script_breakdown_protocol
from services.payload_preview_service import PayloadPreviewError, resolve_connector
from services.user_context import artifacts_dir
from services.video_agent_payload_builder import build_video_agent_run_payload
from services.video_breakdown_result_normalizer import normalize_video_breakdown_result


DEFAULT_WORKFLOW_OPTIONS: dict[str, Any] = {
    "export_json": True,
    "export_excel": True,
    "export_keyframes": True,
    "enable_ocr": True,
    "enable_quality_check": True,
    "keep_debug_payload": True,
    "subtitle_region": "bottom",
    "subtitle_regions": ["bottom"],
    "ocr_workers": 6,
    "ocr_threads": 6,
    "output_dir": "",
}

STEP_DEFS = [
    ("validate_input", "Validate input"),
    ("check_connector", "Check local video agent"),
    ("prepare_payload", "Prepare /run payload"),
    ("call_local_agent", "Call local video agent"),
    ("save_debug_payload", "Save Debug Payload"),
    ("normalize_result", "Normalize result"),
    ("collect_artifacts", "Collect artifacts"),
    ("finalize", "Finalize"),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_steps() -> list[dict[str, Any]]:
    return [
        {"step_id": step_id, "title": title, "status": "pending", "started_at": None, "completed_at": None, "message": "", "detail_json": None}
        for step_id, title in STEP_DEFS
    ]


def _steps(run: dict[str, Any]) -> list[dict[str, Any]]:
    steps = run.get("steps")
    return steps if isinstance(steps, list) and steps else _base_steps()


def _user(run: dict[str, Any]) -> dict[str, Any]:
    return {"user_id": run.get("user_id"), "username": run.get("username"), "role": run.get("role")}


def _set_step(run_id: str, user_id: str, step_id: str, status: str, message: str = "", detail: dict[str, Any] | None = None, progress: int | None = None) -> dict[str, Any] | None:
    run = task_store.get_run(run_id, user_id, include_legacy=False)
    if run is None:
        return None
    now = _now()
    steps = _steps(run)
    for step in steps:
        if step.get("step_id") != step_id:
            continue
        step["status"] = status
        step["message"] = message
        if detail is not None:
            step["detail_json"] = detail
        if status == "running" and not step.get("started_at"):
            step["started_at"] = now
        if status in {"completed", "failed", "skipped"}:
            step["completed_at"] = now
        break
    updates: dict[str, Any] = {"steps": steps, "current_step": message or step_id}
    if progress is not None:
        updates["progress"] = progress
    return task_store.update_run(run_id, updates, user_id)


def _workflow_options(run: dict[str, Any]) -> dict[str, Any]:
    return {**DEFAULT_WORKFLOW_OPTIONS, **(run.get("workflow_options") or {})}


def _output_dir_for_run(run_id: str, user_id: str, options: dict[str, Any]) -> Path:
    configured = str(options.get("output_dir") or "").strip()
    return Path(configured) if configured else artifacts_dir(user_id, run_id)


def _local_agent_path(path_value: str | Path, mount_env: str, root_env: str) -> str:
    mount_root = os.getenv(mount_env, "").strip().replace("\\", "/").rstrip("/")
    host_root = os.getenv(root_env, "").strip()
    path_text = str(path_value).replace("\\", "/")
    if mount_root and host_root and (path_text == mount_root or path_text.startswith(f"{mount_root}/")):
        rel = path_text[len(mount_root):].lstrip("/")
        return str(PureWindowsPath(host_root) / PurePosixPath(rel))
    return str(path_value)


def local_agent_output_dir(container_output_dir: Path) -> str:
    return _local_agent_path(container_output_dir, "LOCAL_VIDEO_AGENT_OUTPUT_MOUNT", "LOCAL_VIDEO_AGENT_OUTPUT_ROOT")


def local_agent_video_file(video_file: str) -> str:
    return _local_agent_path(video_file, "LOCAL_VIDEO_AGENT_UPLOAD_MOUNT", "LOCAL_VIDEO_AGENT_UPLOAD_ROOT")


def _is_cancelled(run_id: str, user_id: str) -> bool:
    run = task_store.get_run(run_id, user_id, include_legacy=False)
    if run and run.get("status") == "cancelled":
        task_store.append_log(run_id, "Task cancelled; workflow stopped.", user_id)
        return True
    return False


def _failed_result(error: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "answer": error,
        "summary": {"status": "failed", "execution_mode": "real"},
        "timeline": [],
        "subtitles": [],
        "selling_points": [],
        "proof_frames": [],
        "quality_warnings": [],
        "files": [],
        "steps": steps,
        "raw_preview": "",
        "normalization_warnings": [],
        "error": error,
    }


def _fail(run_id: str, user_id: str, step_id: str, error: str, detail: dict[str, Any] | None = None) -> None:
    if _is_cancelled(run_id, user_id):
        return
    run = _set_step(run_id, user_id, step_id, "failed", error, detail=detail, progress=100) or task_store.get_run(run_id, user_id, include_legacy=False) or {}
    steps = _steps(run)
    debug_payload_service.save_error(run_id, error)
    task_store.append_log(run_id, f"Video breakdown failed: {error}", user_id)
    task_store.update_run(run_id, {"status": "failed", "progress": 100, "current_step": "Failed", "result": _failed_result(error, steps), "error": error, "completed_at": _now()}, user_id)
    audit_log_service.write_log("agent.video.run_failed", "failed", _user(run), run_id, {"error_type": step_id, "step_count": len(steps)}, "workflow")


def run(run_id: str, user_id: str) -> None:
    current = task_store.get_run(run_id, user_id, include_legacy=False)
    if current is None or _is_cancelled(run_id, user_id):
        return

    task_store.update_run(run_id, {"steps": _base_steps(), "started_at": current.get("started_at") or _now()}, user_id)
    audit_log_service.write_log("agent.video.run_started", "success", _user(current), run_id, {"mode": current.get("mode")}, "workflow")

    _set_step(run_id, user_id, "validate_input", "running", "Validating video input", progress=15)
    prompt = (current.get("prompt") or "").strip()
    if not prompt:
        _fail(run_id, user_id, "validate_input", "prompt is required.")
        return
    _set_step(run_id, user_id, "validate_input", "completed", "Video input validated", progress=20)

    _set_step(run_id, user_id, "check_connector", "running", "Checking local video agent", progress=25)
    status = video_agent_status_service.check_status(timeout_seconds=3)
    task_store.append_log(run_id, f"Local video agent status: {status.get('status')}", user_id)
    if status.get("status") in {"disconnected", "disabled"}:
        _fail(run_id, user_id, "check_connector", status.get("error") or status.get("message") or "Local video agent disconnected.", detail=status)
        return
    _set_step(run_id, user_id, "check_connector", "completed", status.get("message") or "Local video agent available", detail=status, progress=30)

    try:
        connector, connector_id = resolve_connector("video_script_breakdown")
    except PayloadPreviewError as exc:
        _fail(run_id, user_id, "check_connector", str(exc))
        return

    current = task_store.get_run(run_id, user_id, include_legacy=False) or current
    options = _workflow_options(current)
    output_path = _output_dir_for_run(run_id, current.get("user_id") or user_id, options)
    output_path.mkdir(parents=True, exist_ok=True)
    output_dir = str(output_path)
    allow_artifact_root(output_dir)
    task_store.update_run(run_id, {"output_dir": output_dir, "workflow_options": options}, user_id)

    _set_step(run_id, user_id, "prepare_payload", "running", "Preparing native /run payload", progress=40)
    payload = build_video_agent_run_payload(current, options, local_agent_output_dir(output_path))
    if payload.get("video_file"):
        payload["video_file"] = local_agent_video_file(str(payload["video_file"]))
    if payload.get("mode") != "mock" and not payload.get("video_file"):
        _fail(run_id, user_id, "validate_input", "video_file is required for shot_text_excel mode.")
        return
    task_store.append_log(run_id, f"Connector: {connector_id or 'environment default'}", user_id)
    task_store.append_log(run_id, f"Run mode: {payload.get('mode')}", user_id)
    _set_step(run_id, user_id, "prepare_payload", "completed", "Native /run payload prepared", detail={"connector_id": connector_id, "payload": payload}, progress=45)

    if _is_cancelled(run_id, user_id):
        return
    _set_step(run_id, user_id, "call_local_agent", "running", "Calling local video agent", progress=60)
    response = run_video_script_breakdown_protocol({**payload, "_debug_user_id": user_id}, run_id=run_id, connector=connector)
    task_store.append_log(run_id, f"Local agent returned: {response.get('status')}", user_id)
    if not response.get("ok"):
        _fail(run_id, user_id, "call_local_agent", response.get("error") or "Local video agent call failed.", detail={"http_status": response.get("http_status")})
        return
    _set_step(run_id, user_id, "call_local_agent", "completed", "Local video agent completed", detail={"http_status": response.get("http_status")}, progress=70)
    _set_step(run_id, user_id, "save_debug_payload", "completed", "Debug Payload saved", progress=76)

    if _is_cancelled(run_id, user_id):
        return
    _set_step(run_id, user_id, "normalize_result", "running", "Normalizing local agent response", progress=80)
    normalized = normalize_video_breakdown_result(response.get("raw") or response, current, output_dir, response.get("files") or [])
    _set_step(run_id, user_id, "normalize_result", "completed", "Local agent response normalized", detail={"summary": normalized.get("summary")}, progress=84)

    _set_step(run_id, user_id, "collect_artifacts", "running", "Collecting output files", progress=88)
    files = list(normalized.get("files") or [])
    if options.get("export_json", True):
        result_path = output_path / "video_breakdown_result.json"
        result_path.write_text(json.dumps({**normalized, "steps": _steps(task_store.get_run(run_id, user_id, include_legacy=False) or {})}, ensure_ascii=False, indent=2), encoding="utf-8")
        files.append({"name": result_path.name, "path": str(result_path), "type": "json", "source": "local_video_agent"})
    registered_files = register_run_artifacts(user_id, run_id, files)
    _set_step(run_id, user_id, "collect_artifacts", "completed", f"Registered {len(registered_files)} output files", detail={"artifact_count": len(registered_files)}, progress=92)

    final_run = task_store.get_run(run_id, user_id, include_legacy=False) or {}
    _set_step(run_id, user_id, "finalize", "running", "Writing final result", progress=99)
    steps = _steps(task_store.get_run(run_id, user_id, include_legacy=False) or final_run)
    result = {**normalized, "files": registered_files, "steps": steps}
    result.setdefault("summary", {})["artifact_count"] = len(registered_files)
    _set_step(run_id, user_id, "finalize", "completed", "Video breakdown completed", progress=100)
    steps = _steps(task_store.get_run(run_id, user_id, include_legacy=False) or final_run)
    result["steps"] = steps
    task_store.append_log(run_id, "Video breakdown completed.", user_id)
    task_store.update_run(run_id, {"status": "completed", "progress": 100, "current_step": "Completed", "result": result, "error": None, "completed_at": _now()}, user_id)
    audit_log_service.write_log("agent.video.run_completed", "success", _user(current), run_id, {"artifact_count": len(registered_files), "step_count": len(steps)}, "workflow")
