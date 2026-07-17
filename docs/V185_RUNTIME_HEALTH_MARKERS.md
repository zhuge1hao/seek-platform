# v1.8.5 Runtime Health Markers

Version: `meizhaiseek v1.8.5`
Model: `meizhaiseek 2.0`
Status: cycle started

Runtime health reads validation markers from deployment environment variables. `.env` is local secret/runtime state and must not be committed.

## Marker Evidence

| Runtime field | Environment variable | Current status | Evidence |
| --- | --- | --- | --- |
| `multi_instance_sse_verified` | `MULTI_INSTANCE_SSE_VERIFIED` | `passed` | v1.8.4 P1 Redis pause/recovery and API B SSE evidence in `docs/DISTRIBUTED_RUN_EVENTS.md`, commit `2edcfd2215dfd8978b8ffb129b26ccde35921bf3`, executed 2026-07-16. |
| `redis_recovery_verified` | `REDIS_RECOVERY_VERIFIED` | `passed` | Redis pause `1.064s`, recovery `0s`, no duplicate terminal/assistant in `docs/DISTRIBUTED_RUN_EVENTS.md`, commit `2edcfd2215dfd8978b8ffb129b26ccde35921bf3`, executed 2026-07-16. |
| `worker_recovery_verified` | `WORKER_RECOVERY_VERIFIED` | `passed` | Worker crash/restart and zombie recovery in `docs/V184_WORKER_RECOVERY.md`, commit `2edcfd2215dfd8978b8ffb129b26ccde35921bf3`, executed 2026-07-16. |
| `video_queue_50_verified` | `VIDEO_QUEUE_50_VERIFIED` | `passed` | 48 mock + 2 real video jobs in `docs/V184_VIDEO_QUEUE_50.md`, commit `2edcfd2215dfd8978b8ffb129b26ccde35921bf3`, executed 2026-07-16. |
| `dataset_queue_verified` | `DATASET_QUEUE_VERIFIED` | `not_run` | v1.8.5 P0 pending. |
| `knowledge_queue_verified` | `KNOWLEDGE_QUEUE_VERIFIED` | `not_run` | v1.8.5 P0 pending. |
| `blueprint_queue_verified` | `BLUEPRINT_QUEUE_VERIFIED` | `not_run` | v1.8.5 P0 pending. |
| `artifact_s3_verified` | `ARTIFACT_S3_VERIFIED` | `not_run` | v1.8.5 P1 pending. |
| `pgvector_migration_verified` | `PGVECTOR_MIGRATION_VERIFIED` | `not_run` | v1.8.5 P2 pending. |
| `browser_agent_smoke_verified` | `BROWSER_AGENT_SMOKE_VERIFIED` | `not_run` | v1.8.5 P3 pending. |
| `capacity_last_verified_users` | `CAPACITY_LAST_VERIFIED_USERS` | `0` | v1.8.5 capacity not executed; 200/300/500-user tests are deferred to v1.8.6. |
| `capacity_last_test_passed` | `CAPACITY_LAST_TEST_PASSED` | `not_run` | v1.8.5 capacity not executed. |

## Rules

- Only real executed items may be configured as `passed`.
- Failed executed items must be configured as `failed`.
- Unexecuted items remain `not_run`.
- Do not commit `.env`; set deployment markers through environment or compose pass-through.
