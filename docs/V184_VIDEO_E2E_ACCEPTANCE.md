# v1.8.4 Video Agent E2E Acceptance

Version: `meizhaiseek v1.8.4`
Model: `meizhaiseek 2.0`
Status: `not_run`

## Scope

- Platform submits `video_script_breakdown` through API, Redis/RQ, `worker-video`, local 8001 `/run`, artifact storage, SSE, and frontend state restore.
- Local video Agent path: `E:\USE\codexhome\fenge`
- Health URL: `http://127.0.0.1:8001/health`
- Test video: `E:\USE\codexhome\fenge\videos\test\1.mp4`
- Output directory: `E:\USE\codexhome\fenge\output\test`

## Required Evidence

- `run_id`, `conversation_id`, and `queue_job_id`.
- `agent_runs`, `agent_conversations`, and `agent_messages` rows.
- Worker consumption and real 8001 request.
- Run completed, assistant message completed, SSE completed event.
- Excel, JSON report, and evidence artifacts downloadable.
- `final_shots == data_columns == embedded_images`.

## Results

- 8001 health: `not_run`
- Success path: `not_run`
- Failure path with 8001 unavailable: `not_run`
- Artifact download: `not_run`
- Frontend Run card and conversation refresh: `not_run`

