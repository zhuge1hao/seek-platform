# Artifact Storage

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
