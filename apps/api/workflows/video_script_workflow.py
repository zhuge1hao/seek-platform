from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from schemas.agent_runs import DEFAULT_VIDEO_SCRIPT_MODE
from services import audit_log_service, debug_payload_service, task_store, video_agent_status_service
from services.agent_protocol_parser import normalize_agent_protocol_response
from services.artifact_service import normalize_artifact_files, register_run_artifacts
from services.local_agent_client import run_video_script_breakdown_protocol
from services.payload_preview_service import PayloadPreviewError, resolve_connector
from services.user_context import artifacts_dir


DEFAULT_WORKFLOW_OPTIONS: dict[str, Any] = {
    "shot_cut_strategy": "smart",
    "keep_single_frame_proof": True,
    "compress_repeated_talking": True,
    "subtitle_mode": "white_speech_only",
    "subtitle_regions": ["bottom"],
    "ignore_packaging_text": True,
    "ignore_watermark": True,
    "ignore_disclaimer": True,
    "no_subtitle_audio_transcribe": False,
    "excel_layout": "horizontal_by_shot",
    "embed_shot_images": True,
    "enable_shot_cache": True,
    "enable_ocr_cache": True,
    "enable_quality_check": True,
    "generate_contact_sheet": True,
    "export_excel": True,
    "export_json": True,
    "export_keyframes": True,
    "keep_debug_payload": True,
    "target_frame_budget": 80,
    "ocr_threads": 4,
    "baseline_image_dir": "",
    "previous_excel_path": "",
    "output_dir": "",
}

