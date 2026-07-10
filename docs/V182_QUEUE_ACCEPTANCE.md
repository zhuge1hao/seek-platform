# v1.8.2 Queue Acceptance

Date: 2026-07-10

## Encoded

- Agent Run queue facade remains split by `general` and `video`.
- Dataset tasks route to `dataset`.
- Knowledge document ingest/reindex routes to `knowledge`.
- Blueprint test runs route to `blueprint`.
- `worker-general` consumes `general,dataset,knowledge,blueprint` in production compose.

## Executed

- Unit-level queue routing tests.
- QA document enqueue tests.
- Blueprint test-run enqueue and worker helper tests.
- 100-user 15-minute Locust run.
- Redis queue depth check after Locust.

## Passed

- `general` queue recovered from 658 pending jobs to 0 after scaling `worker-general=4`.
- `video`, `dataset`, `knowledge`, and `blueprint` queues were 0 after the recovery check.

## Not Executed

- Real Dataset clean/export worker acceptance.
- Real Knowledge document ingest worker acceptance with production file upload.
- Real Blueprint worker acceptance through Docker worker logs.
- Worker crash/restart and zombie recovery.
- 50 video jobs.

## Environment Limits

- Current compose does not define standalone `worker-dataset`, `worker-knowledge`, or `worker-blueprint`.
