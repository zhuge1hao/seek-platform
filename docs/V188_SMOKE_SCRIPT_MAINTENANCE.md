# v1.8.8 Smoke Script Maintenance

Version: `meizhaiseek v1.8.8`
Model: `meizhaiseek 2.0`

## Change

`apps/api/scripts/smoke_minimal.py` no longer hardcodes `v1.8.4`.

Expected runtime identity resolves in this order:

1. CLI: `--expected-version`, `--expected-model`.
2. Environment: `APP_EXPECTED_VERSION`, `APP_EXPECTED_MODEL`.
3. Unified backend constants: `runtime_health_service.VERSION`, `runtime_health_service.MODEL`.

## Command

```powershell
python apps/api/scripts/smoke_minimal.py --expected-version v1.8.8 --expected-model "meizhaiseek 2.0"
```

## Status

- Unit coverage added.
- Live smoke result: `passed` on 2026-07-19 against a temporary API on `127.0.0.1:8018`.
- Evidence: `/health` returned `meizhaiseek-api`; admin login returned a token; runtime health returned `version=v1.8.8` and `model=meizhaiseek 2.0`; 8001 disconnected video task reached real `failed`; conversation, run, and messages persisted.