STEP_DEFS = [
    ("validate_input", "校验视频输入"),
    ("check_connector", "检测本地视频 Agent"),
    ("prepare_payload", "生成 Payload"),
    ("call_local_agent", "调用本地视频 Agent"),
    ("parse_result", "解析返回结果"),
    ("collect_artifacts", "收集输出文件"),
    ("quality_check", "质量检查"),
    ("finalize", "写入结果和会话"),
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
        step["message"] = message or step.get("message") or ""
        if detail is not None:
            step["detail_json"] = detail
        if status == "running" and not step.get("started_at"):
            step["started_at"] = now
        if status in {"completed", "failed", "skipped"}:
            step["completed_at"] = now
        break
    updates: dict[str, Any] = {"steps": steps, "current_step": message or next((title for sid, title in STEP_DEFS if sid == step_id), step_id)}
    if progress is not None:
        updates["progress"] = progress
    return task_store.update_run(run_id, updates, user_id)


def _is_cancelled(run_id: str, user_id: str) -> bool:
    run = task_store.get_run(run_id, user_id, include_legacy=False)
    if run and run.get("status") == "cancelled":
        task_store.append_log(run_id, "检测到任务已取消，停止 workflow。", user_id)
        return True
    return False


def _workflow_options(run: dict[str, Any]) -> dict[str, Any]:
    options = DEFAULT_WORKFLOW_OPTIONS.copy()
    options.update(run.get("workflow_options") or {})
    return options


def _output_dir_for_run(run_id: str, user_id: str, options: dict[str, Any]) -> Path:
    configured = str(options.get("output_dir") or "").strip()
    return Path(configured) if configured else artifacts_dir(user_id, run_id)


def _protocol_payload(run: dict[str, Any], output_dir: str, options: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": run.get("session_id"),
        "user_id": run.get("user_id"),
        "agent_type": "video_script_breakdown",
        "mode": run.get("mode") or DEFAULT_VIDEO_SCRIPT_MODE,
        "prompt": run.get("prompt") or "",
        "video_path": run.get("video_path") or "",
        "video_url": run.get("video_url") or "",
        "output_dir": output_dir,
        "baseline_image_dir": options.get("baseline_image_dir") or "",
        "previous_excel_path": options.get("previous_excel_path") or "",
        "workflow_options": options,
        "options": {key: value for key, value in options.items() if key not in {"baseline_image_dir", "previous_excel_path", "output_dir"}},
    }


def _merge_response_files(response: dict[str, Any], normalized: dict[str, Any]) -> list[dict[str, Any]]:
    files_by_path: dict[str, dict[str, Any]] = {}
    for file in [*normalize_artifact_files(response.get("files") or []), *normalize_artifact_files(normalized.get("files") or [])]:
        path = file.get("path")
        if path:
            files_by_path[path] = file
    return list(files_by_path.values())


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _raw_dict(normalized: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    raw = normalized.get("raw_response") or response.get("raw") or response
    return raw if isinstance(raw, dict) else {}


def _summary(raw: dict[str, Any], normalized: dict[str, Any], files: list[dict[str, Any]]) -> dict[str, Any]:
    summary = raw.get("summary") if isinstance(raw.get("summary"), dict) else normalized.get("summary") or {}
    timeline = _as_list(raw.get("timeline") or raw.get("shots") or raw.get("shot_list"))
    subtitles = _as_list(raw.get("subtitles") or raw.get("ocr_subtitles"))
    selling_points = _as_list(raw.get("selling_points") or raw.get("selling_point_list"))
    warnings = _as_list(raw.get("quality_warnings") or normalized.get("quality_warnings"))
    return {
        "video_name": summary.get("video_name") or raw.get("video_name"),
        "duration_seconds": summary.get("duration_seconds") or raw.get("duration_seconds"),
        "shot_count": summary.get("shot_count") or len(timeline),
        "subtitle_count": summary.get("subtitle_count") or len(subtitles),
        "selling_point_count": summary.get("selling_point_count") or len(selling_points),
        "quality_warning_count": summary.get("quality_warning_count") or len(warnings),
        "file_count": len(files),
        "execution_mode": "mock" if raw.get("mock") else "real",
    }


def _structured_result(normalized: dict[str, Any], response: dict[str, Any], files: list[dict[str, Any]], steps: list[dict[str, Any]], error: str | None = None) -> dict[str, Any]:
    raw = _raw_dict(normalized, response)
    quality_warnings = _as_list(raw.get("quality_warnings") or normalized.get("quality_warnings") or response.get("quality_warnings"))
    return {
        "answer": normalized.get("answer") or response.get("answer") or error or "",
        "summary": _summary(raw, normalized, files),
        "timeline": _as_list(raw.get("timeline") or raw.get("shots") or raw.get("shot_list")),
        "subtitles": _as_list(raw.get("subtitles") or raw.get("ocr_subtitles")),
        "selling_points": _as_list(raw.get("selling_points") or raw.get("selling_point_list")),
        "proof_frames": _as_list(raw.get("proof_frames") or raw.get("keyframes") or raw.get("frames")),
        "quality_warnings": quality_warnings,
        "skill_suggestions": _as_list(raw.get("skill_suggestions") or normalized.get("skill_suggestions")),
        "files": files,
        "steps": steps,
        "raw_response": normalized.get("raw_response") or response.get("raw"),
        "error": error,
    }


def _fail(run_id: str, user_id: str, step_id: str, error: str, detail: dict[str, Any] | None = None) -> None:
    if _is_cancelled(run_id, user_id):
        return
    run = _set_step(run_id, user_id, step_id, "failed", error, detail=detail, progress=100) or task_store.get_run(run_id, user_id, include_legacy=False)
    steps = _steps(run or {})
    result = _structured_result({}, {}, [], steps, error=error)
    debug_payload_service.save_error(run_id, error)
    task_store.append_log(run_id, f"视频拆解任务失败：{error}", user_id)
    task_store.update_run(run_id, {"status": "failed", "progress": 100, "current_step": "执行失败", "result": result, "error": error, "completed_at": _now()}, user_id)
    audit_log_service.write_log("agent.video.run_failed", "failed", _user(run or {}), run_id, {"error_type": step_id, "step_count": len(steps)}, "workflow")


def run(run_id: str, user_id: str) -> None:
    current = task_store.get_run(run_id, user_id, include_legacy=False)
    if current is None or _is_cancelled(run_id, user_id):
        return

    task_store.update_run(run_id, {"steps": _base_steps(), "started_at": current.get("started_at") or _now()}, user_id)
    debug_payload_service.save_request(
        run_id,
        {
            "session_id": current.get("session_id"),
            "user_id": user_id,
            "agent_type": "video_script_breakdown",
            "mode": current.get("mode"),
            "prompt": current.get("prompt"),
            "video_path": current.get("video_path"),
            "video_url": current.get("video_url"),
            "workflow_options": current.get("workflow_options") or {},
        },
        metadata={"agent_type": "video_script_breakdown", "mode": current.get("mode"), "connector_id": "video_script_agent"},
    )
    audit_log_service.write_log("agent.video.run_started", "success", _user(current), run_id, {"mode": current.get("mode")}, "workflow")

    _set_step(run_id, user_id, "validate_input", "running", "正在校验视频输入", progress=15)
    prompt = (current.get("prompt") or "").strip()
    if not prompt:
        _fail(run_id, user_id, "validate_input", "prompt 不能为空。")
        return
    if not (current.get("video_path") or current.get("video_url") or prompt):
        _fail(run_id, user_id, "validate_input", "请提供视频文件、视频链接或本地视频路径。")
        return
    _set_step(run_id, user_id, "validate_input", "completed", "视频输入校验完成", progress=20)

    _set_step(run_id, user_id, "check_connector", "running", "正在检测本地视频 Agent", progress=25)
    status = video_agent_status_service.check_status(timeout_seconds=3)
    task_store.append_log(run_id, f"本地视频 Agent 状态：{status.get('status')}", user_id)
    if status.get("status") in {"disconnected", "disabled"}:
        _fail(run_id, user_id, "check_connector", status.get("error") or status.get("message") or "本地视频拆解 Agent 未连接。", detail=status)
        return
    _set_step(run_id, user_id, "check_connector", "completed", status.get("message") or "本地视频 Agent 可用", detail=status, progress=30)

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
    task_store.update_run(run_id, {"output_dir": output_dir, "workflow_options": options}, user_id)

    _set_step(run_id, user_id, "prepare_payload", "running", "正在生成本地 Agent Payload", progress=40)
    payload = _protocol_payload(current, output_dir=output_dir, options=options)
    if (connector or {}).get("session_id"):
        payload["session_id"] = connector["session_id"]
    task_store.append_log(run_id, f"当前连接器：{connector_id or '环境变量默认配置'}", user_id)
    task_store.append_log(run_id, f"当前拆解模式：{current.get('mode') or DEFAULT_VIDEO_SCRIPT_MODE}", user_id)
    _set_step(run_id, user_id, "prepare_payload", "completed", "Payload 已生成", detail={"connector_id": connector_id, "mode": current.get("mode")}, progress=45)

    if _is_cancelled(run_id, user_id):
        return
    _set_step(run_id, user_id, "call_local_agent", "running", "正在调用本地视频拆解 Agent", progress=60)
    response = run_video_script_breakdown_protocol(payload, run_id=run_id, connector=connector)
    task_store.append_log(run_id, f"本地 Agent 返回状态：{response.get('status')}", user_id)
    if not response.get("ok"):
        _fail(run_id, user_id, "call_local_agent", response.get("error") or "本地视频拆解 Agent 调用失败。", detail={"http_status": response.get("http_status")})
        return
    _set_step(run_id, user_id, "call_local_agent", "completed", "本地视频 Agent 调用完成", detail={"http_status": response.get("http_status")}, progress=70)

    if _is_cancelled(run_id, user_id):
        return
    _set_step(run_id, user_id, "parse_result", "running", "正在解析返回结果", progress=80)
    normalized = normalize_agent_protocol_response(response.get("raw") or response, output_dir=output_dir)
    files = _merge_response_files(response, normalized)
    _set_step(run_id, user_id, "parse_result", "completed", "返回结果解析完成", progress=84)

    _set_step(run_id, user_id, "collect_artifacts", "running", "正在收集输出文件", progress=88)
    draft_result = _structured_result(normalized, response, files, _steps(task_store.get_run(run_id, user_id, include_legacy=False) or {}))
    if options.get("export_json", True):
        result_path = output_path / "video_breakdown_result.json"
        result_path.write_text(json.dumps(draft_result, ensure_ascii=False, indent=2), encoding="utf-8")
        files.append({"name": result_path.name, "path": str(result_path), "type": "json"})
    registered_files = register_run_artifacts(user_id, run_id, files)
    _set_step(run_id, user_id, "collect_artifacts", "completed", f"已登记 {len(registered_files)} 个输出文件", detail={"artifact_count": len(registered_files)}, progress=92)

    _set_step(run_id, user_id, "quality_check", "running", "正在整理质量警告", progress=95)
    warnings = _as_list(normalized.get("quality_warnings") or response.get("quality_warnings"))
    quality_status = "skipped" if not options.get("enable_quality_check", True) else "completed"
    _set_step(run_id, user_id, "quality_check", quality_status, f"质量警告 {len(warnings)} 条", detail={"quality_warning_count": len(warnings)}, progress=97)

    final_run = task_store.get_run(run_id, user_id, include_legacy=False) or {}
    _set_step(run_id, user_id, "finalize", "running", "正在写入结构化结果", progress=99)
    steps = _steps(task_store.get_run(run_id, user_id, include_legacy=False) or final_run)
    result = _structured_result(normalized, response, registered_files, steps)
    _set_step(run_id, user_id, "finalize", "completed", "视频拆解任务完成", progress=100)
    steps = _steps(task_store.get_run(run_id, user_id, include_legacy=False) or final_run)
    result["steps"] = steps
    task_store.append_log(run_id, "视频拆解任务执行完成", user_id)
    task_store.update_run(run_id, {"status": "completed", "progress": 100, "current_step": "执行完成", "result": result, "error": None, "completed_at": _now()}, user_id)
    audit_log_service.write_log("agent.video.run_completed", "success", _user(current), run_id, {"artifact_count": len(registered_files), "step_count": len(steps)}, "workflow")
