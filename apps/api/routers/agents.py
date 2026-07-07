import os
from typing import Any

from fastapi import APIRouter, Depends, Request

from services import app_sqlite, audit_log_service, cache_service, video_agent_status_service
from services.agent_registry import list_agents as list_registered_agents
from services.auth_service import require_viewer_or_above


router = APIRouter()
AGENT_LIST_CACHE_KEY = "agents:list:v181"


def _json(value: str | None, default: Any) -> Any:
    return app_sqlite.json_load(value, default) if value else default


def _load_blueprint_summaries(agent_types: list[str]) -> dict[str, dict[str, Any]]:
    if not agent_types:
        return {}
    placeholders = ",".join("?" for _ in agent_types)
    with app_sqlite.connection() as conn:
        blueprint_sql = "SELECT blueprint_id, agent_id, status, current_version_id, published_version_id FROM agent_blueprints WHERE agent_id IN (" + placeholders + ") ORDER BY updated_at DESC"  # nosec B608
        blueprint_rows = conn.execute(blueprint_sql, tuple(agent_types)).fetchall()
        blueprints: dict[str, dict[str, Any]] = {}
        version_ids: list[str] = []
        for row in blueprint_rows:
            agent_id = str(row["agent_id"] or "")
            if not agent_id or agent_id in blueprints:
                continue
            item = dict(row)
            blueprints[agent_id] = item
            version_id = str(item.get("published_version_id") or item.get("current_version_id") or "")
            if version_id:
                version_ids.append(version_id)
        versions: dict[str, dict[str, Any]] = {}
        if version_ids:
            version_placeholders = ",".join("?" for _ in version_ids)
            version_sql = "SELECT version_id, blueprint_id, version_number, methodology_json, output_schema_json FROM agent_blueprint_versions WHERE version_id IN (" + version_placeholders + ")"  # nosec B608
            version_rows = conn.execute(version_sql, tuple(version_ids)).fetchall()
            versions = {str(row["version_id"]): dict(row) for row in version_rows}
        latest_tests: dict[str, dict[str, Any]] = {}
        if version_ids:
            test_placeholders = ",".join("?" for _ in version_ids)
            test_sql = "SELECT version_id, status, started_at FROM agent_blueprint_test_runs WHERE version_id IN (" + test_placeholders + ") ORDER BY started_at DESC"  # nosec B608
            test_rows = conn.execute(test_sql, tuple(version_ids)).fetchall()
            for row in test_rows:
                version_id = str(row["version_id"])
                if version_id not in latest_tests:
                    latest_tests[version_id] = dict(row)
    result: dict[str, dict[str, Any]] = {}
    for agent_id, blueprint in blueprints.items():
        if blueprint.get("status") in {"draft", "testing"}:
            result[agent_id] = {"blueprint_status": "unmanaged", "blueprint_published": False}
            continue
        version_id = str(blueprint.get("published_version_id") or blueprint.get("current_version_id") or "")
        version = versions.get(version_id) or {}
        steps = (_json(version.get("methodology_json"), {}).get("steps") or []) if version else []
        sections = (_json(version.get("output_schema_json"), {}).get("sections") or []) if version else []
        last_test = latest_tests.get(version_id)
        result[agent_id] = {
            "blueprint_id": blueprint["blueprint_id"],
            "blueprint_status": blueprint["status"],
            "blueprint_version": version.get("version_number") if version else None,
            "blueprint_published": bool(blueprint.get("published_version_id")),
            "blueprint_last_test_status": last_test.get("status") if last_test else None,
            "blueprint_methodology_summary": {"step_count": len(steps), "steps": [step.get("name") or step.get("step_id") for step in steps[:5] if isinstance(step, dict)]},
            "blueprint_output_summary": {"section_count": len(sections), "sections": [section.get("label") or section.get("section_id") for section in sections[:6] if isinstance(section, dict)]},
        }
    return result


@router.get("/agents")
def list_agents(_user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, list[dict]]:
    cached = cache_service.get(AGENT_LIST_CACHE_KEY)
    if isinstance(cached, dict) and isinstance(cached.get("agents"), list):
        return cached
    registered_agents = list_registered_agents()
    blueprint_summaries = _load_blueprint_summaries([str(agent.get("agent_type") or "") for agent in registered_agents])
    agents = []
    for agent in registered_agents:
        item = dict(agent)
        item.update(blueprint_summaries.get(str(agent.get("agent_type") or ""), {"blueprint_status": "unmanaged", "blueprint_published": False}))
        agents.append(item)
    result = {"agents": agents}
    cache_service.set(AGENT_LIST_CACHE_KEY, result, ttl_seconds=int(os.getenv("AGENT_LIST_CACHE_TTL_SECONDS", "15")))
    return result


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
