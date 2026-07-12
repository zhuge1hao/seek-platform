# v1.8.3 Queue Acceptance

## Target

- QA/Knowledge, Dataset, and Blueprint queue paths return job IDs quickly and use PostgreSQL as the status source.

## Current Status

- P0 unit proof executed and passed.
- QA/Knowledge Redis upload and reindex enqueue tests pass.
- Worker cancelled guard and failure chunk cleanup tests pass.
- Dataset `dataset_clean` Redis enqueue test passes.
- Blueprint Redis enqueue and worker-start unit proof passes.
- Docker compose was checked after Docker daemon recovery: `worker-general` is configured with `RQ_QUEUES=general,dataset,knowledge,blueprint`; `worker-video` is configured with `RQ_QUEUES=video`.
- Redis queue depths were checked for `general`, `video`, `dataset`, `knowledge`, and `blueprint`: all were 0 at the time of the check.

## Passed

- Existing Knowledge upload/reindex production path returns `job_id` in Redis mode.
- Existing Blueprint test-run production path returns `job_id` in Redis mode.
- Existing Dataset clean path returns `job_id` in Redis mode.
- General workers listen to Dataset/Knowledge/Blueprint queues even though standalone workers are not configured.

## Not Executed

- Dataset worker consumption of a real `dataset_clean` job in production Docker.
- Knowledge worker consumption of a real document ingest/reindex job in production Docker.
- Blueprint worker consumption of a real test run in production Docker.
- Failure/retry/cancel acceptance on production Docker.

## Not Passed

- Dataset `dataset_export` API acceptance is not passed because no public dataset export enqueue endpoint exists in the current API surface.

## Environment Limits

- Standalone `worker-dataset`, `worker-knowledge`, and `worker-blueprint` services are not configured in `docker-compose.prod.yml`; `worker-general` currently owns those queues.
