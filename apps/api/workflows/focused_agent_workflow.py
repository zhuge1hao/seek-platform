from pathlib import Path
from typing import Any

from services import file_preview_service, task_store
from services.agent_config_store import get_config
from services.agent_protocol_parser import normalize_agent_protocol_response
from services.agent_registry import get_agent_by_type
from services.artifact_service import normalize_artifact_files
from services.local_agent_client import run_generic_agent_protocol
from services.payload_preview_service import PayloadPreviewError, resolve_connector
from services.skill_template_service import get_templates_by_ids
from services.user_context import artifacts_dir
from services.dataset_store import DatasetError, build_dataset_context


API_ROOT = Path(__file__).resolve().parents[1]


def _is_cancelled(run_id: str, user_id: str) -> bool:
    run = task_store.get_run(run_id, user_id, include_legacy=False)
    if run and run.get("status") == "cancelled":
        task_store.append_log(run_id, "检测到任务已取消，停止 workflow。", user_id)
        return True
    return False


def _fail(run_id: str, user_id: str, error: str) -> None:
    if _is_cancelled(run_id, user_id):
        return
    task_store.append_log(run_id, f"本地 agent 调用失败：{error}", user_id)
    task_store.update_run(run_id, {"status": "failed", "progress": 100, "current_step": "执行失败", "result": None, "error": error}, user_id)


def _output_dir_for_run(run_id: str, user_id: str) -> Path:
    return artifacts_dir(user_id, run_id)


def _collect_file_previews(run_id: str, file_ids: list[str], user_id: str) -> list[dict[str, Any]]:
    previews: list[dict[str, Any]] = []
    for file_id in file_ids:
        try:
            previews.append(file_preview_service.preview_file(file_id, user_id=user_id))
        except Exception as exc:
            task_store.append_log(run_id, f"文件 {file_id} 预览失败：{exc}", user_id)
            previews.append({"file_id": file_id, "error": str(exc)})
    return previews


