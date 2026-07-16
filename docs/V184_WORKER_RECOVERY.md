# v1.8.4 Worker Recovery Acceptance

Version: `meizhaiseek v1.8.4`
Status: `not_run`

## Required Scenarios

- Controlled long task picked by worker.
- Worker stopped after task pickup.
- Zombie maintenance run.
- Worker restarted.
- Task reaches recovered/retried/failed terminal state, never permanent running.
- Terminal status and `row_version` are not overwritten by stale updates.

## Results

- General queue crash/restart: `not_run`
- Video queue crash/restart: `not_run`
- Dataset queue crash/restart: `not_run`
- Knowledge queue crash/restart: `not_run`
- Blueprint queue crash/restart: `not_run`
- Zombie recovery: `not_run`

