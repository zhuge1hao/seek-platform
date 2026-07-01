# Testing

Run unit tests:

```powershell
python -m unittest discover -s apps/api/tests
```

Run smoke:

```powershell
python apps/api/scripts/smoke_minimal.py
```

Optional video Agent E2E:

```powershell
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

Environment variables:

- `API_BASE_URL`
- `SMOKE_ADMIN_USERNAME`
- `SMOKE_ADMIN_PASSWORD`
- `VIDEO_AGENT_BASE_URL`
- `VIDEO_AGENT_TEST_VIDEO`
- `VIDEO_AGENT_TEST_OUTPUT_DIR`

Unit tests use temporary SQLite paths and do not require DeepSeek, BGE, or 8001.
