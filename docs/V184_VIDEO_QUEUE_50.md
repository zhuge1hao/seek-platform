# v1.8.4 50 Video Jobs Acceptance

Version: `meizhaiseek v1.8.4`
Model: `meizhaiseek 2.0`
Executed: `2026-07-16`
Status: `passed`

## Scenario

- Submitted 50 video jobs.
- 48 jobs were controlled mock video RQ jobs.
- 2 jobs were real `video_script_breakdown` API jobs using local video Agent 8001 and `E:\USE\codexhome\fenge\videos\test\1.mp4`.
- `worker-video` was paused before submission to prove queue buildup, then unpaused.
- One queued mock run was cancelled before execution.

## Results

- Submitted: `50`.
- Mock video jobs: `48`.
- Real video jobs: `2`, status `passed`.
- Completed: `49`.
- Failed: `0`.
- Cancelled: `1`.
- Max queued: `48`.
- Max executing: `2`.
- Average wait time: `3.082s`.
- Max wait time: `77.0s`.
- Average execution time: `7.612s`.
- Max execution time: `117.0s`.
- Final `video` queue: `queued=0`, `started=0`.
- Other queues blocked: `false`.
- API `/health` stayed reachable.
- `/api/agents` stayed readable.
- Login token creation stayed available.

## Queue Snapshot During Backlog

| Queue | Queued | Started |
| --- | ---: | ---: |
| general | 0 | 0 |
| video | 48 | 0 |
| dataset | 0 | 0 |
| knowledge | 0 | 0 |
| blueprint | 0 | 0 |

## Sample Jobs

- `run_20260716181437_de18d0ee`, job `acceptance-video-50-run_20260716181437_de18d0ee`
- `run_20260716181437_8eaedf9c`, job `acceptance-video-50-run_20260716181437_8eaedf9c`
- `run_20260716181437_790d28a2`, job `acceptance-video-50-run_20260716181437_790d28a2`
- `run_20260716181437_975103db`, job `acceptance-video-50-run_20260716181437_975103db`
- `run_20260716181437_29a4856c`, job `acceptance-video-50-run_20260716181437_29a4856c`

## Notes

- The test did not run 50 real large video jobs.
- Real jobs were limited to 2 small-video jobs.
- Local video files and video outputs were not staged or committed.
