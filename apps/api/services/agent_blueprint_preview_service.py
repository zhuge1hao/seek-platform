from __future__ import annotations

from typing import Any

from services.agent_blueprint_validator import INPUT_TYPES, RENDERERS


def input_preview(input_schema: dict[str, Any]) -> dict[str, Any]:
    fields = []
    for index, field in enumerate((input_schema or {}).get("fields") or []):
        if not isinstance(field, dict):
            continue
        field_type = str(field.get("type") or "text")
        fields.append({
            "field_id": field.get("field_id") or f"field_{index + 1}",
            "label": field.get("label") or field.get("field_id") or f"字段 {index + 1}",
            "type": field_type if field_type in INPUT_TYPES else "text",
            "required": bool(field.get("required")),
            "placeholder": field.get("placeholder") or "",
            "description": field.get("description") or "",
            "options": field.get("options") or [],
            "preview_only": True,
            "warning": "仅预览，不读取本地文件。" if field_type == "local_path" else "",
        })
    return {"preview_only": True, "fields": fields, "field_count": len(fields)}


def result_preview(output_schema: dict[str, Any], result_ui_config: dict[str, Any]) -> dict[str, Any]:
    sections = []
    for index, section in enumerate((output_schema or {}).get("sections") or []):
        if not isinstance(section, dict):
            continue
        sections.append({
            "section_id": section.get("section_id") or f"section_{index + 1}",
            "type": section.get("type") or "text",
            "label": section.get("label") or section.get("section_id") or f"区块 {index + 1}",
            "required": bool(section.get("required")),
            "order": section.get("order") or index + 1,
            "lazy": bool(section.get("lazy")),
        })
    renderer = str((result_ui_config or {}).get("renderer") or "generic_structured")
    return {
        "preview_only": True,
        "renderer": renderer if renderer in RENDERERS else "generic_structured",
        "tabs": (result_ui_config or {}).get("tabs") or [item["section_id"] for item in sections],
        "default_tab": (result_ui_config or {}).get("default_tab") or (sections[0]["section_id"] if sections else ""),
        "sections": sorted(sections, key=lambda item: int(item.get("order") or 0)),
    }
