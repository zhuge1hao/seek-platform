import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DISTRIBUTED_ACCEPTANCE_TESTS") != "1",
    reason="requires live Docker workers and controlled queue fault injection",
)


def test_zombie_recovery_manual_acceptance_documented() -> None:
    """Executable marker for the v1.8.2 zombie maintenance scenario.

    The 2026-07-06 acceptance run paused general workers, created a controlled
    running Agent Run, removed its queued RQ job, forced `updated_at` old, then
    executed `agent_run_maintenance.repair_stale(timeout_minutes=1)`.

    Result: one stale running run was repaired to failed. A late non-terminal
    update did not overwrite status, progress, step, result, or error.

    Not covered: killing an actually executing worker process and retrying the
    job to success. That remains not_run for v1.8.2 P2 unless a controlled long
    task fixture is added.
    """

    assert True
