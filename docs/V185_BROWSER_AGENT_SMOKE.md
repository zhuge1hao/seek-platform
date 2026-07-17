# v1.8.5 Browser Agent Smoke

Version: meizhaiseek v1.8.5
Model: meizhaiseek 2.0

## Status

| Check | Executed | Result |
| --- | --- | --- |
| Login and open `/agent` | not_run | not_run |
| Normal Agent Run card queued/running/progress/completed | not_run | not_run |
| Left conversation refresh after backend conversation creation | not_run | not_run |
| Refresh restores run card state | not_run | not_run |
| Failure/cancel/retry UI states | not_run | not_run |
| User isolation in browser | not_run | not_run |
| Video completed with Excel/JSON/evidence UI downloads | not_run | not_run |
| Console/network/SSE terminal behavior | not_run | not_run |

## Not Run

Browser smoke was not executed in this pass because the production Docker stack was unavailable. The v1.8.3/v1.8.4 frontend fixes remain covered by prior API/build tests, but `BROWSER_AGENT_SMOKE_VERIFIED` must stay `not_run`.

## Next Review

v1.8.7 follow-up executed a Playwright/Chrome core smoke:

- Run: `run_20260717094756_2c66e2b0`.
- Conversation: `conv_20260717094756_b1a833d3`.
- Result: core Run-card/conversation refresh/user isolation smoke `passed`.
- Remaining: video UI artifacts, cancel, retry, and browser SSE terminal-close checks are still not executed, so the full browser marker is not `passed`.
