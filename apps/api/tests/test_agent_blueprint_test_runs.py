import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentBlueprintTestRunsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_test_run_history_is_not_overwritten(self) -> None:
        from services import agent_blueprint_store as store
        store.create_blueprint({"blueprint_id": "bp_runs", "name": "bp", "display_name": "BP"}, "u")
        store.create_version("bp_runs", {}, "u")
        case = store.save_test_case("bp_runs", {"name": "case", "input": {}}, "u")
        first = store.create_test_run("bp_runs", "v1", case["test_case_id"], "u", "completed")
        second = store.create_test_run("bp_runs", "v1", case["test_case_id"], "u", "completed")
        store.update_test_run(first["test_run_id"], {"status": "failed", "agent_run_id": "run_a", "actual_status": "failed"})
        store.update_test_run(second["test_run_id"], {"status": "passed", "agent_run_id": "run_b", "actual_status": "completed"})
        runs = store.list_test_runs("bp_runs", limit=10)
        self.assertEqual(len(runs), 2)
        stored_run = store.get_test_run_by_agent_run_id("run_b")
        self.assertIsNotNone(stored_run)
        assert stored_run is not None
        self.assertEqual(stored_run["status"], "passed")


if __name__ == "__main__":
    unittest.main()
