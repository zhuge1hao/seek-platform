import csv
import io
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from services import agent_config_store, agent_connector_store, agent_run_maintenance, app_sqlite, audit_log_service, debug_payload_service, file_preview_service, file_store, json_to_sqlite_migrator, local_agent_client, payload_preview_service, security_config_service, skill_template_service
from services.auth_service import require_admin
from services.config_backup_service import backup_file, list_backups
from services.config_guard import guard_file_store, validate_json_file


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/admin/runtime/health")
def runtime_health() -> dict[str, Any]:
    agent_report = agent_config_store.guard_configs()
    skill_report = skill_template_service.guard_templates()
    warnings = [*agent_report.get("warnings", []), *skill_report.get("warnings", []), *security_config_service.get_security_warnings()]
    return {
        "status": "ok" if not warnings else "warning",
        "version": "v1.6.3",
        "service": "meizhaiseek-api",
        "configs_valid": True,
        "agent_run_store_valid": True,
        "warnings": warnings,
    }


@router.get("/admin/storage/health")
def storage_health(request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    result = app_sqlite.health_check()
    audit_log_service.write_log("storage.health.view", "success", user, "storage", {"status": result.get("status")}, audit_log_service.client_ip(request))
    return result


@router.post("/admin/storage/migrate-json")
def migrate_json_storage(request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        result = json_to_sqlite_migrator.migrate_json_to_sqlite(force=True)
    except Exception as exc:
        audit_log_service.write_log("storage.migrate_json.failed", "failed", user, "storage", {"error": str(exc)}, audit_log_service.client_ip(request))
        raise HTTPException(status_code=500, detail=f"JSON 迁移失败：{exc}") from exc
    audit_log_service.write_log("storage.migrate_json", result.get("status", "success"), user, "storage", {"migrated": result.get("migrated"), "error_count": len(result.get("errors") or [])}, audit_log_service.client_ip(request))
    return result


@router.get("/admin/runtime/configs/status")
def configs_status() -> dict[str, Any]:
    agent_report = agent_config_store.guard_configs()
    visible_agent_count = len([item for item in agent_report["items"] if item.get("visible", True)])
    skill_report = skill_template_service.guard_templates()
    file_report = guard_file_store(file_store._store_path())  # type: ignore[attr-defined]
    return {
        "status": "ok",
        "configs": [
            {
                "name": "agent_configs",
                "path": agent_report["path"],
                "exists": True,
                "valid": True,
                "schema_version": agent_report["schema_version"],
                "count": visible_agent_count,
                "warnings": agent_report["warnings"],
            },
            {
                "name": "skill_templates",
                "path": skill_report["path"],
                "exists": True,
                "valid": True,
                "schema_version": skill_report["schema_version"],
                "count": len(skill_report["items"]),
                "warnings": skill_report["warnings"],
            },
            {
                "name": "files",
                "path": file_report["path"],
                "exists": True,
                "valid": True,
                "schema_version": "1.0",
                "count": len(file_report["items"]),
                "warnings": file_report["warnings"],
            },
        ],
    }


@router.post("/admin/runtime/configs/backup")
def backup_configs() -> dict[str, Any]:
    backups = []
    for path in [agent_config_store._resolve_store_path(), skill_template_service._store_path(), file_store._store_path()]:  # type: ignore[attr-defined]
        item = backup_file(path, "manual_backup")
        if item:
            backups.append(item)
    return {"status": "ok", "backups": backups, "all_backups": list_backups()}


@router.post("/admin/runtime/configs/repair")
def repair_configs(request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    result = {"status": "ok", "agent_configs": agent_config_store.guard_configs(), "skill_templates": skill_template_service.guard_templates(), "files": guard_file_store(file_store._store_path())}  # type: ignore[attr-defined]
    audit_log_service.write_log("runtime.config.repair", "success", user, "runtime", {}, audit_log_service.client_ip(request))
    return result


@router.post("/admin/runtime/configs/reset")
def reset_configs(request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    backup_configs()
    result = {"status": "ok", "agent_configs": agent_config_store.reset_configs(), "skill_templates": skill_template_service.reset_templates()}
    audit_log_service.write_log("runtime.config.reset", "success", user, "runtime", {}, audit_log_service.client_ip(request))
    return result


@router.get("/admin/runtime/configs/export")
def export_configs() -> dict[str, Any]:
    return {"agent_configs": agent_config_store.list_configs(include_hidden=True), "skill_templates": skill_template_service.list_templates(enabled_only=False), "files": file_store.list_file_records(include_legacy=True, include_all_users=True)}


@router.post("/admin/runtime/cache/clear")
def clear_cache(request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    result = {"status": "ok", "file_previews_cleared": file_preview_service.clear_preview_cache()}
    audit_log_service.write_log("runtime.cache.clear", "success", user, "runtime", result, audit_log_service.client_ip(request))
    return result


@router.get("/admin/agent-runs/stats")
def agent_run_stats() -> dict[str, int]:
    return agent_run_maintenance.stats()


@router.post("/admin/agent-runs/repair-stale")
def repair_stale(request: Request, payload: dict[str, Any] | None = None, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    timeout_minutes = int((payload or {}).get("timeout_minutes") or 120)
    result = agent_run_maintenance.repair_stale(timeout_minutes)
    audit_log_service.write_log("agent_run.repair_stale", "success", user, "agent_runs", result, audit_log_service.client_ip(request))
    return result


@router.post("/admin/agent-runs/cleanup")
def cleanup_runs(payload: dict[str, Any], request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    result = agent_run_maintenance.cleanup(days=int(payload.get("days") or 7), statuses=payload.get("statuses") or ["completed", "failed", "cancelled"], dry_run=bool(payload.get("dry_run", True)))
    audit_log_service.write_log("agent_run.cleanup", "success", user, "agent_runs", result, audit_log_service.client_ip(request))
    return result


@router.get("/admin/debug-payloads")
def list_debug_payloads(limit: int = 50, agent_type: str | None = None, status: str | None = None) -> dict[str, Any]:
    return {"items": debug_payload_service.list_debug_payloads(limit=limit, agent_type=agent_type, status=status)}


@router.get("/admin/debug-payloads/{run_id}")
def get_debug_payload(run_id: str, request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    result = debug_payload_service.read_debug_payload(run_id)
    if not result.get("request_exists") and not result.get("response_exists") and not result.get("error_exists"):
        raise HTTPException(status_code=404, detail="联调记录不存在。")
    audit_log_service.write_log("debug_payload.view", "success", user, run_id, {}, audit_log_service.client_ip(request))
    return result
    return debug_payload_service.read_debug_payload(run_id)


@router.post("/admin/debug-payloads/{run_id}/replay")
def replay_debug_payload(run_id: str, http_request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    debug_payload = debug_payload_service.read_debug_payload(run_id)
    saved_request = debug_payload.get("request")
    if not saved_request:
        raise HTTPException(status_code=404, detail="request.json 不存在。")
    agent_type = str(saved_request.get("agent_type") or "")
    try:
        connector, _ = payload_preview_service.resolve_connector(agent_type)
        if agent_type == "video_script_breakdown":
            replay_result = local_agent_client.run_video_script_breakdown_protocol(saved_request, connector=connector)
        else:
            replay_result = local_agent_client.run_generic_agent_protocol(saved_request, connector=connector)
    except payload_preview_service.PayloadPreviewError as exc:
        replay_result = {"ok": False, "status": "failed", "error": str(exc)}
    audit_log_service.write_log("debug_payload.replay", "success" if replay_result.get("ok") else "failed", user, run_id, {"agent_type": agent_type, "error": replay_result.get("error")}, audit_log_service.client_ip(http_request))
    return {"run_id": run_id, "replay_result": replay_result}


@router.get("/admin/audit-logs")
def get_audit_logs(action: str | None = None, user: str | None = None, status: str | None = None, start_time: str | None = None, end_time: str | None = None, limit: int = 100) -> dict[str, list[dict[str, Any]]]:
    try:
        return {"logs": audit_log_service.list_logs(action=action, user=user, status=status, start_time=start_time, end_time=end_time, limit=limit)}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/admin/audit-logs/export")
def export_audit_logs(request: Request, format: str = "csv", action: str | None = None, user: str | None = None, status: str | None = None, start_time: str | None = None, end_time: str | None = None, limit: int = 500, current_user: dict[str, Any] = Depends(require_admin)) -> Response:
    if format not in {"csv", "jsonl"}:
        raise HTTPException(status_code=400, detail="导出格式只能是 csv 或 jsonl。")
    logs = audit_log_service.list_logs(action=action, user=user, status=status, start_time=start_time, end_time=end_time, limit=limit)
    if format == "jsonl":
        content = "\n".join(json.dumps(item, ensure_ascii=False) for item in logs)
        media_type = "application/x-ndjson"
    else:
        output = io.StringIO()
        fieldnames = ["time", "user_id", "username", "role", "action", "target", "status", "ip", "detail"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for item in logs:
            row = {key: item.get(key, "") for key in fieldnames}
            row["detail"] = json.dumps(row["detail"], ensure_ascii=False)
            writer.writerow(row)
        content = "\ufeff" + output.getvalue()
        media_type = "text/csv"
    audit_log_service.write_log("audit_log.export", "success", current_user, "audit_logs", {"format": format, "count": len(logs)}, audit_log_service.client_ip(request))
    return Response(content=content.encode("utf-8"), media_type=media_type, headers={"Content-Disposition": f'attachment; filename="audit_logs.{format}"'})


