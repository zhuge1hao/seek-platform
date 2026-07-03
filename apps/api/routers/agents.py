from typing import Any

from fastapi import APIRouter, Depends, Request

from services import agent_blueprint_store, audit_log_service, video_agent_status_service
from services.agent_registry import list_agents as list_registered_agents
from services.auth_service import require_viewer_or_above


router = APIRouter()


@router.get("/agents")
def list_agents(_user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, list[dict]]:
    agents = []
    for agent in list_registered_agents():
        item = dict(agent)
        blueprint = agent_blueprint_store.get_blueprint_by_agent(str(agent.get("agent_type") or ""))
        if not blueprint:
            item.update({"blueprint_status": "unmanaged", "blueprint_published": False})
        else:
            version = agent_blueprint_store.get_version(str(blueprint.get("published_version_id") or blueprint.get("current_version_id") or ""))
            item.update({
                "blueprint_id": blueprint["blueprint_id"],
                "blueprint_status": blueprint["status"],
                "blueprint_version": version.get("version_number") if version else None,
                "blueprint_published": bool(blueprint.get("published_version_id")),
            })
        agents.append(item)
    return {"agents": agents}


@router.get("/agents/video-script/status")
def video_script_status(request: Request, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    result = video_agent_status_service.check_status()
    audit_log_service.write_log(
        "agent.video.status_check",
        "success" if result.get("reachable") else "failed",
        user,
        result.get("connector_id") or "video_script_agent",
        {
            "status": result.get("status"),
            "connector_id": result.get("connector_id"),
            "latency_ms": result.get("latency_ms"),
            "error_type": "connection" if result.get("status") == "disconnected" else None,
        },
        audit_log_service.client_ip(request),
    )
    return result
