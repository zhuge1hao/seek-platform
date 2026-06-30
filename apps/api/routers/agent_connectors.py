from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from services import agent_connector_store, agent_connector_tester, audit_log_service, payload_preview_service
from services.auth_service import require_admin


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/agent-connectors")
def list_connectors() -> dict[str, list[dict[str, Any]]]:
    return {"items": agent_connector_store.list_connectors()}


@router.get("/agent-connectors/{connector_id}")
def get_connector(connector_id: str) -> dict[str, Any]:
    connector = agent_connector_store.get_connector(connector_id)
    if connector is None:
        raise HTTPException(status_code=404, detail="连接器不存在。")
    return connector


@router.post("/agent-connectors")
def create_connector(payload: dict[str, Any], request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        connector = agent_connector_store.create_connector(payload)
    except agent_connector_store.ConnectorConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except agent_connector_store.ConnectorStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    audit_log_service.write_log("agent_connector.create", "success", user, connector["connector_id"], {"agent_type": connector["agent_type"]}, audit_log_service.client_ip(request))
    return connector


@router.post("/agent-connectors/{connector_id}")
def update_connector(connector_id: str, payload: dict[str, Any], request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        connector = agent_connector_store.update_connector(connector_id, payload)
    except agent_connector_store.ConnectorStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if connector is None:
        raise HTTPException(status_code=404, detail="连接器不存在。")
    audit_log_service.write_log("agent_connector.update", "success", user, connector_id, {"fields": list(payload)}, audit_log_service.client_ip(request))
    return connector


@router.delete("/agent-connectors/{connector_id}")
def delete_connector(connector_id: str, request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    connector = agent_connector_store.disable_connector(connector_id)
    if connector is None:
        raise HTTPException(status_code=404, detail="连接器不存在。")
    audit_log_service.write_log("agent_connector.delete", "success", user, connector_id, {"enabled": False}, audit_log_service.client_ip(request))
    return connector


@router.post("/agent-connectors/{connector_id}/test")
def test_connector(connector_id: str, payload: dict[str, Any], request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    connector = agent_connector_store.get_connector(connector_id)
    if connector is None:
        raise HTTPException(status_code=404, detail="连接器不存在。")
    result = agent_connector_tester.test_connector(connector, str(payload.get("prompt") or "测试连接"), payload.get("extra_payload") or {})
    audit_log_service.write_log("agent_connector.test", result["status"], user, connector_id, {"mode": connector.get("mode"), "duration_ms": result["duration_ms"], "error": result.get("error")}, audit_log_service.client_ip(request))
    return result


@router.post("/agent-connectors/{connector_id}/preview-payload")
def preview_connector_payload(connector_id: str, payload: dict[str, Any], request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    if agent_connector_store.get_connector(connector_id) is None:
        raise HTTPException(status_code=404, detail="连接器不存在。")
    try:
        result = payload_preview_service.build_payload(payload, user, explicit_connector_id=connector_id)
    except payload_preview_service.PayloadPreviewError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    audit_log_service.write_log("payload.preview", "success", user, connector_id, {"agent_type": payload.get("agent_type")}, audit_log_service.client_ip(request))
    return {"connector_id": result["connector_id"], "payload": result["payload"]}
