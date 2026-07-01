# Frontend Data Layer

v1.6.5 keeps `apps/web/src/lib/api.ts` as the single HTTP, auth, and error handling layer. SWR hooks only call functions from `api.ts`.

SWR-backed reads:

- Runtime/storage health and current user
- Agent/QA conversations
- Knowledge stats, model status, and document list
- Agent connectors/configs and skill templates
- Debug payload list
- Dataset list, uploaded file list, mapping templates
- Admin users

Non-SWR paths:

- POST/PUT/DELETE actions
- Uploads, downloads, blob previews, and large detail payloads
- `/agent` run summary/result status updates

Mutation rule: write through `api.ts`, then call the matching SWR `mutate`.

`/agent` run updates use `useAgentRunEvents` first and fall back to `useAgentRunPolling`; SWR must not poll run summary.
