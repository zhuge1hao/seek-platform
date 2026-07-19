# v1.8.9 Multi-instance SSE

Version: `meizhaiseek v1.8.9`

## Status

- API instance count: `2`.
- Cross-instance run events: `passed`.
- Redis pause/recovery: `passed`.
- API restart: `passed`.
- Event propagation p95: `3.938s`.
- Marker target: `MULTI_INSTANCE_SSE_VERIFIED=passed` and `REDIS_RECOVERY_VERIFIED=passed` for the v1.8.9 stack started with `docker-compose.v189.override.yml`.

## Evidence

- Command: `python apps/api/scripts/acceptance_redis_recovery.py --api-a http://127.0.0.1:8000 --api-b-port 8002 --json-report`.
- API A: `http://127.0.0.1:8000`; API B: `http://127.0.0.1:8002`.
- API A worker-backed run: `run_20260719100014_839d7813`, conversation `conv_20260719100014_cbecf146`, queue job `agent-run-run_20260719100014_839d7813`, terminal `completed`.
- API B events for API-created run: `running progress=10`, then `completed progress=100`.
- Redis pause/recovery run: `run_20260719180016_cc5e7399`; API B received `running progress=10`, `running progress=33`, `completed progress=100`.
- PostgreSQL fallback during Redis pause: API B summary returned `status=running`, `progress=66`.
- Redis pause duration: `1.099s`; recovery lag for new events: `0s`.
- Post-recovery run: `run_20260719180020_4b1a2df8`, terminal `completed`.
- API A restart duration: `3.684s`; post-restart run `run_20260719100026_aaf051f4` terminal `completed`.
- Duplicate terminal: `false`.
- Assistant messages: `1` for Redis-pause run, `1` for post-recovery run, `1` for post-restart run.
- Sensitive-field check: `passed`; SSE payloads did not include `raw_response`, `prompt`, `workflow_options`, authorization, bearer tokens, `api_key`, `secret`, or `password`.

## Safety

SSE payloads must not include `raw_response`, `prompt`, `workflow_options`, `token`, `api_key`, `secret`, `password`, or complete local filesystem paths.
