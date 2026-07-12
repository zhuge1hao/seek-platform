# v1.8.3 Queue Acceptance

## Target

- QA/Knowledge, Dataset, and Blueprint queue paths return job IDs quickly and use PostgreSQL as the status source.

## Current Status

- P0 unit proof executed.
- QA/Knowledge Redis upload and reindex enqueue tests pass.
- Worker cancelled guard and failure chunk cleanup tests pass.
- Full Docker/RQ Dataset/Knowledge/Blueprint acceptance is not executed yet.
