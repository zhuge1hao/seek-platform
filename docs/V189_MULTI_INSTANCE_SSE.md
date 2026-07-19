# v1.8.9 Multi-instance SSE

Version: `meizhaiseek v1.8.9`

## Status

- API instance count: `not_run`.
- Cross-instance run events: `not_run`.
- Redis pause/recovery: `not_run`.
- API restart: `not_run`.
- Event propagation p95: `not_run`.
- Marker target: keep `MULTI_INSTANCE_SSE_VERIFIED=not_run` until two API instances pass live validation.

## Safety

SSE payloads must not include `raw_response`, `prompt`, `workflow_options`, `token`, `api_key`, `secret`, `password`, or complete local filesystem paths.
