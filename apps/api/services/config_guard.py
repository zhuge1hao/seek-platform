import json
from pathlib import Path
from typing import Any

from schemas.agent_runs import DEFAULT_VIDEO_SCRIPT_SESSION_ID
from services.config_backup_service import backup_file, move_to_corrupted
from services.config_migration_service import (
    SCHEMA_VERSION,
    unwrap_agent_configs,
    unwrap_skill_templates,
    wrap_agent_configs,
    wrap_skill_templates,
    write_json,
)


MOJIBAKE_MARKERS = ("\u00e8", "\u00e6", "\u00e5", "\u00e4", "\u00e7", "\u923b", "\u9241", "\ufffd")
VALID_RUN_STATUSES = {"running", "completed", "failed", "cancelled"}


def looks_corrupt_text(value: Any) -> bool:
    return isinstance(value, str) and any(marker in value for marker in MOJIBAKE_MARKERS)


def validate_json_file(path: Path) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    if not path.exists():
        return {"exists": False, "valid": False, "warnings": ["文件不存在。"], "errors": []}
    try:
        text = path.read_text(encoding="utf-8")
        json.loads(text)
        if any(marker in text for marker in MOJIBAKE_MARKERS):
            warnings.append("检测到疑似乱码字符。")
        return {"exists": True, "valid": not errors, "warnings": warnings, "errors": errors}
    except json.JSONDecodeError as exc:
        errors.append(f"JSON 解析失败：{exc}")
    except OSError as exc:
        errors.append(f"文件读取失败：{exc}")
    return {"exists": True, "valid": False, "warnings": warnings, "errors": errors}


def _load_or_default(path: Path, default_payload: Any, corrupted_reason: str) -> tuple[Any, list[str]]:
    warnings: list[str] = []
    if not path.exists():
        warnings.append("文件不存在，已初始化默认配置。")
        return default_payload, warnings
    try:
        return json.loads(path.read_text(encoding="utf-8")), warnings
    except json.JSONDecodeError:
        move_to_corrupted(path, corrupted_reason)
        warnings.append("文件损坏，已移入 corrupted 并恢复默认配置。")
        return default_payload, warnings


def guard_agent_configs(path: Path, default_configs: list[dict[str, Any]]) -> dict[str, Any]:
    warnings: list[str] = []
    default_by_type = {item["agent_type"]: item for item in default_configs}
    raw, load_warnings = _load_or_default(path, default_configs, "invalid_json")
    warnings.extend(load_warnings)

    try:
        configs, migrated, schema_version = unwrap_agent_configs(raw)
        if migrated:
            warnings.append(f"已从旧结构或旧 schema 迁移到 {SCHEMA_VERSION}。")
    except ValueError:
        backup_file(path, "invalid_structure")
        configs = default_configs
        schema_version = None
        warnings.append("结构无效，已恢复默认智能体配置。")

    repaired: list[dict[str, Any]] = []
    seen: set[str] = set()
    for config in configs:
        agent_type = config.get("agent_type")
        if agent_type not in default_by_type:
            warnings.append(f"忽略非法 agent_type：{agent_type}")
            continue
        default = default_by_type[agent_type]
        merged = {**default, **config}
        if agent_type == "competitor_analysis":
            merged["visible"] = True
        for field in ("name", "description"):
            if not merged.get(field) or looks_corrupt_text(merged.get(field)):
                merged[field] = default.get(field)
                warnings.append(f"{agent_type}.{field} 已修复。")
        for field in ("agent_type", "enabled", "workflow", "accepted_inputs", "output_types"):
            if field not in merged or merged.get(field) in (None, "", []):
                merged[field] = default.get(field)
                warnings.append(f"{agent_type}.{field} 缺失，已补默认值。")
        if agent_type == "video_script_breakdown" and merged.get("session_id") != DEFAULT_VIDEO_SCRIPT_SESSION_ID:
            merged["session_id"] = DEFAULT_VIDEO_SCRIPT_SESSION_ID
            warnings.append("video_script_breakdown.session_id 已恢复固定值。")
        if "connector_id" not in config:
            merged["connector_id"] = default.get("connector_id")
            warnings.append(f"{agent_type}.connector_id 缺失，已补默认值。")
        if agent_type == "video_script_breakdown" and not merged.get("connector_id"):
            merged["connector_id"] = "video_script_agent"
            warnings.append("video_script_breakdown.connector_id 已恢复默认绑定。")
        repaired.append(merged)
        if agent_type:
            seen.add(str(agent_type))

    for agent_type, default in default_by_type.items():
        if agent_type not in seen:
            repaired.append(default)
            warnings.append(f"缺失智能体 {agent_type}，已补齐。")

    if warnings or schema_version != SCHEMA_VERSION or isinstance(raw, list):
        if path.exists():
            backup_file(path, "before_repair")
        write_json(path, wrap_agent_configs(repaired))

    return {"items": repaired, "warnings": warnings, "schema_version": SCHEMA_VERSION, "path": str(path)}


