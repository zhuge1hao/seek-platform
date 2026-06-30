import json
from datetime import datetime
from typing import Any


SCHEMA_VERSION = "1.0"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def wrap_agent_configs(configs: list[dict[str, Any]], data_source: str = "runtime") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_iso(),
        "data_source": data_source,
        "agents": {config["agent_type"]: config for config in configs if config.get("agent_type")},
    }


def unwrap_agent_configs(raw: Any) -> tuple[list[dict[str, Any]], bool, str | None]:
    if isinstance(raw, list):
        return raw, True, None
    if isinstance(raw, dict) and isinstance(raw.get("agents"), dict):
        return list(raw["agents"].values()), raw.get("schema_version") != SCHEMA_VERSION, raw.get("schema_version")
    raise ValueError("agent_configs 格式错误，应为旧数组或包含 agents 的对象。")


def wrap_skill_templates(templates: list[dict[str, Any]], data_source: str = "runtime") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_iso(),
        "data_source": data_source,
        "skills": {template["id"]: template for template in templates if template.get("id")},
    }


def unwrap_skill_templates(raw: Any) -> tuple[list[dict[str, Any]], bool, str | None]:
    if isinstance(raw, list):
        return raw, True, None
    if isinstance(raw, dict) and isinstance(raw.get("skills"), dict):
        return list(raw["skills"].values()), raw.get("schema_version") != SCHEMA_VERSION, raw.get("schema_version")
    raise ValueError("skill_templates 格式错误，应为旧数组或包含 skills 的对象。")


def write_json(path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
