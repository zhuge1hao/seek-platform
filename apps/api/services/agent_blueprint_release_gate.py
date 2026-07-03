from __future__ import annotations

from typing import Any

from services import agent_blueprint_store as store
from services.agent_blueprint_validator import validate_blueprint


class ReleaseGateError(RuntimeError):
    def __init__(self, gate: dict[str, Any]):
        super().__init__("blueprint release gate failed")
        self.gate = gate


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _artifact_types(test_run: dict[str, Any]) -> set[str]:
    summary = test_run.get("result_summary") or {}
    files = summary.get("files") if isinstance(summary, dict) else []
    types = set()
    for item in files if isinstance(files, list) else []:
        if not isinstance(item, dict):
            continue
        types.add(str(item.get("file_type") or item.get("type") or "").lower())
        name = str(item.get("filename") or item.get("name") or item.get("path") or "").lower()
        if name.endswith((".xlsx", ".xls", ".csv")):
            types.add("excel")
        if name.endswith(".json"):
            types.add("json")
    return types


def check_release_gate(blueprint_id: str, version_id: str) -> dict[str, Any]:
    blueprint = store.get_blueprint(blueprint_id)
    version = store.get_version_for_blueprint(blueprint_id, version_id)
    blocking: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not blueprint or not version:
        blocking.append(_issue("VERSION_NOT_FOUND", "待发布版本不存在"))
        return {"allowed": False, "blocking_errors": blocking, "warnings": warnings, "version_id": version_id}
    if blueprint.get("status") in {"disabled", "deprecated"}:
        blocking.append(_issue("BLUEPRINT_NOT_ACTIVE", "已停用或废弃蓝图不能发布"))

    validation = store.latest_validation_for_version(blueprint_id, version_id)
    if not validation:
        blocking.append(_issue("NO_VALIDATION", "当前版本尚未保存验证结果"))
    elif not validation.get("is_valid"):
        blocking.append(_issue("VALIDATION_FAILED", "当前版本最近验证未通过"))
    live = validate_blueprint(blueprint, version, store.list_test_cases(blueprint_id))
    if live.get("errors"):
        blocking.append(_issue("LIVE_VALIDATION_FAILED", "当前版本实时校验存在错误"))
    if live.get("warnings"):
        warnings.append(_issue("VALIDATION_WARNINGS", f"当前版本有 {len(live['warnings'])} 条验证警告"))

    enabled_cases = [case for case in store.list_test_cases(blueprint_id) if case.get("is_enabled")]
    if not enabled_cases:
        blocking.append(_issue("NO_TEST_CASE", "当前蓝图没有启用的测试用例"))
    test_run = store.latest_test_run_for_version(blueprint_id, version_id)
    if not test_run:
        blocking.append(_issue("NO_TEST_RUN", "当前版本没有测试运行记录"))
    elif test_run.get("status") != "passed":
        blocking.append(_issue("LATEST_TEST_NOT_PASSED", "当前版本最近一次测试未通过"))
    elif test_run.get("actual_status") != (test_run.get("expected_status") or "completed"):
        blocking.append(_issue("TEST_STATUS_MISMATCH", "测试期望状态与实际状态不一致"))

    if test_run:
        rules = version.get("acceptance_rules") or {}
        summary = test_run.get("result_summary") or {}
        missing_fields = [path for path in rules.get("required_result_fields") or [] if _get_path(summary, str(path)) is None]
        missing_artifacts = [kind for kind in rules.get("required_artifact_types") or [] if str(kind).lower() not in _artifact_types(test_run)]
        if missing_fields:
            blocking.append(_issue("MISSING_RESULT_FIELDS", "测试结果缺少必需字段"))
        if missing_artifacts:
            blocking.append(_issue("MISSING_ARTIFACTS", "测试结果缺少必需产物"))
        max_seconds = rules.get("max_duration_seconds")
        if max_seconds and test_run.get("duration_ms") and int(test_run["duration_ms"]) > int(max_seconds) * 1000:
            blocking.append(_issue("TEST_TIMEOUT", "测试耗时超过验收限制"))
    return {
        "allowed": not blocking,
        "blocking_errors": blocking,
        "warnings": warnings,
        "validation_id": validation.get("validation_id") if validation else None,
        "test_run_id": test_run.get("test_run_id") if test_run else None,
        "version_id": version_id,
    }


def assert_release_allowed(blueprint_id: str, version_id: str, confirm_warnings: bool = False) -> dict[str, Any]:
    gate = check_release_gate(blueprint_id, version_id)
    if gate["blocking_errors"] or (gate["warnings"] and not confirm_warnings):
        if gate["warnings"] and not gate["blocking_errors"] and not confirm_warnings:
            gate["blocking_errors"] = [_issue("WARNINGS_REQUIRE_CONFIRMATION", "存在发布警告，需要确认")]
        raise ReleaseGateError(gate)
    return gate
