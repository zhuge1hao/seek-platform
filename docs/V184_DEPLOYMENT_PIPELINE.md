# v1.8.4 Deployment Pipeline

Version: `meizhaiseek v1.8.4`
Status: `not_run`

## Required CI/CD Changes

- Build API Docker image.
- Build Web Docker image.
- Push GHCR images on `main` and tags only.
- PR builds without image push.
- Tags: `v1.8.4`, commit SHA, and `latest` only on `main`.
- No secrets baked into images.
- Locust CI smoke uses 20 users for 1-2 minutes with mock DeepSeek and mock 8001.

## Results

- Docker image build: `not_run`
- GHCR push: `not_run`
- CI Locust smoke: `not_run`

