# Observability

v1.8 adds:

- `X-Request-ID` on responses.
- Structured request timing through middleware.
- Optional `/metrics` endpoint when `prometheus-client` is installed.
- Runtime health component status for database, Redis, queue, events, artifact storage, RAG, and capacity profile.

Metrics should cover HTTP, DB pool, Redis, queue, worker, SSE, DeepSeek, 8001, and artifact paths as they are wired into production.

Secrets, connection strings, raw prompts, raw responses, and full workflow options must not be returned from health or metrics endpoints.
