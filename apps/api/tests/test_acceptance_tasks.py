import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AcceptanceTasksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_DB_BACKEND"] = "sqlite"
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["AUTH_TOKEN_SECRET"] = "acceptance-secret-123456789012345"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "AdminTest123!"
        from services import app_sqlite

        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        from services import app_sqlite

        app_sqlite._INIT_DONE = False
        for key in ("APP_DB_BACKEND", "APP_SQLITE_PATH", "AUTH_TOKEN_SECRET", "MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"):
            os.environ.pop(key, None)
        self.tmp.cleanup()

    def test_controlled_run_completes_and_respects_cancel(self) -> None:
        from services import task_store
        from tasks.acceptance_tasks import controlled_run

        run = task_store.create_run_from_payload({"user_id": "alice", "username": "alice", "role": "admin", "agent_type": "acceptance", "prompt": "ok"})
        controlled_run(run["run_id"], "alice", 0)
        completed = task_store.get_run(run["run_id"], "alice")
        assert completed is not None
        self.assertEqual(completed["status"], "completed")

        cancelled = task_store.create_run_from_payload({"user_id": "alice", "username": "alice", "role": "admin", "agent_type": "acceptance", "prompt": "cancel"})
        task_store.cancel_run(cancelled["run_id"], "alice")
        controlled_run(cancelled["run_id"], "alice", 0)
        cancelled_result = task_store.get_run(cancelled["run_id"], "alice")
        assert cancelled_result is not None
        self.assertEqual(cancelled_result["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
