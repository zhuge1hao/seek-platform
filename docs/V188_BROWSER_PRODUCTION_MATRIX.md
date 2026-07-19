# v1.8.8 Browser Production Matrix

Version: `meizhaiseek v1.8.8`
Model: `meizhaiseek 2.0`

## Status

- Ordinary Agent browser smoke: `passed` on 2026-07-19 with temporary API `127.0.0.1:8018` and Web `127.0.0.1:3000`.
- Video success/download matrix: `not_run`; requires local video Agent `http://127.0.0.1:8001`, worker-video, and `MEIZHAISEEK_E2E_RUN_VIDEO=1`.
- Video failure/retry/isolation matrix: `passed` through API-level Playwright failed-video retry and user isolation checks.
- SSE lifecycle matrix: `passed` for terminal failed stream close and sensitive-field checks.
- Browser marker target: keep `BROWSER_AGENT_SMOKE_VERIFIED=failed` until the real video success/download/cancel matrix is executed.

## 2026-07-19 Evidence

- Command: `npm.cmd run e2e:agent -- --project=chrome`.
- Result: `3 passed, 1 skipped`.
- Passed: UI login, ordinary Agent run submit, run_id/conversation_id return, left conversation restore, reload restore, API user isolation, failed-video retry/isolation, SSE terminal close, and SSE sensitive-field filtering.
- Skipped: real video download matrix because local video Agent `127.0.0.1:8001` was unavailable and `MEIZHAISEEK_E2E_RUN_VIDEO` was not enabled.

## Commands

```powershell
cd apps\web
npm.cmd ci
npm.cmd run build
npm.cmd run e2e:agent -- --project=chrome
```

Optional real video success/download:

```powershell
$env:MEIZHAISEEK_E2E_RUN_VIDEO='1'
$env:MEIZHAISEEK_E2E_VIDEO_PATH='E:\USE\codexhome\fenge\videos\test\1.mp4'
npm.cmd run e2e:agent -- --project=chrome
```

## Evidence To Record

- run_id, conversation_id, terminal status, assistant message count, console errors.
- Excel/JSON/evidence download HTTP status and byte length.
- SSE terminal close and absence of `raw_response`, `workflow_options`, token, API key, and secret strings.
