# v1.8.9 Browser Matrix

Version: `meizhaiseek v1.8.9`

## Status

- Real video success: `passed`.
- Excel download: `passed`.
- JSON download: `passed`.
- Evidence download: `passed`.
- Queued/running cancel: `passed`.
- Retry: `passed`.
- Run switch abort: `passed`.
- SSE terminal close: `passed`.
- Browser user isolation: `passed`.
- Marker target: `BROWSER_AGENT_SMOKE_VERIFIED=passed` for the v1.8.9 production stack started with `docker-compose.v189.override.yml`.

## Evidence

- Environment: production Docker stack with `worker-general=4`, `worker-video=2`, local video Agent `http://127.0.0.1:8001` healthy.
- Command: `npm.cmd run e2e:agent -- --project=chrome --workers=1`.
- Result: `6 passed` in `2.3m` on 2026-07-19 after retrying a prior Playwright request timeout in the video polling spec.
- Specs: `agent-cancel-switch.spec.ts`, `agent-retry-isolation.spec.ts`, `agent-run-smoke.spec.ts`, `agent-sse-lifecycle.spec.ts`, `agent-video-download.spec.ts`.
- Browser users: temporary admin `v189_e2e_a_20260719175216` and temporary viewer `v189_e2e_b_20260719175216`; passwords were generated in memory and were not written to the repo.
- Final P9 rerun: `npm.cmd run e2e:agent -- --project=chrome --workers=1` returned `6 passed` in `2.3m` with temporary admin `e2e_v189_full2_a_20260719194622` and temporary viewer `e2e_v189_full2_b_20260719194622`.
- Retry note: an intermediate P9 full rerun produced `5 passed / 1 failed` because `agent-run-smoke.spec.ts` raced initial conversation restoration; the spec now clears `meizhaiseek_active_conversation_id`, waits for initial conversation loading, opens a fresh conversation, and the failed spec plus full matrix were rerun successfully.
- Real video run: `run_20260719095232_40ade676`, conversation `conv_20260719095232_4cab920d`, terminal status `completed`.
- Video input: `E:\USE\codexhome\fenge\videos\test\1.mp4`.
- Video result counts: `raw_shot_count=161`, `model_optimized_shot_count=45`, `excel_column_count=45`, `excel_image_count=45`, `artifact_count=261`.
- Artifact index: `2` Excel files, `7` JSON files, `251` evidence images, `261/261` files with backend download URLs.
- Downloads: Playwright requested one Excel, one JSON, and one evidence image through `/api/agent-runs/{run_id}/artifacts/{artifact_id}/download`; all returned HTTP `200` and non-empty bodies.
- Cancel evidence: `agent-cancel-switch.spec.ts` cancelled a real video run, repeated cancel idempotently, verified persisted `cancelled` status after page reload, and verified no later completed overwrite.
- Run switch evidence: browser fetch instrumentation observed the previous `/events` request AbortSignal firing after switching from a non-terminal run conversation to another conversation; stale run ID was not visible in the target conversation.
- Retry evidence: failed video run retried into a distinct new run in the same conversation; original failed run remained present and cross-user requests returned `403` or `404`.
- SSE evidence: terminal stream response contained the run ID and terminal/status event, then ended without `raw_response`, `workflow_options`, authorization, bearer token, `api_key`, or `secret`.
- User isolation evidence: viewer user could not access the admin user's run, summary, events, or conversation by direct backend request.
