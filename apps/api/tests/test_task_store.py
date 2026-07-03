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
        from services import conversation_store, service_events, task_store

        service_events.clear_handlers_for_test()
        service_events.register_run_updated_handler(conversation_store.sync_run_to_conversation)

        run = task_store.create_run_from_payload({"user_id": "user_a", "username": "user_a", "role": "operator", "agent_type": "video_script_breakdown", "prompt": "do it"})
        conversation, _ = conversation_store.attach_run(run)
        task_store.update_run(run["run_id"], {"conversation_id": conversation["conversation_id"]}, "user_a")
        task_store.update_run(run["run_id"], {"status": "completed", "progress": 100, "result": {"answer": "done"}}, "user_a")
        completed = task_store.get_run(run["run_id"], "user_a", include_legacy=False)
        self.assertEqual(completed["status"], "completed")
        loaded = conversation_store.get_conversation(conversation["conversation_id"], "user_a")
        self.assertEqual(loaded["latest_run_id"], run["run_id"])
        self.assertEqual(loaded["status"], "completed")
        self.assertEqual(loaded["summary"], "done")
        assistant = next(message for message in loaded["messages"] if message.get("run_id") == run["run_id"])
        self.assertEqual(assistant["status"], "completed")
        self.assertEqual(assistant["content"], "done")
        self.assertEqual(assistant["result"]["answer"], "done")

        retry = task_store.clone_run_for_retry(run["run_id"], "user_a")
        self.assertIsNotNone(retry)
        self.assertNotEqual(retry["run_id"], run["run_id"])

        failed = task_store.create_run_from_payload({"user_id": "user_a", "username": "user_a", "role": "operator", "agent_type": "video_script_breakdown", "prompt": "fail"})
        failed_conversation, _ = conversation_store.attach_run(failed)
        task_store.update_run(failed["run_id"], {"conversation_id": failed_conversation["conversation_id"]}, "user_a")
        task_store.update_run(failed["run_id"], {"status": "failed", "error": "boom"}, "user_a")
        self.assertEqual(task_store.get_run(failed["run_id"], "user_a", include_legacy=False)["error"], "boom")
        failed_loaded = conversation_store.get_conversation(failed_conversation["conversation_id"], "user_a")
        failed_assistant = next(message for message in failed_loaded["messages"] if message.get("run_id") == failed["run_id"])
        self.assertEqual(failed_loaded["status"], "failed")
        self.assertEqual(failed_loaded["summary"], "boom")
        self.assertEqual(failed_assistant["status"], "failed")
        self.assertEqual(failed_assistant["content"], "boom")


if __name__ == "__main__":
    unittest.main()
