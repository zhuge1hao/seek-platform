# Realtime Run Events

v1.8 keeps the task realtime strategy as SSE + durable DB summary + polling fallback.

`agent_run_event_hub` is a lightweight in-process notification layer. It does not store business state and does not replace SQLite. `task_store` publishes a small run-change notification after SQLite writes; SSE waits on the hub first and re-reads SQLite before emitting data. Heartbeats still re-check SQLite, so API restarts or multi-worker deployments degrade to the durable polling behavior.

For local development, `EVENT_BACKEND=memory` keeps the v1.7.2 in-process behavior.

For production, `EVENT_BACKEND=redis` uses `agent_run_event_bus` and Redis Pub/Sub. Redis messages are lightweight wakeups only; they do not include raw response, full prompt, full workflow options, or business truth. Each SSE response re-reads the run summary from the configured DB before sending data to the browser.

This intentionally avoids WebSocket. Polling fallback remains available after SSE errors, API restarts, Redis interruptions, or page visibility changes.

## v1.8.2 P2 Client Backoff Update - 2026-07-10

Encoded:

- Agent Run SSE client retry uses 1s/2s/4s/8s/16s/30s exponential backoff with jitter.
- Browser network recovery triggers an immediate retry.
- HTTP 401/403/404 stops retry instead of looping forever.
- Completed, failed, and cancelled runs close the stream.
- Component unmount and run switch abort the previous stream.
- Existing polling fallback remains the durable fallback and is stopped when SSE reconnects.

Executed:

- Frontend production build passed.

Not executed:

- Redis pause/recovery browser-level reconnection timing test.
- Multi-tab duplicate SSE connection stress test.
# v1.8.5 Browser/SSE Status

- v1.8.4 Redis pause/recovery evidence remains the latest passed distributed event record.
- v1.8.5 browser-side SSE terminal close, retry, cancel, and artifact refresh smoke is `not_run` until the Docker stack and browser smoke are available.

## v1.8.7 Browser Event Smoke

- Playwright/Chrome core smoke passed for run `run_20260717094756_2c66e2b0`.
- The browser observed the Run-card restore after reload from durable API state.
- User-isolation checks intentionally produced `403/404` responses and did not reveal another user's run.
- Browser DevTools timing for SSE terminal close, page unload abort, and run-switch abort remains `not_run`.
