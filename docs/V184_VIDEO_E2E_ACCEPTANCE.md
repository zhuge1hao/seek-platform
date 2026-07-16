# v1.8.4 Video Agent E2E Acceptance

Version: `meizhaiseek v1.8.4`
Model: `meizhaiseek 2.0`
Status: `passed` for backend/API/RQ/worker-video/8001/SSE/S3 artifact chain; frontend browser smoke remains `not_run`.

## Scope

- Platform submits `video_script_breakdown` through API, Redis/RQ, `worker-video`, local 8001 `/run`, artifact storage, SSE, and frontend state restore.
- Local video Agent path: `E:\USE\codexhome\fenge`
- Health URL: `http://127.0.0.1:8001/health`
- Test video: `E:\USE\codexhome\fenge\videos\test\1.mp4`
- Output directory used for Docker E2E: `E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api\runtime\video-agent-output\v184-p0-*`

## Required Evidence

- `run_id`, `conversation_id`, and `queue_job_id`.
- `agent_runs`, `agent_conversations`, and `agent_messages` rows.
- Worker consumption and real 8001 request.
- Run completed, assistant message completed, SSE completed event.
- Excel, JSON report, and evidence artifacts downloadable.
- `final_shots == data_columns == embedded_images`.

## Results

- 8001 health: `passed`
  - `GET http://127.0.0.1:8001/health` returned `status=ok`, service `shot-cutting-agent`, version `0.1.0`.
  - API container also reached `http://host.docker.internal:8001/health`.
- Success path backend chain: `passed`
  - Command: `docker exec -w /app/apps/api meizhaiseek-platform-api-1 python scripts/v184_video_e2e_smoke.py --api-base http://127.0.0.1:8000`.
  - `run_id=run_20260716094829_ecf1360b`.
  - `conversation_id=conv_20260716094829_e4b8023b`.
  - `queue_job_id=agent-run-run_20260716094829_ecf1360b`.
  - DB rows: `agent_runs=1`, `agent_conversations=1`, `agent_messages=2`, `artifacts=260`, `debug_payloads=1`.
  - `worker-video` consumed the job and SSE emitted running/progress/completed events.
  - 8001 returned completed; platform run status is `completed`; assistant message status is `completed`.
  - `GET /api/conversations` contained the new conversation after submit.
- Artifact download: `passed`
  - Excel download: HTTP 200, content type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, sampled bytes `821300`.
  - JSON report download: HTTP 200, content type `application/json`, sampled bytes `43936`.
  - Evidence image download: HTTP 200, content type `image/jpeg`, sampled bytes `98263`.
  - Folder manifest download: HTTP 200, content type `application/json`, sampled bytes `27189`.
- Shot consistency: `passed`
  - `final_shots=45`, `data_columns=45`, `embedded_images=45`.
  - Evidence artifacts registered: `251` image files.
- Failure path with 8001 unavailable: `passed`
  - Evidence run: `run_20260716093735_2b597cc0`.
  - Worker consumed the run and wrote terminal `failed` status when the container-local Connector pointed at unavailable `http://127.0.0.1:8001`.
  - Conversation `conv_20260716093735_f215d04d` contains `user completed=1` and `assistant failed=1`; no duplicate assistant message was observed.
  - Error was written to both run and assistant message; the run was not left permanently running.
- Frontend Run card browser smoke: `not_run`
  - No real browser click-through was executed in this P0 pass.
  - API-level conversation list refresh and SSE event delivery were verified.

## Fixes Made During P0

- Connector runtime repair now honors `VIDEO_AGENT_BASE_URL` for Docker workers when the stored video connector still points to local loopback.
- Artifact path resolution can translate Windows host paths under `apps/api/runtime` to the mounted container path.
- Video result normalization handles Windows `video_file` paths when deriving the target stem/name, so evidence images are registered.
- S3 artifact downloads now use RFC 5987 `Content-Disposition` for non-ASCII filenames.

## Still Not Executed

- Direct browser verification of the `/agent` Run card visual update.
- Direct browser verification of left-side conversation refresh.
- Cancel/retry/user-isolation browser flows for this video run.
