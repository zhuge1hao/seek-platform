from typing import Any
from uuid import uuid4

from services import file_preview_service
from services.agent_config_store import get_config
from services.agent_connector_store import get_connector
from services.agent_registry import get_agent_by_type
from services.skill_template_service import get_templates_by_ids
from services.user_context import artifacts_dir
from services.dataset_store import DatasetError, build_dataset_context
from services.video_agent_payload_builder import build_video_agent_run_payload


class PayloadPreviewError(RuntimeError):
    pass


def resolve_connector(agent_type: str, explicit_connector_id: str | None = None) -> tuple[dict[str, Any] | None, str | None]:
    config = get_config(agent_type) or {}
    connector_id = explicit_connector_id or config.get("connector_id")
    if not connector_id:
        return None, None
    connector = get_connector(str(connector_id))
    if connector is None:
        raise PayloadPreviewError(f"当前智能体绑定的本地 Agent 连接器不存在：{connector_id}。")
    if not connector.get("enabled"):
        raise PayloadPreviewError(f"连接器已禁用：{connector_id}。")
    return connector, str(connector_id)


def build_payload(data: dict[str, Any], user: dict[str, Any], explicit_connector_id: str | None = None) -> dict[str, Any]:
    agent_type = str(data.get("agent_type") or "").strip()
    prompt = str(data.get("prompt") or "")
    if not agent_type:
        raise PayloadPreviewError("agent_type 不能为空。")
    config = get_config(agent_type) or {}
    agent = get_agent_by_type(agent_type) or {"agent_type": agent_type, "name": config.get("name") or agent_type, "default_mode": "default"}
    connector, connector_id = resolve_connector(agent_type, explicit_connector_id)
    skill_ids = list(data.get("selected_skill_ids") or config.get("default_skill_ids") or [])
    file_ids = list(data.get("file_ids") or [])
    dataset_ids = list(data.get("dataset_ids") or [])
    if agent_type == "video_script_breakdown" and dataset_ids:
        raise PayloadPreviewError("视频脚本拆解不支持 dataset_ids，请使用视频或链接输入。")
    previews = []
    for file_id in file_ids:
        try:
            previews.append(file_preview_service.preview_file(str(file_id), user_id=user["user_id"]))
        except Exception as exc:
            previews.append({"file_id": file_id, "error": str(exc)})
    output_dir = str(artifacts_dir(user["user_id"]) / f"preview_{uuid4().hex[:10]}")
    try:
        dataset_profiles, dataset_files = build_dataset_context(dataset_ids, user["user_id"], include_all_users=user.get("role") == "admin")
    except DatasetError as exc:
        raise PayloadPreviewError(str(exc)) from exc
    session_id = (connector or {}).get("session_id") or data.get("session_id") or config.get("session_id") or ""
    options = data.get("workflow_options") or config.get("default_options") or agent.get("default_options") or {}
    common = {
        "session_id": session_id,
        "user_id": user["user_id"],
        "agent_type": agent_type,
        "agent_name": config.get("name") or agent.get("name") or agent_type,
        "mode": data.get("mode") or agent.get("default_mode") or "default",
        "prompt": prompt,
        "selected_skills": skill_ids,
        "skill_templates": get_templates_by_ids(skill_ids),
        "file_ids": file_ids,
        "file_previews": previews,
        "dataset_ids": dataset_ids,
        "dataset_profiles": dataset_profiles,
        "dataset_files": dataset_files,
        "link": data.get("link") or "",
        "image_paths": data.get("image_paths") or [],
        "video_path": data.get("video_path") or "",
        "video_url": data.get("video_url") or "",
        "output_dir": output_dir,
        "options": options,
    }
    if agent_type == "video_script_breakdown":
        preview_output_dir = str(options.get("output_dir") or output_dir)
        common = build_video_agent_run_payload({**data, "user_id": user["user_id"]}, options, preview_output_dir)
    return {"connector_id": connector_id, "connector": connector, "payload": common}