def guard_skill_templates(path: Path, default_templates: list[dict[str, Any]]) -> dict[str, Any]:
    warnings: list[str] = []
    default_by_id = {item["id"]: item for item in default_templates}
    raw, load_warnings = _load_or_default(path, default_templates, "invalid_json")
    warnings.extend(load_warnings)

    try:
        templates, migrated, schema_version = unwrap_skill_templates(raw)
        if migrated:
            warnings.append(f"已从旧结构或旧 schema 迁移到 {SCHEMA_VERSION}。")
    except ValueError:
        backup_file(path, "invalid_structure")
        templates = default_templates
        schema_version = None
        warnings.append("结构无效，已恢复默认技能模板。")

    repaired: list[dict[str, Any]] = []
    seen: set[str] = set()
    for template in templates:
        skill_id = template.get("id")
        default = default_by_id.get(skill_id, {})
        merged = {**default, **template}
        if not skill_id:
            warnings.append("忽略缺少 id 的技能模板。")
            continue
        for field in ("name", "prompt_template"):
            if not merged.get(field) or looks_corrupt_text(merged.get(field)):
                merged[field] = default.get(field) or f"{skill_id} 默认模板"
                warnings.append(f"{skill_id}.{field} 已修复。")
        if not merged.get("agent_types"):
            merged["agent_types"] = default.get("agent_types") or []
            warnings.append(f"{skill_id}.agent_types 缺失，已补默认值。")
        merged["enabled"] = bool(merged.get("enabled", True))
        repaired.append(merged)
        seen.add(skill_id)

    for skill_id, default in default_by_id.items():
        if skill_id not in seen:
            repaired.append(default)
            warnings.append(f"缺失技能模板 {skill_id}，已补齐。")

    if warnings or schema_version != SCHEMA_VERSION or isinstance(raw, list):
        if path.exists():
            backup_file(path, "before_repair")
        write_json(path, wrap_skill_templates(repaired))

    return {"items": repaired, "warnings": warnings, "schema_version": SCHEMA_VERSION, "path": str(path)}


def guard_file_store(path: Path) -> dict[str, Any]:
    warnings: list[str] = []
    if not path.exists():
        write_json(path, [])
        return {"items": [], "warnings": ["文件记录不存在，已创建空文件。"], "path": str(path)}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        move_to_corrupted(path, "invalid_json")
        write_json(path, [])
        return {"items": [], "warnings": ["文件记录损坏，已隔离并重建空文件。"], "path": str(path)}
    if isinstance(raw, dict) and isinstance(raw.get("files"), list):
        raw = raw["files"]
        warnings.append("文件记录已从对象结构迁移为数组。")
    if not isinstance(raw, list):
        backup_file(path, "invalid_structure")
        raw = []
        warnings.append("文件记录结构错误，已重建空数组。")
    if warnings:
        write_json(path, raw)
    return {"items": raw, "warnings": warnings, "path": str(path)}


def guard_agent_run_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        run = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        move_to_corrupted(path, "invalid_agent_run_json")
        return None
    changed = False
    defaults = {
        "run_id": path.stem,
        "agent_type": "unknown",
        "status": "failed",
        "progress": 100,
        "current_step": "任务文件已修复",
        "logs": [],
        "result": None,
        "error": None,
        "created_at": "",
        "updated_at": "",
    }
    for key, value in defaults.items():
        if key not in run:
            run[key] = value
            changed = True
    if run.get("status") not in VALID_RUN_STATUSES:
        run["status"] = "failed"
        run["progress"] = 100
        run["error"] = "任务状态非法，已由系统自动修复为 failed。"
        run.setdefault("logs", []).append(run["error"])
        changed = True
    if changed:
        backup_file(path, "before_run_repair")
        write_json(path, run)
    return run
