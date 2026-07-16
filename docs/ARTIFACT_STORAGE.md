# Artifact Storage

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
