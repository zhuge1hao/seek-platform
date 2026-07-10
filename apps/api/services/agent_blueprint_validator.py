from __future__ import annotations

import re
from typing import Any

from services import agent_connector_store
from services.agent_blueprint_store import STATUSES
from services.agent_registry import get_agent_by_type


INPUT_TYPES = {"text", "textarea", "number", "boolean", "select", "multi_select", "file", "image", "video", "excel", "word", "local_path", "dataset", "knowledge_base"}
FAILURE_POLICIES = {"stop", "continue", "retry", "skip"}
EXECUTION_TYPES = {"internal", "http_connector", "cli_connector", "mock"}
WORKFLOWS = {"video_script_workflow", "competitor_analysis_workflow", "smart_selection_workflow", "detail_page_planning_workflow", "main_image_breakdown_workflow", "generic_agent_workflow"}
RENDERERS = {"generic_text", "generic_structured", "video_breakdown", "table_report", "dataset_report"}
SENSITIVE_TOKENS = ("password", "secret", "api_key", "apikey")
VAR_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}|\{([A-Za-z_][A-Za-z0-9_]*)\}")
VALIDATOR_VERSION = "v1.8"


def _issue(field: str, message: str) -> dict[str, str]:
    return {"field": field, "message": message}


def _walk_sensitive(value: Any, path: str = "") -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}" if path else str(key)
            lower_key = str(key).lower()
            if any(token in lower_key for token in SENSITIVE_TOKENS) or lower_key == "token" or lower_key.endswith("_token"):
                issues.append(_issue(next_path, "sensitive field is not allowed"))
            issues.extend(_walk_sensitive(item, next_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(_walk_sensitive(item, f"{path}[{index}]"))
    return issues


def validate_blueprint(blueprint: dict[str, Any] | None, version: dict[str, Any] | None, test_cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not blueprint:
        errors.append(_issue("blueprint", "blueprint not found"))
    if not version:
        errors.append(_issue("version", "version not found"))
        return {"valid": False, "errors": errors, "warnings": warnings}

    status = str((blueprint or {}).get("status") or "")
    if status and status not in STATUSES:
        errors.append(_issue("status", "invalid lifecycle status"))

    input_schema = version.get("input_schema") or {}
    fields = input_schema.get("fields") or []
    seen_fields: set[str] = set()
    if not isinstance(fields, list):
        errors.append(_issue("input_schema.fields", "fields must be a list"))
        fields = []
    for index, field in enumerate(fields):
        field_id = str((field or {}).get("field_id") or "")
        field_type = str((field or {}).get("type") or "")
        if not field_id:
            errors.append(_issue(f"input_schema.fields[{index}].field_id", "field_id is required"))
        elif field_id in seen_fields:
            errors.append(_issue(f"input_schema.fields[{index}].field_id", "field_id is duplicated"))
        seen_fields.add(field_id)
        if field_type not in INPUT_TYPES:
            errors.append(_issue(f"input_schema.fields[{index}].type", "unsupported input type"))

    methodology = version.get("methodology") or {}
    steps = methodology.get("steps") or []
    orders: list[int] = []
    if not isinstance(steps, list):
        errors.append(_issue("methodology.steps", "steps must be a list"))
        steps = []
    for index, step in enumerate(steps):
        if str((step or {}).get("failure_policy") or "stop") not in FAILURE_POLICIES:
            errors.append(_issue(f"methodology.steps[{index}].failure_policy", "unsupported failure policy"))
        order_value = (step or {}).get("order")
        try:
            if order_value is None:
                raise ValueError
            orders.append(int(order_value))
        except (TypeError, ValueError):
            errors.append(_issue(f"methodology.steps[{index}].order", "order must be numeric"))
    if orders and orders != sorted(orders):
        errors.append(_issue("methodology.steps", "step order must be ascending"))

    prompt_config = version.get("prompt_config") or {}
    variables = prompt_config.get("variables") or []
    declared = {str(item.get("name")) for item in variables if isinstance(item, dict) and item.get("name")}
    template = "\n".join(str(prompt_config.get(key) or "") for key in ("system_prompt", "user_prompt_template", "output_instructions"))
    used = {left or right for left, right in VAR_RE.findall(template)}
    for name in sorted(used - declared):
        errors.append(_issue("prompt_config.variables", f"template uses undefined variable: {name}"))
    for name in sorted(declared - used):
        warnings.append(_issue("prompt_config.variables", f"variable declared but unused: {name}"))

    execution = version.get("execution_config") or {}
    execution_type = str(execution.get("execution_type") or "internal")
    if execution_type not in EXECUTION_TYPES:
        errors.append(_issue("execution_config.execution_type", "unsupported execution type"))
    agent_id = str(execution.get("agent_id") or (blueprint or {}).get("agent_id") or "")
    if agent_id and not get_agent_by_type(agent_id):
        errors.append(_issue("execution_config.agent_id", "bound agent does not exist"))
    workflow_type = str(execution.get("workflow_type") or "")
    if workflow_type and workflow_type not in WORKFLOWS:
        errors.append(_issue("execution_config.workflow_type", "workflow does not exist"))
    connector_id = str(execution.get("connector_id") or "")
    if execution_type in {"http_connector", "cli_connector"}:
        connector = agent_connector_store.get_connector(connector_id) if connector_id else None
        if not connector:
            errors.append(_issue("execution_config.connector_id", "connector does not exist"))
        elif not connector.get("enabled"):
            errors.append(_issue("execution_config.connector_id", "connector is disabled"))

    ui = version.get("result_ui_config") or {}
    renderer = str(ui.get("renderer") or "generic_structured")
    if renderer not in RENDERERS:
        errors.append(_issue("result_ui_config.renderer", "unsupported renderer"))

    cases = test_cases or []
    if not cases:
        warnings.append(_issue("test_cases", "no test cases configured"))
    for index, case in enumerate(cases):
        if not case.get("name"):
            errors.append(_issue(f"test_cases[{index}].name", "test case name is required"))
        if not isinstance(case.get("input"), dict):
            errors.append(_issue(f"test_cases[{index}].input", "test case input must be an object"))

    errors.extend(_walk_sensitive({"blueprint": blueprint or {}, "version": version or {}, "test_cases": cases}))
    return {"valid": not errors, "errors": errors, "warnings": warnings}
