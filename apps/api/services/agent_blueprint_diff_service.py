from __future__ import annotations

from typing import Any

from services import agent_blueprint_store as store


SECTION_LABELS = {
    "basic": "基本信息",
    "input_schema": "输入协议",
    "methodology": "方法论",
    "prompt_config": "Prompt",
    "execution_config": "执行配置",
    "output_schema": "输出协议",
    "result_ui_config": "结果 UI",
    "acceptance_rules": "验收规则",
}
ID_KEYS = {"fields": "field_id", "steps": "step_id", "sections": "section_id", "variables": "name"}


def _short(value: Any) -> Any:
    if isinstance(value, str) and len(value) > 500:
        return value[:500] + "..."
    return value


def _indexable(path: str, before: Any, after: Any) -> tuple[dict[str, Any], dict[str, Any]] | None:
    key = ID_KEYS.get(path.rsplit(".", 1)[-1])
    if not key or not isinstance(before, list) or not isinstance(after, list):
        return None
    if not all(isinstance(item, dict) and item.get(key) for item in before + after):
        return None
    return ({str(item[key]): item for item in before}, {str(item[key]): item for item in after})


def _diff(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        changes: list[dict[str, Any]] = []
        for key in sorted(set(before) | set(after)):
            next_path = f"{path}.{key}" if path else str(key)
            if key not in before:
                changes.append({"path": next_path, "change_type": "added", "before": None, "after": _short(after[key])})
            elif key not in after:
                changes.append({"path": next_path, "change_type": "removed", "before": _short(before[key]), "after": None})
            else:
                changes.extend(_diff(before[key], after[key], next_path))
        return changes
    indexed = _indexable(path, before, after)
    if indexed:
        left, right = indexed
        changes = []
        for key in sorted(set(left) | set(right)):
            next_path = f"{path}.{key}" if path else key
            if key not in left:
                changes.append({"path": next_path, "change_type": "added", "before": None, "after": _short(right[key])})
            elif key not in right:
                changes.append({"path": next_path, "change_type": "removed", "before": _short(left[key]), "after": None})
            else:
                changes.extend(_diff(left[key], right[key], next_path))
        return changes
    if isinstance(before, list) and isinstance(after, list):
        changes = []
        for index in range(max(len(before), len(after))):
            next_path = f"{path}[{index}]"
            if index >= len(before):
                changes.append({"path": next_path, "change_type": "added", "before": None, "after": _short(after[index])})
            elif index >= len(after):
                changes.append({"path": next_path, "change_type": "removed", "before": _short(before[index]), "after": None})
            else:
                changes.extend(_diff(before[index], after[index], next_path))
        return changes
    return [{"path": path, "change_type": "changed", "before": _short(before), "after": _short(after)}]


def compare_blueprint_versions(blueprint_id: str, from_version_id: str, to_version_id: str) -> dict[str, Any]:
    blueprint = store.get_blueprint(blueprint_id)
    before = store.get_version_for_blueprint(blueprint_id, from_version_id)
    after = store.get_version_for_blueprint(blueprint_id, to_version_id)
    if not blueprint or not before or not after:
        raise ValueError("blueprint or version not found")
    sections = []
    totals = {"added": 0, "removed": 0, "changed": 0}
    basic = {key: blueprint.get(key) for key in ("agent_id", "name", "display_name", "description", "category", "icon", "status")}
    for key, left, right in [
        ("basic", basic, basic),
        ("input_schema", before.get("input_schema") or {}, after.get("input_schema") or {}),
        ("methodology", before.get("methodology") or {}, after.get("methodology") or {}),
        ("prompt_config", before.get("prompt_config") or {}, after.get("prompt_config") or {}),
        ("execution_config", before.get("execution_config") or {}, after.get("execution_config") or {}),
        ("output_schema", before.get("output_schema") or {}, after.get("output_schema") or {}),
        ("result_ui_config", before.get("result_ui_config") or {}, after.get("result_ui_config") or {}),
        ("acceptance_rules", before.get("acceptance_rules") or {}, after.get("acceptance_rules") or {}),
    ]:
        changes = _diff(left, right, key)
        for change in changes:
            totals[change["change_type"]] = totals.get(change["change_type"], 0) + 1
        sections.append({"section": key, "label": SECTION_LABELS[key], "has_changes": bool(changes), "changes": changes})
    return {
        "blueprint_id": blueprint_id,
        "from_version": {"version_id": from_version_id, "version_number": before["version_number"]},
        "to_version": {"version_id": to_version_id, "version_number": after["version_number"]},
        "has_changes": any(section["has_changes"] for section in sections),
        "summary": totals,
        "sections": sections,
    }
