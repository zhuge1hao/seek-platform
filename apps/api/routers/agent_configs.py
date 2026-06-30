from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from services.agent_config_store import ConfigStoreError, get_config, list_configs, update_config
from services import audit_log_service
from services.auth_service import require_admin, require_viewer_or_above


router = APIRouter()


@router.get("/agent-configs")
def get_agent_configs(_user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, list[dict[str, Any]]]:
    try:
        return {"items": list_configs()}
    except ConfigStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/agent-configs/{agent_type}")
def get_agent_config(agent_type: str, _user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    try:
        config = get_config(agent_type)
    except ConfigStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if config is None:
        raise HTTPException(status_code=404, detail="智能体配置不存在。")
    return config


@router.post("/agent-configs/{agent_type}")
def save_agent_config(agent_type: str, payload: dict[str, Any], request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    previous = get_config(agent_type)
    try:
        config = update_config(agent_type, payload)
    except ConfigStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if config is None:
        raise HTTPException(status_code=404, detail="智能体配置不存在。")
    audit_log_service.write_log("agent_config.update", "success", user, agent_type, {"fields": list(payload)}, audit_log_service.client_ip(request))
    if "connector_id" in payload and (previous or {}).get("connector_id") != config.get("connector_id"):
        audit_log_service.write_log("agent_config.bind_connector", "success", user, agent_type, {"connector_id": config.get("connector_id")}, audit_log_service.client_ip(request))
    return config
