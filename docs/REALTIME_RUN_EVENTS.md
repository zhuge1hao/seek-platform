# Realtime Run Events

v1.7.2 keeps the task realtime strategy as SSE + SQLite + polling fallback.

`agent_run_event_hub` is a lightweight in-process notification layer. It does not store business state and does not replace SQLite. `task_store` publishes a small run-change notification after SQLite writes; SSE waits on the hub first and re-reads SQLite before emitting data. Heartbeats still re-check SQLite, so API restarts or multi-worker deployments degrade to the durable polling behavior.

This intentionally avoids WebSocket, Redis, queues, and cross-process event guarantees for the current small local deployment profile.
