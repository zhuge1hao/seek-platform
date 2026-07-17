# v1.8.7 Browser Agent Smoke

## Status

- Method: `Playwright / Chrome`
- Executed: `passed`
- Core run-card smoke: `passed`
- Full browser acceptance marker: `failed`

## Required Evidence

- Login and `/agent` load.
- Normal Agent run and video Agent run when 8001 is available.
- Left conversation refresh.
- Run-card queued/running/progress/completed updates.
- Refresh restore.
- Failed, cancelled, and retry flows.
- User isolation.
- Artifact downloads.
- Console/network/SSE checks.

## Results

Executed on 2026-07-17 against the Docker production stack and `http://localhost:3000`.

Command:

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\web
npm.cmd run e2e:agent -- --project=chrome
```

Evidence:

- Test file: `apps/web/e2e/agent-run-smoke.spec.ts`.
- Temporary operator users were created inside the API container; passwords were passed only through environment variables and were not written to code or docs.
- Passing run: `run_20260717094756_2c66e2b0`.
- Conversation: `conv_20260717094756_b1a833d3`.
- Agent type: `blue_ocean`.
- Terminal status: `failed`, which validates the failed Run-card path for the currently unavailable generic local-agent execution.
- Playwright result: `1 passed`.

Passed checks:

- Login via the real UI.
- Open `/agent`.
- Submit a normal Agent Run through the frontend.
- `POST /api/agent-runs` returned a real `run_id`, `conversation_id`, and queue job id.
- Left conversation route updated with the backend conversation id.
- Run card displayed the real run id.
- Reload restored the Run card from backend state.
- Owner could read the conversation and run.
- A second user received `403/404` for the first user's run/conversation.
- Logging in as the second user and opening the first user's conversation URL did not reveal the run.

Not executed:

- Video Agent browser run with 8001 available.
- Excel/JSON/evidence downloads from the browser UI.
- Cancel button behavior.
- Retry button behavior.
- SSE terminal-close timing from browser DevTools.
- Page unload/run-switch abort observation.

Outcome:

- Core Run-card/conversation refresh smoke is `passed`.
- `BROWSER_AGENT_SMOKE_VERIFIED` must remain `failed` or `not_run` until the full browser matrix above is executed. It must not be marked `passed` from this partial smoke alone.
