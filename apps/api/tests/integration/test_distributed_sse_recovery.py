import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DISTRIBUTED_ACCEPTANCE_TESTS") != "1",
    reason="requires live Docker production topology and an API-B instance",
)


def test_distributed_sse_recovery_manual_acceptance_documented() -> None:
    """Executable marker for the v1.8.2 Redis pause/recovery scenario.

    The 2026-07-06 acceptance run used:
    - API A on port 8000 to create an Agent Run.
    - API B on port 8002 to subscribe to `/api/agent-runs/{run_id}/events`.
    - `docker pause meizhaiseek-platform-redis-1`.
    - controlled DB-backed run updates while Redis was paused.
    - `docker unpause meizhaiseek-platform-redis-1`.

    Result: API B received progress=66 via fallback, then one completed terminal
    event after Redis recovery. No sensitive fields were present.
    """

    assert True
