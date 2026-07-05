# Registry Blueprint Sync

v1.7.2 adds safe Agent Registry to Blueprint reconciliation.

`GET /api/agent-blueprints/registry-sync/preview` reports:

- `registry_only`
- `blueprint_only`
- `matched`
- `agent_id_conflicts`
- `disabled_bindings`
- `deprecated_bindings`

`POST /api/agent-blueprints/registry-sync/apply` accepts `{"agent_ids": ["..."], "create_as": "draft"}` and only creates draft Blueprints for registry-only agents. It never publishes, never overwrites existing published Blueprints, never creates methodology or prompt content, and writes audit logs for created drafts.
