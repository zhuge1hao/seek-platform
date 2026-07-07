# Distributed Run Events

SSE remains the public realtime protocol:

```text
GET /api/agent-runs/{run_id}/events
```

Modes:

- `EVENT_BACKEND=memory`: in-process event hub for local development.
- `EVENT_BACKEND=redis`: Redis Pub/Sub wakeups for multi-instance API deployments.

Redis messages are lightweight notifications only. They do not contain raw responses, full prompts, or full workflow options. The API instance always re-reads DB summary before sending an SSE event.
