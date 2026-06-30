import json
import os
from pathlib import Path
from typing import Any

from schemas.agent_runs import DEFAULT_VIDEO_SCRIPT_SESSION_ID
from services.config_guard import guard_agent_configs
from services.config_migration_service import wrap_agent_configs
from services.agent_registry import list_agents


API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
HIDDEN_COMPETITOR_AGENT_TYPE = "competitor_analysis"


class ConfigStoreError(RuntimeError):
    pass


def _resolve_store_path() -> Path:
    configured = os.getenv("AGENT_CONFIG_STORE_PATH", "runtime/configs/agent_configs.json")
    path = Path(configured)
    if not path.is_absolute():
        if len(path.parts) >= 2 and path.parts[0] == "apps" and path.parts[1] == "api":
            path = PROJECT_ROOT / path
        else:
            path = API_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _default_skill_ids(agent_type: str) -> list[str]:
    mapping = {
        "smart_selection": ["smart_selection_basic"],
        "detail_page_planning": ["detail_page_10_screen"],
        "brand_detail_page_planning": ["detail_page_10_screen"],
        "hot_main_image_breakdown": ["main_image_breakdown"],
        "search_main_image": ["main_image_breakdown"],
        "main_image_planning": ["main_image_breakdown"],
        "review_analysis": ["review_painpoint_cluster"],
        "qa_analysis": ["review_painpoint_cluster"],
        "title_writing": ["title_writing_basic"],
        HIDDEN_COMPETITOR_AGENT_TYPE: ["competitor_low_cost_ratio"],
    }
    return mapping.get(agent_type, [])


def _workflow_for_agent(agent: dict[str, Any]) -> str:
    agent_type = agent["agent_type"]
    if agent_type == "video_script_breakdown":
        return "video_script_workflow"
    if agent_type == HIDDEN_COMPETITOR_AGENT_TYPE:
        return "competitor_analysis_workflow"
    if agent_type == "smart_selection":
        return "smart_selection_workflow"
    if agent_type in {"detail_page_planning", "brand_detail_page_planning"}:
        return "detail_page_planning_workflow"
    if agent_type in {"hot_main_image_breakdown", "search_main_image", "main_image_planning"}:
        return "main_image_breakdown_workflow"
    return agent.get("workflow") or "generic_agent_workflow"


def _config_from_agent(agent: dict[str, Any], visible: bool = True) -> dict[str, Any]:
    agent_type = agent["agent_type"]
    return {
        "agent_type": agent_type,
        "name": agent["name"],
        "enabled": bool(agent.get("enabled", True)),
        "workflow": _workflow_for_agent(agent),
        "local_agent_mode": os.getenv("LOCAL_AGENT_MODE", "http"),
        "session_id": DEFAULT_VIDEO_SCRIPT_SESSION_ID if agent_type == "video_script_breakdown" else "",
        "payload_style": os.getenv("LOCAL_AGENT_PAYLOAD_STYLE", "protocol"),
        "accepted_inputs": agent.get("accepted_inputs") or ["text"],
        "default_skill_ids": _default_skill_ids(agent_type),
        "output_types": ["text", "xlsx"] if agent_type in {"smart_selection", HIDDEN_COMPETITOR_AGENT_TYPE} else ["text"],
        "default_options": agent.get("default_options") or {},
        "description": agent.get("description") or "",
        "connector_id": "video_script_agent" if agent_type == "video_script_breakdown" else None,
        "visible": visible,
    }


def _default_configs() -> list[dict[str, Any]]:
    configs = [_config_from_agent(agent, visible=True) for agent in list_agents()]
    return configs


def _read_configs() -> list[dict[str, Any]]:
    try:
        return guard_agent_configs(_resolve_store_path(), _default_configs())["items"]
    except Exception as exc:
        raise ConfigStoreError(f"智能体配置读取失败：{exc}") from exc


def _write_configs(configs: list[dict[str, Any]]) -> None:
    _resolve_store_path().write_text(json.dumps(wrap_agent_configs(configs), ensure_ascii=False, indent=2), encoding="utf-8")


def reset_configs() -> list[dict[str, Any]]:
    configs = _default_configs()
    _write_configs(configs)
    return configs


def guard_configs() -> dict[str, Any]:
    return guard_agent_configs(_resolve_store_path(), _default_configs())


def list_configs(include_hidden: bool = False) -> list[dict[str, Any]]:
    configs = _read_configs()
    if include_hidden:
        return configs
    return [config for config in configs if config.get("visible", True)]


def get_config(agent_type: str) -> dict[str, Any] | None:
    return next((config for config in _read_configs() if config.get("agent_type") == agent_type), None)


def update_config(agent_type: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    configs = _read_configs()
    for config in configs:
        if config.get("agent_type") != agent_type:
            continue
        for key, value in updates.items():
            if (value is not None or key == "connector_id") and key in {
                "enabled",
                "workflow",
                "local_agent_mode",
                "session_id",
                "payload_style",
                "accepted_inputs",
                "default_skill_ids",
                "output_types",
                "default_options",
                "description",
                "connector_id",
            }:
                config[key] = value
        if agent_type == "video_script_breakdown" and not config.get("session_id"):
            config["session_id"] = DEFAULT_VIDEO_SCRIPT_SESSION_ID
        if agent_type == "video_script_breakdown" and not config.get("connector_id"):
            config["connector_id"] = "video_script_agent"
        _write_configs(configs)
        return config
    return None
