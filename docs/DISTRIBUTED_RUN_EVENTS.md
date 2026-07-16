# Distributed Run Events

## v1.8.4 Acceptance Status

- Multi-instance SSE: `passed`
- Redis interruption fallback: `passed`
- Polling fallback / DB summary fallback: `passed`
- Terminal event close: `passed`
- Secret/raw payload redaction: `passed`

## v1.8.4 Redis Pause/Recovery Evidence - 2026-07-16

- Primary run: `run_20260716181758_d2867ca8`.
- Post-recovery run: `run_20260716181802_b723d0bd`.
- Redis pause duration: `1.064s`.
- Redis recovery time after unpause: `0s`.
- Fallback DB summary while Redis was paused: status `running`, progress `66`.
- Pre-pause/terminal events observed by API B: `running 10`, `running 33`, `completed 100`.
- Post-recovery events observed: `running`, `completed`.
- Event p95: `2.014s`.
- Duplicate terminal event: `false`.
- Duplicate assistant message: `false`; assistant messages remained `1` for each run.
- Sensitive leak scan: `passed`; observed events did not include raw response, Prompt, workflow options, token, API key, or secret fields.

SSE remains the public realtime protocol:

```text
GET /api/agent-runs/{run_id}/events
```

Modes:

- `EVENT_BACKEND=memory`: in-process event hub for local development.
- `EVENT_BACKEND=redis`: Redis Pub/Sub wakeups for multi-instance API deployments.

Redis messages are lightweight notifications only. They do not contain raw responses, full prompts, or full workflow options. The API instance always re-reads DB summary before sending an SSE event.
