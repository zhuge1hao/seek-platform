from __future__ import annotations

import re
from typing import Any

from services import agent_blueprint_service, agent_blueprint_store, audit_log_service
from services.agent_registry import list_agents


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip()).strip("_").lower()
    return slug or "agent"


def _blueprints_by_agent() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for blueprint in agent_blueprint_store.list_blueprints(include_unpublished=True):
        grouped.setdefault(str(blueprint.get("agent_id") or ""), []).append(blueprint)
    return grouped


def preview_registry_sync() -> dict[str, Any]:
    agents = list_agents()
    registry_by_agent = {str(agent.get("agent_type") or ""): agent for agent in agents if agent.get("agent_type")}
    blueprints_by_agent = _blueprints_by_agent()
    blueprint_agent_ids = set(blueprints_by_agent)
    registry_agent_ids = set(registry_by_agent)

    matched = []
    conflicts = []
    disabled = []
    deprecated = []
    for agent_id in sorted(registry_agent_ids & blueprint_agent_ids):
        bindings = blueprints_by_agent[agent_id]
        agent = registry_by_agent[agent_id]
        matched.append({"agent_id": agent_id, "agent": agent, "blueprints": bindings})
        if len(bindings) > 1:
            conflicts.append({"agent_id": agent_id, "blueprints": bindings})
        for blueprint in bindings:
            if blueprint.get("status") == "disabled":
                disabled.append({"agent_id": agent_id, "blueprint": blueprint})
            if blueprint.get("status") == "deprecated":
                deprecated.append({"agent_id": agent_id, "blueprint": blueprint})

    return {
        "registry_only": [registry_by_agent[agent_id] for agent_id in sorted(registry_agent_ids - blueprint_agent_ids)],
        "blueprint_only": [item for agent_id in sorted(blueprint_agent_ids - registry_agent_ids) for item in blueprints_by_agent.get(agent_id, []) if agent_id],
        "matched": matched,
        "agent_id_conflicts": conflicts,
        "disabled_bindings": disabled,
        "deprecated_bindings": deprecated,
    }


def apply_registry_sync(agent_ids: list[str], user: dict[str, Any]) -> dict[str, Any]:
    preview = preview_registry_sync()
    registry_only = {str(agent.get("agent_type")): agent for agent in preview["registry_only"]}
    created = []
    skipped = []
    for agent_id in agent_ids:
        agent = registry_only.get(agent_id)
        if not agent:
            skipped.append({"agent_id": agent_id, "reason": "not_registry_only"})
            continue
        blueprint_id = f"bp_registry_{_slug(agent_id)}"
        suffix = 2
        while agent_blueprint_store.get_blueprint(blueprint_id):
            blueprint_id = f"bp_registry_{_slug(agent_id)}_{suffix}"
            suffix += 1
        result = agent_blueprint_service.create_draft(
            {
                "blueprint_id": blueprint_id,
                "agent_id": agent_id,
                "name": _slug(agent_id),
                "display_name": agent.get("name") or agent_id,
                "description": agent.get("description") or "",
                "category": agent.get("category") or "",
                "metadata": {"registry_sync": True},
            },
            user,
        )
        created.append(result["blueprint"])
        audit_log_service.write_log("agent_blueprint.registry_sync.create_draft", "success", user, blueprint_id, {"agent_id": agent_id})
    return {"created": created, "skipped": skipped, "preview": preview_registry_sync()}
