from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services import agent_blueprint_store as store
from services import agent_blueprint_service
from services.agent_blueprint_validator import validate_blueprint


SENSITIVE = ("password", "secret", "api_key", "apikey")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_import_id(source_id: str) -> str:
    base = f"{source_id}_import"
    if not store.get_blueprint(base):
        return base
    index = 2
    while store.get_blueprint(f"{base}_{index}"):
        index += 1
    return f"{base}_{index}"


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***REDACTED***" if (
                any(token in str(key).lower() for token in SENSITIVE)
                or str(key).lower() == "token"
                or str(key).lower().endswith("_token")
            ) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def export_blueprint(blueprint_id: str, user: dict[str, Any]) -> dict[str, Any]:
    detail = agent_blueprint_service.get_detail(blueprint_id, user)
    version = detail["current_version"] or detail["published_version"] or {}
    return redact({
        "format_version": "1.0",
        "platform": "meizhaiseek",
        "exported_at": _now(),
        "blueprint": detail["blueprint"],
        "version": version,
        "test_cases": detail.get("test_cases") or [],
    })


def preview_import(payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    blueprint = dict(payload.get("blueprint") or {})
    version = dict(payload.get("version") or {})
    test_cases = list(payload.get("test_cases") or [])
    source_id = str(blueprint.get("blueprint_id") or "")
    conflict = bool(source_id and store.get_blueprint(source_id))
    validation = validate_blueprint(blueprint, version, test_cases)
    return {
        "valid": validation["valid"],
        "errors": validation["errors"],
        "warnings": validation["warnings"],
        "conflict": conflict,
        "source_blueprint_id": source_id,
        "import_blueprint_id": _next_import_id(source_id) if conflict and source_id else source_id,
        "action": "create_new_id" if conflict else "create",
    }


def import_blueprint(payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    preview = preview_import(payload, user)
    if not preview["valid"]:
        raise RuntimeError("导入内容校验失败。")
    source_blueprint = dict(payload.get("blueprint") or {})
    source_version = dict(payload.get("version") or {})
    target_id = str(payload.get("target_blueprint_id") or "")
    if target_id:
        target = store.get_blueprint(target_id)
        if not target:
            raise RuntimeError("目标蓝图不存在。")
        version = agent_blueprint_service.create_version(target_id, source_version, user)
        return {"action": "create_version", "blueprint": target, "version": version}

    blueprint_id = preview["import_blueprint_id"] or None
    create_payload = {
        **source_blueprint,
        "blueprint_id": blueprint_id,
        "status": "draft",
        "published_version_id": None,
        "current_version_id": None,
        "input_schema": source_version.get("input_schema") or {},
        "methodology": source_version.get("methodology") or {},
        "prompt_config": source_version.get("prompt_config") or {},
        "execution_config": source_version.get("execution_config") or {},
        "output_schema": source_version.get("output_schema") or {},
        "result_ui_config": source_version.get("result_ui_config") or {},
        "acceptance_rules": source_version.get("acceptance_rules") or {},
    }
    detail = agent_blueprint_service.create_draft(create_payload, user)
    new_id = detail["blueprint"]["blueprint_id"]
    for case in payload.get("test_cases") or []:
        agent_blueprint_service.save_test_case(new_id, case, user)
    return {"action": "create", **agent_blueprint_service.get_detail(new_id, user)}
