# v1.8.4 Worker Recovery Acceptance

Version: `meizhaiseek v1.8.4`
Model: `meizhaiseek 2.0`
Executed: `2026-07-16`
Status: `passed`

## Environment

- Branch: `stabilization/v1.8.4`
- Docker topology: PostgreSQL, Redis, MinIO, API, Web, Nginx, `worker-general` x4, `worker-video` x2.
- `worker-general` consumes `general,dataset,knowledge,blueprint`.
- Standalone dataset/knowledge/blueprint workers are not configured.
- `worker-video` consumes `video`.
- PostgreSQL remains the run state source of truth; Redis/RQ is execution infrastructure.

## Worker Crash/Restart

| Queue | Consumer | Run ID | Job ID | Stopped worker | Final status | Row version | Artifact count | Queue depth | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| general | worker-general | `run_20260716181405_cd91a5c3` | `acceptance-worker-general-run_20260716181405_cd91a5c3` | `61b8cb887eca` | `failed` | `3 -> 4` | `0` | `queued=0, started=0` | `passed` |
| video | worker-video | `run_20260716181410_d867a363` | `acceptance-worker-video-run_20260716181410_d867a363` | `cfcf88f87b5c` | `failed` | `3 -> 4` | `0` | `queued=0, started=0` | `passed` |
| knowledge | worker-general | `run_20260716181414_1a49583d` | `acceptance-worker-knowledge-run_20260716181414_1a49583d` | `61b8cb887eca` | `failed` | `3 -> 4` | `0` | `queued=0, started=0` | `passed` |
| dataset | worker-general | `run_20260716181418_21f5a012` | `acceptance-worker-dataset-run_20260716181418_21f5a012` | `61b8cb887eca` | `failed` | `3 -> 4` | `0` | `queued=0, started=0` | `passed` |
| blueprint | worker-general | `run_20260716181423_15894ff1` | `acceptance-worker-blueprint-run_20260716181423_15894ff1` | `61b8cb887eca` | `failed` | `3 -> 4` | `0` | `queued=0, started=0` | `passed` |

Each queue used a controlled acceptance RQ job. The worker was killed after the run entered `running`; stale maintenance then marked the run `failed` with a queryable error. Acceptance jobs do not generate business artifacts, so duplicate artifact validation used `artifact_count=0`.

## Zombie Recovery

- Stale run: `run_20260716181429_b42b4460`, status changed from `running` to `failed`.
- Active run: `run_20260716181429_37bd998d`, remained `running`.
- Completed protection: remained `completed`.
- Failed protection: remained `failed`.
- Cancelled protection: remained `cancelled`.
- Maintenance result: `repaired=1`, `timeout_minutes=1`.
- Result: `passed`.

## Terminal Protection

- Cancelled protection run: `run_20260716181429_0c3598e6`, late completed update did not overwrite `cancelled`.
- Failed protection run: `run_20260716181429_3365a57c`, late running update did not overwrite `failed`.
- Result: `passed`.

## Notes

- The first two script attempts failed before this passing run. Root cause: host-side validation scripts normalized `APP_DATABASE_URL` to `127.0.0.1` and accidentally passed that value into `docker compose`, causing recreated workers to connect to localhost inside the container. The scripts now avoid passing host-normalized DB/Redis URLs into Docker CLI calls.
- RQ `StartedJobRegistry` can retain killed acceptance jobs until cleanup. The validation script removes only job IDs prefixed with `acceptance-worker-`; it does not remove business jobs.
