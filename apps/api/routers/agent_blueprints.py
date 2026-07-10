from __future__ import annotations

from typing import Any, NoReturn

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from services import agent_blueprint_diff_service, agent_blueprint_import_export, agent_blueprint_preview_service, agent_blueprint_registry_sync_service, agent_blueprint_service, agent_blueprint_store, audit_log_service
from services.agent_blueprint_release_gate import ReleaseGateError
from services.agent_blueprint_service import BlueprintServiceError
from services.auth_service import require_admin, require_operator_or_admin, require_viewer_or_above


router = APIRouter()


def _raise(exc: Exception) -> NoReturn:
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if isinstance(exc, ReleaseGateError):
        raise HTTPException(status_code=409, detail=exc.gate) from exc
    if isinstance(exc, BlueprintServiceError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/agent-blueprints")
def list_blueprints(user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    return {"items": agent_blueprint_service.list_blueprints(user)}


@router.post("/agent-blueprints")
def create_blueprint(payload: dict[str, Any], user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.create_draft(payload, user)
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/import/preview")
def preview_import(payload: dict[str, Any], request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    result = agent_blueprint_import_export.preview_import(payload, user)
    audit_log_service.write_log("agent_blueprint.import.preview", "success" if result.get("valid") else "failed", user, "agent_blueprint_import", {"validation_error_count": len(result.get("errors") or []), "validation_warning_count": len(result.get("warnings") or [])}, audit_log_service.client_ip(request))
    return result


@router.post("/agent-blueprints/import")
def import_blueprint(payload: dict[str, Any], request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        result = agent_blueprint_import_export.import_blueprint(payload, user)
    except Exception as exc:
        _raise(exc)
    audit_log_service.write_log("agent_blueprint.import", "success", user, (result.get("blueprint") or {}).get("blueprint_id", "agent_blueprint_import"), {"action": result.get("action")}, audit_log_service.client_ip(request))
    return result


@router.get("/agent-blueprints/registry-sync/preview")
def preview_registry_sync(user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    return agent_blueprint_registry_sync_service.preview_registry_sync()


@router.post("/agent-blueprints/registry-sync/apply")
def apply_registry_sync(payload: dict[str, Any], request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    agent_ids = payload.get("agent_ids") if isinstance(payload, dict) else []
    if not isinstance(agent_ids, list):
        raise HTTPException(status_code=422, detail="agent_ids must be a list")
    if payload.get("create_as") not in (None, "draft"):
        raise HTTPException(status_code=422, detail="create_as must be draft")
    result = agent_blueprint_registry_sync_service.apply_registry_sync([str(item) for item in agent_ids], user)
    audit_log_service.write_log("agent_blueprint.registry_sync.apply", "success", user, "agent_blueprint_registry_sync", {"agent_ids": agent_ids, "created_count": len(result.get("created") or [])}, audit_log_service.client_ip(request))
    return result


@router.get("/agent-blueprints/{blueprint_id}")
def get_blueprint(blueprint_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.get_detail(blueprint_id, user)
    except Exception as exc:
        _raise(exc)


@router.patch("/agent-blueprints/{blueprint_id}")
def update_blueprint(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.update_basic(blueprint_id, payload, user)
    except Exception as exc:
        _raise(exc)


@router.delete("/agent-blueprints/{blueprint_id}")
def delete_blueprint(blueprint_id: str, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return {"deleted": agent_blueprint_service.delete_blueprint(blueprint_id, user)}
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/versions")
def create_version(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return {"version": agent_blueprint_service.create_version(blueprint_id, payload, user)}
    except Exception as exc:
        _raise(exc)


@router.get("/agent-blueprints/{blueprint_id}/versions")
def list_versions(blueprint_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    try:
        agent_blueprint_service.get_detail(blueprint_id, user)
        return {"items": agent_blueprint_store.list_versions(blueprint_id, include_prompt=user.get("role") != "viewer")}
    except Exception as exc:
        _raise(exc)


@router.get("/agent-blueprints/{blueprint_id}/versions/diff")
def diff_versions(blueprint_id: str, from_version_id: str, to_version_id: str, request: Request, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    try:
        agent_blueprint_service.get_detail(blueprint_id, user)
        result = agent_blueprint_diff_service.compare_blueprint_versions(blueprint_id, from_version_id, to_version_id)
    except Exception as exc:
        _raise(exc)
    audit_log_service.write_log("agent_blueprint.diff.view", "success", user, blueprint_id, {"blueprint_id": blueprint_id, "diff_summary": result.get("summary")}, audit_log_service.client_ip(request))
    return result


@router.get("/agent-blueprints/{blueprint_id}/versions/{version_id}")
def get_version(blueprint_id: str, version_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    try:
        agent_blueprint_service.get_detail(blueprint_id, user)
        version = agent_blueprint_store.get_version_for_blueprint(blueprint_id, version_id, include_prompt=user.get("role") != "viewer")
        if not version:
            raise BlueprintServiceError("版本不存在。")
        return {"version": version}
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/validate")
def validate_blueprint(blueprint_id: str, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.validate(blueprint_id, user)
    except Exception as exc:
        _raise(exc)


@router.get("/agent-blueprints/{blueprint_id}/validations")
def list_validations(blueprint_id: str, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return {"items": agent_blueprint_service.list_validations(blueprint_id, user)}
    except Exception as exc:
        _raise(exc)


@router.get("/agent-blueprints/{blueprint_id}/validations/{validation_id}")
def get_validation(blueprint_id: str, validation_id: str, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return {"validation": agent_blueprint_service.get_validation(blueprint_id, validation_id, user)}
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/release-gate")
def release_gate(blueprint_id: str, payload: dict[str, Any] | None = None, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.release_gate(blueprint_id, payload or {}, user)
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/publish")
def publish_blueprint(blueprint_id: str, payload: dict[str, Any] | None = None, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.publish(blueprint_id, payload or {}, user)
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/rollback")
def rollback_blueprint(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.rollback(blueprint_id, payload, user)
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/clone")
def clone_blueprint(blueprint_id: str, payload: dict[str, Any] | None = None, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.clone(blueprint_id, payload or {}, user)
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/disable")
def disable_blueprint(blueprint_id: str, payload: dict[str, Any] | None = None, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.set_state(blueprint_id, "disable", "disabled", user, str((payload or {}).get("note") or ""))
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/enable")
def enable_blueprint(blueprint_id: str, payload: dict[str, Any] | None = None, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.set_state(blueprint_id, "enable", "published", user, str((payload or {}).get("note") or ""))
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/deprecate")
def deprecate_blueprint(blueprint_id: str, payload: dict[str, Any] | None = None, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.set_state(blueprint_id, "deprecate", "deprecated", user, str((payload or {}).get("note") or ""))
    except Exception as exc:
        _raise(exc)


@router.get("/agent-blueprints/{blueprint_id}/test-cases")
def list_test_cases(blueprint_id: str, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        agent_blueprint_service.get_detail(blueprint_id, user)
        return {"items": agent_blueprint_store.list_test_cases(blueprint_id)}
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/test-cases")
def create_test_case(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return {"test_case": agent_blueprint_service.save_test_case(blueprint_id, payload, user)}
    except Exception as exc:
        _raise(exc)


@router.patch("/agent-blueprints/{blueprint_id}/test-cases/{test_case_id}")
def update_test_case(blueprint_id: str, test_case_id: str, payload: dict[str, Any], user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return {"test_case": agent_blueprint_service.save_test_case(blueprint_id, payload, user, test_case_id=test_case_id)}
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/test-cases/{test_case_id}/run")
def run_test_case(blueprint_id: str, test_case_id: str, background_tasks: BackgroundTasks, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return agent_blueprint_service.run_test_case(blueprint_id, test_case_id, background_tasks, user)
    except Exception as exc:
        _raise(exc)


@router.get("/agent-blueprints/{blueprint_id}/test-runs")
def list_test_runs(blueprint_id: str, limit: int = 20, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return {"items": agent_blueprint_service.list_test_runs(blueprint_id, user, limit=limit)}
    except Exception as exc:
        _raise(exc)


@router.get("/agent-blueprints/{blueprint_id}/test-runs/{test_run_id}")
def get_test_run(blueprint_id: str, test_run_id: str, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        return {"test_run": agent_blueprint_service.get_test_run(blueprint_id, test_run_id, user)}
    except Exception as exc:
        _raise(exc)


@router.post("/agent-blueprints/{blueprint_id}/preview/input")
def preview_input(blueprint_id: str, request: Request, payload: dict[str, Any] | None = None, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        agent_blueprint_service.get_detail(blueprint_id, user)
        result = agent_blueprint_preview_service.input_preview((payload or {}).get("input_schema") or payload or {})
    except Exception as exc:
        _raise(exc)
    audit_log_service.write_log("agent_blueprint.preview.input", "success", user, blueprint_id, {"blueprint_id": blueprint_id}, audit_log_service.client_ip(request))
    return result


@router.post("/agent-blueprints/{blueprint_id}/preview/result")
def preview_result(blueprint_id: str, request: Request, payload: dict[str, Any] | None = None, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        agent_blueprint_service.get_detail(blueprint_id, user)
        data = payload or {}
        result = agent_blueprint_preview_service.result_preview(data.get("output_schema") or data, data.get("result_ui_config") or {})
    except Exception as exc:
        _raise(exc)
    audit_log_service.write_log("agent_blueprint.preview.result", "success", user, blueprint_id, {"blueprint_id": blueprint_id}, audit_log_service.client_ip(request))
    return result


@router.get("/agent-blueprints/{blueprint_id}/releases")
def list_releases(blueprint_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    try:
        agent_blueprint_service.get_detail(blueprint_id, user)
        return {"items": agent_blueprint_store.list_releases(blueprint_id)}
    except Exception as exc:
        _raise(exc)


@router.get("/agent-blueprints/{blueprint_id}/export")
def export_blueprint(blueprint_id: str, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    try:
        result = agent_blueprint_import_export.export_blueprint(blueprint_id, user)
    except Exception as exc:
        _raise(exc)
    audit_log_service.write_log("agent_blueprint.export", "success", user, blueprint_id, {"blueprint_id": blueprint_id}, audit_log_service.client_ip(request))
    return result
