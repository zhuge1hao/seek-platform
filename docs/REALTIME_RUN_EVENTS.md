# Realtime Run Events

v1.8 keeps the task realtime strategy as SSE + durable DB summary + polling fallback.

`agent_run_event_hub` is a lightweight in-process notification layer. It does not store business state and does not replace SQLite. `task_store` publishes a small run-change notification after SQLite writes; SSE waits on the hub first and re-reads SQLite before emitting data. Heartbeats still re-check SQLite, so API restarts or multi-worker deployments degrade to the durable polling behavior.

For local development, `EVENT_BACKEND=memory` keeps the v1.7.2 in-process behavior.

For production, `EVENT_BACKEND=redis` uses `agent_run_event_bus` and Redis Pub/Sub. Redis messages are lightweight wakeups only; they do not include raw response, full prompt, full workflow options, or business truth. Each SSE response re-reads the run summary from the configured DB before sending data to the browser.

This intentionally avoids WebSocket. Polling fallback remains available after SSE errors, API restarts, Redis interruptions, or page visibility changes.
