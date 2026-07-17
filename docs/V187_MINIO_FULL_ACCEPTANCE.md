# v1.8.7 MinIO Full Acceptance

## Status

- Coded: `passed`
- Executed: `passed`
- Passed: `passed`
- Failed: `not_run`

## Required Evidence

- User A upload/download.
- User B forbidden download.
- Path traversal rejected.
- Short TTL signed URL expires.
- 10MB streaming upload/download.
- 100MB streaming upload/download when resources allow.
- Checksum, content-type, Chinese filename, secret redaction, and local storage compatibility.

## Results

Executed in Docker API container on 2026-07-17 after rebuilding the API image with the v1.8.7 artifact route and script updates.

### 10MB Required Matrix

Command:

```powershell
docker compose -f docker-compose.prod.yml exec -T api python scripts/acceptance_minio_storage.py --json-report --size 10MB
```

Result: `passed`.

- Run: `run_20260717092013_6dc58ed5`
- Artifact: `artifact_ea3ef3408ed9`
- Storage backend: `s3`
- User A login/download: HTTP 200.
- User B signed URL: HTTP 403.
- Missing artifact: HTTP 404.
- Path traversal: HTTP 403.
- Signed URL immediate fetch: HTTP 200.
- Signed URL after 2 second TTL plus wait: HTTP 403.
- Streaming download size: `10485760` bytes.
- Streaming chunks observed by client: `10`.
- Checksum matched: `ebd2881d8acc427157023a3b40df7e7de8457cbda329c00b815b006bb71a4839`.
- Content type: `application/octet-stream`.
- Chinese filename Content-Disposition used `filename*=UTF-8''...`.
- Object key partition: `artifacts/<user_id>/<run_id>/<artifact_id>/...`.
- JSON report download: HTTP 200, `application/json`.
- Excel download: HTTP 200, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
- Evidence image download: HTTP 200, `image/png`.
- Signed URL response secret leak scan: passed; URL itself was not written to this document.

### 100MB Optional Matrix

Command:

```powershell
docker compose -f docker-compose.prod.yml exec -T api python scripts/acceptance_minio_storage.py --json-report --size 100MB
```

Initial script order failed because the 2 second signed URL expired while the script first downloaded the 100MB file through the API. The script was corrected to validate signed URL immediate/expired behavior before the large API streaming download, then rerun.

Rerun result: `passed`.

- Run: `run_20260717092215_0dda7a92`
- Artifact: `artifact_129484ccdf07`
- Storage backend: `s3`
- User A login/download: HTTP 200.
- User B signed URL: HTTP 403.
- Missing artifact: HTTP 404.
- Path traversal: HTTP 403.
- Signed URL immediate fetch: HTTP 200.
- Signed URL after 2 second TTL plus wait: HTTP 403.
- Streaming download size: `104857600` bytes.
- Streaming chunks observed by client: `100`.
- Checksum matched: `51814a87760a4477a224a458625fbe03dee570e0aecd4d7a74dc93ac23d5c75b`.
- JSON, Excel, and evidence image downloads all returned HTTP 200.

### Marker

`ARTIFACT_S3_VERIFIED` is eligible for `passed` when the production runtime environment is started with the marker set. `.env` remains uncommitted.
