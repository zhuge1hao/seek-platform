# Artifact Storage
## v1.8.8 Browser Artifact Evidence

Browser video Excel/JSON/evidence download verification is `not_run` until the real video Agent matrix is executed. Signed artifact routes must continue to enforce user isolation and avoid leaking MinIO secrets.

## v1.8.4 Acceptance Status

- MinIO permission checks: `not_run`
- Signed URL TTL checks: `not_run`
- Streaming upload/download checks: `not_run`
- Video Excel/JSON/evidence artifact checks: `not_run`

S3/MinIO secrets must never be returned to frontend responses or committed documentation.

v1.8 adds an artifact storage provider facade.

Backends:

- `local`: existing local runtime path, default for development.
- `local_shared`: shared filesystem path for production deployments with multiple API/worker containers.
- `s3`: provider facade reserved for object storage.

Artifact metadata now includes:

- `storage_backend`
- `object_key`
- `original_filename`
- `checksum`

Downloads remain served by the API and must pass existing user/run ownership checks.

Current status: local/local_shared metadata is wired. S3 actual upload and mock/provider tests remain follow-up work.
# v1.8.5 Artifact Storage Status

- S3 provider now exposes presigned download URL generation with bounded TTL.
- Authenticated run artifact signed-url endpoint is coded.
- `apps/api/scripts/acceptance_minio_storage.py` is available for 10MB default and explicit 100MB reruns.
- Real MinIO permission, TTL, streaming, and cross-user download acceptance is `not_run` for v1.8.5 in the current environment because Docker/MinIO was unavailable.

## v1.8.7 MinIO Acceptance

Status on 2026-07-17: `passed` for the required 10MB matrix and the resource-allowed 100MB matrix.

Validated behavior:

- Run artifact downloads stream through the API from S3/MinIO.
- Authenticated signed URL route enforces run/artifact ownership.
- Cross-user artifact access returns HTTP 403.
- Missing artifact returns HTTP 404.
- Path traversal through the legacy local artifact download route returns HTTP 403.
- Short TTL presigned URLs work immediately and expire with HTTP 403.
- Object keys are partitioned by `user_id/run_id/artifact_id`.
- Checksums match for 10MB and 100MB objects.
- Chinese filenames use RFC 5987 `filename*` Content-Disposition.
- JSON report, Excel workbook, and evidence image artifacts download with expected content types.
- Signed URL JSON responses do not include S3 secret fields.

Evidence: `docs/V187_MINIO_FULL_ACCEPTANCE.md`.

Runtime marker: `artifact_s3_verified=passed` only in deployments that set `ARTIFACT_S3_VERIFIED=passed` after this acceptance. S3/MinIO access keys and secret keys remain excluded from frontend responses and committed documentation.
