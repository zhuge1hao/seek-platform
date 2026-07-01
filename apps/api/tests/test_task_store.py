import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TaskStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_LEGACY_JSON_FALLBACK"] = "false"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_run_status_and_retry(self) -> None:
        from services import conversation_store, task_store

        run = task_store.create_run_from_payload({"user_id": "user_a", "username": "user_a", "role": "operator", "agent_type": "video_script_breakdown", "prompt": "do it"})
        conversation, _ = conversation_store.attach_run(run)
        run["conversation_id"] = conversation["conversation_id"]
        task_store.update_run(run["run_id"], {"status": "completed", "progress": 100, "result": {"answer": "done"}})
        completed = task_store.get_run(run["run_id"], "user_a", include_legacy=False)
        self.assertEqual(completed["status"], "completed")

        retry = task_store.clone_run_for_retry(run["run_id"], "user_a")
        self.assertIsNotNone(retry)
        self.assertNotEqual(retry["run_id"], run["run_id"])

        failed = task_store.create_run_from_payload({"user_id": "user_a", "username": "user_a", "role": "operator", "agent_type": "video_script_breakdown", "prompt": "fail"})
        task_store.update_run(failed["run_id"], {"status": "failed", "error": "boom"})
        self.assertEqual(task_store.get_run(failed["run_id"], "user_a", include_legacy=False)["error"], "boom")


if __name__ == "__main__":
    unittest.main()
