from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import BackgroundTasks

from schemas.agent_runs import AgentRunCreate
from services import agent_blueprint_diff_service, agent_blueprint_store as store
from services import audit_log_service, orchestrator
from services.agent_blueprint_release_gate import ReleaseGateError, assert_release_allowed, check_release_gate
from services.agent_blueprint_validator import VALIDATOR_VERSION, validate_blueprint


class BlueprintServiceError(RuntimeError):
    pass


TERMINAL = {"completed", "failed", "cancelled"}
SENSITIVE_TOKENS = ("password", "secret", "api_key", "apikey")


def _user_id(user: dict[str, Any]) -> str:
    return str(user.get("user_id") or user.get("username") or "system")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _current_version(blueprint: dict[str, Any], include_prompt: bool = True) -> dict[str, Any] | None:
    version_id = blueprint.get("current_version_id") or blueprint.get("published_version_id")
    return store.get_version(str(version_id), include_prompt=include_prompt) if version_id else None


def _assert_no_sensitive(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}" if path else str(key)
            lower_key = str(key).lower()
            if any(token in lower_key for token in SENSITIVE_TOKENS) or lower_key == "token" or lower_key.endswith("_token"):
                raise BlueprintServiceError(f"蓝图配置不能保存敏感字段: {next_path}")
            _assert_no_sensitive(item, next_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_sensitive(item, f"{path}[{index}]")


def _assert_can_view(blueprint: dict[str, Any] | None, user: dict[str, Any]) -> dict[str, Any]:
    if not blueprint:
        raise BlueprintServiceError("蓝图不存在。")
    if user.get("role") == "viewer" and blueprint.get("status") != "published":
        raise PermissionError("当前账号无权访问该蓝图。")
    return blueprint


def _duration_ms(started_at: str | None, completed_at: str | None) -> int | None:
    if not started_at or not completed_at:
        return None
    try:
        return max(0, int((datetime.fromisoformat(completed_at) - datetime.fromisoformat(started_at)).total_seconds() * 1000))
    except ValueError:
        return None


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _artifact_types(result: Any) -> set[str]:
    files = (result or {}).get("files") if isinstance(result, dict) else []
    types: set[str] = set()
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


def list_blueprints(user: dict[str, Any]) -> list[dict[str, Any]]:
    return store.list_blueprints(include_unpublished=user.get("role") != "viewer")


def get_detail(blueprint_id: str, user: dict[str, Any]) -> dict[str, Any]:
    blueprint = _assert_can_view(store.get_blueprint(blueprint_id), user)
    include_prompt = user.get("role") != "viewer"
    versions = store.list_versions(blueprint_id, include_prompt=include_prompt)
    test_cases = [] if user.get("role") == "viewer" else store.list_test_cases(blueprint_id)
    releases = store.list_releases(blueprint_id)
    current_version = next((item for item in versions if item["version_id"] == blueprint.get("current_version_id")), None)
    published_version = next((item for item in versions if item["version_id"] == blueprint.get("published_version_id")), None)
    return {"blueprint": blueprint, "current_version": current_version, "published_version": published_version, "versions": versions, "test_cases": test_cases, "releases": releases}


def create_draft(payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    _assert_no_sensitive(payload)
    data = {**payload, "status": payload.get("status") or "draft"}
    blueprint = store.create_blueprint(data, _user_id(user))
    version = store.create_version(blueprint["blueprint_id"], {
        "version_name": payload.get("version_name") or "初始版本",
        "change_summary": payload.get("change_summary") or "创建蓝图",
        "input_schema": payload.get("input_schema") or {},
        "methodology": payload.get("methodology") or {},
        "prompt_config": payload.get("prompt_config") or {},
        "execution_config": payload.get("execution_config") or {},
        "output_schema": payload.get("output_schema") or {},
        "result_ui_config": payload.get("result_ui_config") or {},
        "acceptance_rules": payload.get("acceptance_rules") or {},
    }, _user_id(user))
    if data["status"] == "published":
        store.mark_version_published(blueprint["blueprint_id"], version["version_id"])
        store.update_blueprint(blueprint["blueprint_id"], {"published_version_id": version["version_id"], "current_version_id": version["version_id"], "status": "published"}, _user_id(user))
        store.create_release(blueprint["blueprint_id"], version["version_id"], "publish", _user_id(user), "seed publish", to_version_id=version["version_id"])
    audit_log_service.write_log("agent_blueprint.create", "success", user, blueprint["blueprint_id"], {"blueprint_id": blueprint["blueprint_id"], "status": data["status"]})
    return get_detail(blueprint["blueprint_id"], user)


def update_basic(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    blueprint = _assert_can_view(store.get_blueprint(blueprint_id), user)
    if blueprint.get("status") in {"published", "deprecated"}:
        raise BlueprintServiceError("已发布或废弃蓝图不能直接修改基本信息，请创建新版本或复制蓝图。")
    updated = store.update_blueprint(blueprint_id, payload, _user_id(user))
    audit_log_service.write_log("agent_blueprint.update", "success", user, blueprint_id, {"blueprint_id": blueprint_id, "status": (updated or {}).get("status")})
    return get_detail(blueprint_id, user)


def create_version(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    _assert_no_sensitive(payload)
    blueprint = _assert_can_view(store.get_blueprint(blueprint_id), user)
    if blueprint.get("status") == "deprecated":
        raise BlueprintServiceError("废弃蓝图只读。")
    base = _current_version(blueprint) or {}
    version = store.create_version(blueprint_id, {
        "version_name": payload.get("version_name") or "",
        "change_summary": payload.get("change_summary") or "",
        "input_schema": payload.get("input_schema", base.get("input_schema") or {}),
        "methodology": payload.get("methodology", base.get("methodology") or {}),
        "prompt_config": payload.get("prompt_config", base.get("prompt_config") or {}),
        "execution_config": payload.get("execution_config", base.get("execution_config") or {}),
        "output_schema": payload.get("output_schema", base.get("output_schema") or {}),
        "result_ui_config": payload.get("result_ui_config", base.get("result_ui_config") or {}),
        "acceptance_rules": payload.get("acceptance_rules", base.get("acceptance_rules") or {}),
        "parent_version_id": base.get("version_id"),
        "metadata": payload.get("metadata") or {},
    }, _user_id(user))
    audit_log_service.write_log("agent_blueprint.version.create", "success", user, blueprint_id, {"blueprint_id": blueprint_id, "version_id": version["version_id"]})
    return version


def validate(blueprint_id: str, user: dict[str, Any]) -> dict[str, Any]:
    blueprint = _assert_can_view(store.get_blueprint(blueprint_id), user)
    version = _current_version(blueprint)
    result = validate_blueprint(blueprint, version, store.list_test_cases(blueprint_id))
    if version:
        saved = store.create_validation_result(blueprint_id, version["version_id"], result, _user_id(user), VALIDATOR_VERSION)
        result.update({"validation_id": saved["validation_id"], "version_id": version["version_id"]})
    audit_log_service.write_log("agent_blueprint.validation.run", "success" if result["valid"] else "failed", user, blueprint_id, {"blueprint_id": blueprint_id, "version_id": result.get("version_id"), "validation_id": result.get("validation_id"), "validation_error_count": len(result["errors"]), "validation_warning_count": len(result["warnings"])})
    return result


def publish(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    blueprint = _assert_can_view(store.get_blueprint(blueprint_id), user)
    version_id = str(payload.get("version_id") or blueprint.get("current_version_id") or "")
    version = store.get_version_for_blueprint(blueprint_id, version_id)
    if not version:
        raise BlueprintServiceError("发布版本不存在。")
    try:
        gate = assert_release_allowed(blueprint_id, version_id, bool(payload.get("confirm_warnings")))
    except ReleaseGateError:
        raise
    previous = blueprint.get("published_version_id")
    store.mark_version_published(blueprint_id, version_id)
    store.update_blueprint(blueprint_id, {"status": "published", "published_version_id": version_id, "current_version_id": version_id}, _user_id(user))
    store.create_release(blueprint_id, version_id, "publish", _user_id(user), str(payload.get("note") or ""), from_version_id=previous, to_version_id=version_id, metadata={"validation_id": gate.get("validation_id"), "test_run_id": gate.get("test_run_id"), "release_gate_summary": gate})
    audit_log_service.write_log("agent_blueprint.publish", "success", user, blueprint_id, {"blueprint_id": blueprint_id, "version_id": version_id, "validation_id": gate.get("validation_id"), "test_run_id": gate.get("test_run_id")})
    return get_detail(blueprint_id, user)


def rollback(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    blueprint = _assert_can_view(store.get_blueprint(blueprint_id), user)
    target = store.get_version_for_blueprint(blueprint_id, str(payload.get("version_id") or ""))
    if not target or not target.get("is_published"):
        raise BlueprintServiceError("只能回滚到历史已发布版本。")
    result = validate_blueprint(blueprint, target, store.list_test_cases(blueprint_id))
    if result.get("errors"):
        raise BlueprintServiceError("回滚目标版本校验失败，禁止回滚。")
    previous = blueprint.get("published_version_id")
    diff = agent_blueprint_diff_service.compare_blueprint_versions(blueprint_id, str(previous or target["version_id"]), target["version_id"]) if previous else {"summary": {}}
    copied = store.create_version(blueprint_id, {
        "version_name": f"Rollback to v{target['version_number']}",
        "change_summary": payload.get("note") or "回滚发布",
        "input_schema": target.get("input_schema") or {},
        "methodology": target.get("methodology") or {},
        "prompt_config": target.get("prompt_config") or {},
        "execution_config": target.get("execution_config") or {},
        "output_schema": target.get("output_schema") or {},
        "result_ui_config": target.get("result_ui_config") or {},
        "acceptance_rules": target.get("acceptance_rules") or {},
        "parent_version_id": target["version_id"],
        "is_published": True,
    }, _user_id(user))
    store.mark_version_published(blueprint_id, copied["version_id"])
    store.update_blueprint(blueprint_id, {"status": "published", "published_version_id": copied["version_id"], "current_version_id": copied["version_id"]}, _user_id(user))
    store.create_release(blueprint_id, copied["version_id"], "rollback", _user_id(user), str(payload.get("note") or ""), from_version_id=previous, to_version_id=copied["version_id"], metadata={"rollback_target_version_id": target["version_id"], "diff_summary": diff.get("summary")})
    audit_log_service.write_log("agent_blueprint.rollback", "success", user, blueprint_id, {"blueprint_id": blueprint_id, "version_id": copied["version_id"], "diff_summary": diff.get("summary")})
    return get_detail(blueprint_id, user)


def set_state(blueprint_id: str, action: str, status: str, user: dict[str, Any], note: str = "") -> dict[str, Any]:
    blueprint = _assert_can_view(store.get_blueprint(blueprint_id), user)
    version_id = blueprint.get("published_version_id") or blueprint.get("current_version_id")
    store.update_blueprint(blueprint_id, {"status": status}, _user_id(user))
    store.create_release(blueprint_id, str(version_id or ""), action, _user_id(user), note, from_version_id=blueprint.get("published_version_id"), to_version_id=version_id)
    audit_log_service.write_log(f"agent_blueprint.{action}", "success", user, blueprint_id, {"blueprint_id": blueprint_id, "status": status})
    return get_detail(blueprint_id, user)


def clone(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    detail = get_detail(blueprint_id, user)
    source = detail["blueprint"]
    version = detail["current_version"] or detail["published_version"] or {}
    cloned = create_draft({
        "agent_id": source.get("agent_id"),
        "name": payload.get("name") or f"{source.get('name')} copy",
        "display_name": payload.get("display_name") or f"{source.get('display_name')} 副本",
        "description": source.get("description"),
        "category": source.get("category"),
        "icon": source.get("icon"),
        "metadata": {"cloned_from": blueprint_id},
        "input_schema": version.get("input_schema") or {},
        "methodology": version.get("methodology") or {},
        "prompt_config": version.get("prompt_config") or {},
        "execution_config": version.get("execution_config") or {},
        "output_schema": version.get("output_schema") or {},
        "result_ui_config": version.get("result_ui_config") or {},
        "acceptance_rules": version.get("acceptance_rules") or {},
    }, user)
    audit_log_service.write_log("agent_blueprint.clone", "success", user, blueprint_id, {"blueprint_id": blueprint_id, "new_blueprint_id": cloned["blueprint"]["blueprint_id"]})
    return cloned


def save_test_case(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any], test_case_id: str | None = None) -> dict[str, Any]:
    _assert_no_sensitive(payload)
    _assert_can_view(store.get_blueprint(blueprint_id), user)
    case = store.save_test_case(blueprint_id, payload, _user_id(user), test_case_id=test_case_id)
    audit_log_service.write_log("agent_blueprint.test_case.create", "success", user, blueprint_id, {"blueprint_id": blueprint_id, "test_case_id": case["test_case_id"]})
    return case


def run_test_case(blueprint_id: str, test_case_id: str, background_tasks: BackgroundTasks, user: dict[str, Any]) -> dict[str, Any]:
    blueprint = _assert_can_view(store.get_blueprint(blueprint_id), user)
    case = store.get_test_case(test_case_id)
    if not case or case["blueprint_id"] != blueprint_id:
        raise BlueprintServiceError("测试用例不存在。")
    version = _current_version(blueprint)
    if not version:
        raise BlueprintServiceError("蓝图版本不存在。")
    version_id = str(case.get("version_id") or version["version_id"])
    test_run = store.create_test_run(blueprint_id, version_id, test_case_id, _user_id(user), case.get("expected_status") or "completed")
    from tasks.queue import backend as queue_backend, enqueue_call

    if queue_backend() == "redis":
        job_id = f"blueprint-test-{test_run['test_run_id']}"
        queue_result = enqueue_call("tasks.blueprint_tasks.execute_blueprint_test", (test_run["test_run_id"], _user_id(user)), job_id, background_tasks, timeout_seconds=3600)
        queued = store.update_test_run(test_run["test_run_id"], {"status": "pending", "metadata": {"queue_job_id": queue_result.get("job_id")}}) or test_run
        audit_log_service.write_log("agent_blueprint.test_run.enqueue", "success", user, blueprint_id, {"blueprint_id": blueprint_id, "test_case_id": test_case_id, "test_run_id": test_run["test_run_id"], "job_id": queue_result.get("job_id")})
        return {"test_case": store.get_test_case(test_case_id), "test_run": queued, "run": None, "job_id": queue_result.get("job_id"), "status": "queued"}
    data = case.get("input") or {}
    agent_type = str(data.get("agent_type") or blueprint.get("agent_id") or "")
    payload = AgentRunCreate(
        agent_type=agent_type,
        mode=data.get("mode"),
        prompt=str(data.get("prompt") or f"blueprint test: {case['name']}"),
        video_path=data.get("video_path") or data.get("video_file"),
        video_url=data.get("video_url"),
        workflow_options={key: value for key, value in data.items() if key not in {"agent_type", "mode", "prompt", "video_path", "video_file", "video_url"}},
    )
    try:
        created = orchestrator.start_run(payload, background_tasks, user)
    except Exception as exc:
        store.update_test_run(test_run["test_run_id"], {"status": "error", "completed_at": _now(), "error_message": str(exc)})
        raise
    store.update_test_run(test_run["test_run_id"], {"status": "running", "agent_run_id": created["run_id"]})
    store.set_test_case_run_result(test_case_id, created["run_id"], {"status": "running", "run_id": created["run_id"], "test_run_id": test_run["test_run_id"]})
    audit_log_service.write_log("agent_blueprint.test_run.create", "success", user, blueprint_id, {"blueprint_id": blueprint_id, "test_case_id": test_case_id, "test_run_id": test_run["test_run_id"], "run_id": created["run_id"]})
    return {"test_case": store.get_test_case(test_case_id), "test_run": store.get_test_run(test_run["test_run_id"]), "run": created}


def execute_queued_test_case(test_run_id: str, user_id: str) -> None:
    test_run = store.get_test_run(test_run_id)
    if not test_run or test_run.get("status") in TERMINAL:
        return
    case = store.get_test_case(str(test_run.get("test_case_id") or ""))
    blueprint = store.get_blueprint(str(test_run.get("blueprint_id") or ""))
    if not case or not blueprint:
        store.update_test_run(test_run_id, {"status": "error", "completed_at": _now(), "error_message": "blueprint test case not found"})
        return
    if str(case.get("blueprint_id") or "") != str(blueprint.get("blueprint_id") or ""):
        store.update_test_run(test_run_id, {"status": "error", "completed_at": _now(), "error_message": "blueprint test case mismatch"})
        return
    data = case.get("input") or {}
    agent_type = str(data.get("agent_type") or blueprint.get("agent_id") or "")
    payload = AgentRunCreate(
        agent_type=agent_type,
        mode=data.get("mode"),
        prompt=str(data.get("prompt") or f"blueprint test: {case['name']}"),
        video_path=data.get("video_path") or data.get("video_file"),
        video_url=data.get("video_url"),
        workflow_options={key: value for key, value in data.items() if key not in {"agent_type", "mode", "prompt", "video_path", "video_file", "video_url"}},
    )
    user = {"user_id": user_id, "username": user_id, "role": "operator"}
    try:
        created = orchestrator.start_run(payload, BackgroundTasks(), user)
    except Exception as exc:
        store.update_test_run(test_run_id, {"status": "error", "completed_at": _now(), "error_message": str(exc)})
        raise
    store.update_test_run(test_run_id, {"status": "running", "agent_run_id": created["run_id"]})
    store.set_test_case_run_result(str(test_run["test_case_id"]), created["run_id"], {"status": "running", "run_id": created["run_id"], "test_run_id": test_run_id})
    audit_log_service.write_log("agent_blueprint.test_run.start", "success", user, str(test_run["blueprint_id"]), {"blueprint_id": test_run["blueprint_id"], "test_case_id": test_run["test_case_id"], "test_run_id": test_run_id, "run_id": created["run_id"]})


def sync_test_run_result(run: dict[str, Any]) -> None:
    status = str(run.get("status") or "")
    run_id = str(run.get("run_id") or "")
    if status not in TERMINAL or not run_id:
        return
    test_run = store.get_test_run_by_agent_run_id(run_id)
    case = store.get_test_case(test_run["test_case_id"]) if test_run else store.get_test_case_by_run_id(run_id)
    if not case:
        return
    expected = case.get("expected_status") or "completed"
    result = run.get("result") if isinstance(run.get("result"), dict) else {}
    required_fields = (case.get("expected_result_rules") or {}).get("required_result_fields") or []
    required_artifacts = (case.get("expected_artifacts") or {}).get("required_artifact_types") or []
    missing_fields = [path for path in required_fields if _get_path(result, str(path)) is None]
    missing_artifacts = [kind for kind in required_artifacts if str(kind).lower() not in _artifact_types(result)]
    passed = status == expected and not missing_fields and not missing_artifacts
    completed_at = run.get("completed_at") or _now()
    if test_run:
        store.update_test_run(test_run["test_run_id"], {
            "status": "passed" if passed else ("cancelled" if status == "cancelled" else "failed"),
            "actual_status": status,
            "completed_at": completed_at,
            "duration_ms": _duration_ms(test_run.get("started_at"), completed_at),
            "result_summary": result,
            "missing_result_fields": missing_fields,
            "missing_artifacts": missing_artifacts,
            "error_message": run.get("error") or "",
        })
    store.set_test_case_run_result(case["test_case_id"], run_id, {
        "status": "PASS" if passed else "FAIL",
        "run_status": status,
        "error": run.get("error"),
        "summary": result.get("summary") if isinstance(result, dict) else None,
        "missing_result_fields": missing_fields,
        "missing_artifacts": missing_artifacts,
        "test_run_id": test_run.get("test_run_id") if test_run else None,
        "run_id": run_id,
    })


def list_validations(blueprint_id: str, user: dict[str, Any]) -> list[dict[str, Any]]:
    _assert_can_view(store.get_blueprint(blueprint_id), user)
    if user.get("role") == "viewer":
        raise PermissionError("viewer cannot view validation history")
    return store.list_validation_results(blueprint_id)


def get_validation(blueprint_id: str, validation_id: str, user: dict[str, Any]) -> dict[str, Any]:
    _assert_can_view(store.get_blueprint(blueprint_id), user)
    item = store.get_validation_result(validation_id)
    if not item or item["blueprint_id"] != blueprint_id:
        raise BlueprintServiceError("validation not found")
    return item


def list_test_runs(blueprint_id: str, user: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    _assert_can_view(store.get_blueprint(blueprint_id), user)
    if user.get("role") == "viewer":
        raise PermissionError("viewer cannot view test runs")
    return store.list_test_runs(blueprint_id, limit=limit)


def get_test_run(blueprint_id: str, test_run_id: str, user: dict[str, Any]) -> dict[str, Any]:
    _assert_can_view(store.get_blueprint(blueprint_id), user)
    item = store.get_test_run(test_run_id)
    if not item or item["blueprint_id"] != blueprint_id:
        raise BlueprintServiceError("test run not found")
    return item


def release_gate(blueprint_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    blueprint = _assert_can_view(store.get_blueprint(blueprint_id), user)
    version_id = str(payload.get("version_id") or blueprint.get("current_version_id") or "")
    gate = check_release_gate(blueprint_id, version_id)
    audit_log_service.write_log("agent_blueprint.release_gate.check", "success" if gate.get("allowed") else "failed", user, blueprint_id, {"blueprint_id": blueprint_id, "version_id": version_id, "gate_allowed": gate.get("allowed")})
    return gate


def delete_blueprint(blueprint_id: str, user: dict[str, Any]) -> bool:
    blueprint = _assert_can_view(store.get_blueprint(blueprint_id), user)
    if blueprint.get("published_version_id") or blueprint.get("status") != "draft":
        raise BlueprintServiceError("只能删除未发布草稿蓝图。")
    return store.delete_blueprint(blueprint_id)