def run_focused_workflow(run_id: str, user_id: str, workflow_name: str) -> None:
    current = task_store.get_run(run_id, user_id, include_legacy=False)
    if current is None or _is_cancelled(run_id, user_id):
        return

    task_store.update_run(run_id, {"progress": 20, "current_step": "参数校验完成"}, user_id)
    prompt = (current.get("prompt") or "").strip()
    if not prompt:
        _fail(run_id, user_id, "prompt 不能为空。")
        return

    agent_type = current.get("agent_type") or ""
    agent = get_agent_by_type(agent_type) or {"agent_type": agent_type, "name": agent_type, "default_options": {}}
    config = get_config(agent_type) or {}
    try:
        connector, connector_id = resolve_connector(agent_type)
    except PayloadPreviewError as exc:
        _fail(run_id, user_id, str(exc))
        return

    task_store.update_run(run_id, {"progress": 30, "current_step": "读取智能体配置"}, user_id)
    task_store.append_log(run_id, f"已进入{workflow_name} workflow", user_id)
    task_store.append_log(run_id, f"当前智能体：{config.get('name') or agent.get('name')}", user_id)
    task_store.append_log(run_id, f"当前连接器：{connector_id or '环境变量默认配置'}", user_id)
    task_store.append_log(run_id, f"当前 mode：{(connector or {}).get('mode') or config.get('local_agent_mode') or 'env'}", user_id)
    task_store.append_log(run_id, f"payload_style：{(connector or {}).get('payload_style') or config.get('payload_style') or 'env'}", user_id)
    task_store.append_log(run_id, f"session_id 是否配置：{bool((connector or {}).get('session_id') or current.get('session_id') or config.get('session_id'))}", user_id)

    selected_skill_ids = current.get("selected_skill_ids") or config.get("default_skill_ids") or []
    skill_templates = get_templates_by_ids(selected_skill_ids)
    task_store.append_log(run_id, f"检测到技能模板数量：{len(skill_templates)}", user_id)

    file_previews = _collect_file_previews(run_id, current.get("file_ids") or [], current.get("user_id") or "admin")
    task_store.append_log(run_id, f"检测到文件预览数量：{len(file_previews)}", user_id)
    dataset_ids = current.get("dataset_ids") or []
    try:
        dataset_profiles, dataset_files = build_dataset_context(dataset_ids, current.get("user_id") or user_id)
    except DatasetError as exc:
        _fail(run_id, user_id, str(exc))
        return
    task_store.append_log(run_id, f"检测到清洗数据集数量：{len(dataset_ids)}", user_id)

    output_path = _output_dir_for_run(run_id, current.get("user_id") or "admin")
    output_path.mkdir(parents=True, exist_ok=True)
    output_dir = str(output_path)
    task_store.update_run(run_id, {"output_dir": output_dir, "progress": 40, "current_step": "准备输出目录"}, user_id)
    task_store.append_log(run_id, f"output_dir：{output_dir}", user_id)

    if _is_cancelled(run_id, user_id):
        return

    payload = {
        "session_id": (connector or {}).get("session_id") or current.get("session_id") or config.get("session_id") or "",
        "user_id": current.get("user_id"),
        "agent_type": agent_type,
        "agent_name": config.get("name") or agent.get("name"),
        "mode": current.get("mode") or agent.get("default_mode") or "default",
        "prompt": prompt,
        "selected_skills": selected_skill_ids,
        "skill_templates": skill_templates,
        "link": current.get("link") or "",
        "file_ids": current.get("file_ids") or [],
        "file_previews": file_previews,
        "dataset_ids": dataset_ids,
        "dataset_profiles": dataset_profiles,
        "dataset_files": dataset_files,
        "image_paths": current.get("image_paths") or [],
        "video_path": current.get("video_path") or "",
        "video_url": current.get("video_url") or "",
        "output_dir": output_dir,
        "options": current.get("workflow_options") or config.get("default_options") or agent.get("default_options") or {},
    }

    task_store.update_run(run_id, {"progress": 60, "current_step": "正在调用本地 agent"}, user_id)
    task_store.append_log(run_id, "正在调用本地 agent", user_id)
    response = run_generic_agent_protocol(payload, run_id=run_id, connector=connector)

    if _is_cancelled(run_id, user_id):
        return

    task_store.append_log(run_id, f"本地 agent 返回状态：{response.get('status')}", user_id)
    if not response.get("ok"):
        _fail(run_id, user_id, response.get("error") or "本地 agent 调用失败。")
        return

    task_store.update_run(run_id, {"progress": 80, "current_step": "正在解析返回结果"}, user_id)
    normalized = normalize_agent_protocol_response(response.get("raw") or response, output_dir=output_dir)
    files_by_path: dict[str, dict[str, str]] = {}
    for file in [*normalize_artifact_files(response.get("files") or []), *normalize_artifact_files(normalized.get("files") or [])]:
        path = file.get("path")
        if path:
            files_by_path[path] = file

    files = list(files_by_path.values())
    task_store.append_log(run_id, "本地 agent 返回完成", user_id)
    task_store.append_log(run_id, f"检测到文件数量：{len(files)}", user_id)

    if _is_cancelled(run_id, user_id):
        return

    task_store.update_run(run_id, {"progress": 90, "current_step": "正在整理输出文件"}, user_id)
    result = {
        "answer": normalized.get("answer") or response.get("answer") or "",
        "summary": normalized.get("summary") or response.get("summary") or {},
        "files": files,
        "quality_warnings": normalized.get("quality_warnings") or response.get("quality_warnings") or [],
        "skill_suggestions": normalized.get("skill_suggestions") or response.get("skill_suggestions") or [],
        "raw_response": normalized.get("raw_response"),
    }

    task_store.append_log(run_id, "任务执行完成", user_id)
    task_store.update_run(run_id, {"status": "completed", "progress": 100, "current_step": "执行完成", "result": result, "error": None}, user_id)
