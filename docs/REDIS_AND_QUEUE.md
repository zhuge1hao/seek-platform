# Redis And Queue

v1.8 uses Redis for cache, rate limit, RQ queue, and distributed event wakeups. Redis keys use the `meizhaiseek:` prefix.

Queue modes:

- `TASK_QUEUE_BACKEND=inline`: local development; FastAPI background task executes the run.
- `TASK_QUEUE_BACKEND=redis`: production; `POST /api/agent-runs` returns after creating the run and enqueues worker execution.

Worker entry:

```powershell
python -m workers.worker
```

Current status: Agent Run execution is wired through the queue facade. Dataset/document/Blueprint test run queue migration remains a v1.8 follow-up.
