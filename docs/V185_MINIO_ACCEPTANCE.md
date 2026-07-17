# v1.8.5 MinIO Acceptance

Version: meizhaiseek v1.8.5
Model: meizhaiseek 2.0

## Status

| Check | Coded | Executed | Result |
| --- | --- | --- | --- |
| Authenticated artifact signed URL route | yes | unit/static only | not_run |
| S3 presigned download support | yes | not_run | not_run |
| User A upload/download | existing | not_run | not_run |
| User B forbidden download | existing route guard | not_run | not_run |
| Object key traversal rejection | existing validator | not_run | not_run |
| 10MB streaming upload/download | script entry | not_run | not_run |
| 100MB streaming upload/download | script entry | not_run | not_run |
| TTL expiry | S3 presign supports TTL | not_run | not_run |
| Secret leak scan | script entry | not_run | not_run |

## Implemented

- Added `S3ArtifactStorage.presigned_download_url`.
- Added authenticated `GET /api/agent-runs/{run_id}/artifacts/{artifact_id}/signed-url`.
- Added `apps/api/scripts/acceptance_minio_storage.py`.

## Not Run

Docker/MinIO was not reachable on 2026-07-17, so no MinIO permission, TTL, streaming, or browser download result is marked `passed`.

## Accepted Risk

Local storage compatibility remains routed through the authenticated streaming download endpoint instead of an unauthenticated signed URL.
