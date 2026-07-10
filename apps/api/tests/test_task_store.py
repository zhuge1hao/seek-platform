import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
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
        self.assertIsNotNone(completed)
        assert completed is not None
        self.assertEqual(completed["status"], "completed")
        loaded = conversation_store.get_conversation(conversation["conversation_id"], "user_a")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded["latest_run_id"], run["run_id"])
        self.assertEqual(loaded["status"], "completed")
        self.assertEqual(loaded["summary"], "done")
        assistant = next(message for message in loaded["messages"] if message.get("run_id") == run["run_id"])
        self.assertEqual(assistant["status"], "completed")
        self.assertEqual(assistant["content"], "done")
        self.assertEqual(assistant["result"]["answer"], "done")

        retry = task_store.clone_run_for_retry(run["run_id"], "user_a")
        self.assertIsNotNone(retry)
        assert retry is not None
        self.assertNotEqual(retry["run_id"], run["run_id"])
        self.assertEqual(retry["conversation_id"], conversation["conversation_id"])

        failed = task_store.create_run_from_payload({"user_id": "user_a", "username": "user_a", "role": "operator", "agent_type": "video_script_breakdown", "prompt": "fail"})
        failed_conversation, _ = conversation_store.attach_run(failed)
        task_store.update_run(failed["run_id"], {"conversation_id": failed_conversation["conversation_id"]}, "user_a")
        task_store.update_run(failed["run_id"], {"status": "failed", "error": "boom"}, "user_a")
        failed_run = task_store.get_run(failed["run_id"], "user_a", include_legacy=False)
        self.assertIsNotNone(failed_run)
        assert failed_run is not None
        self.assertEqual(failed_run["error"], "boom")
        failed_loaded = conversation_store.get_conversation(failed_conversation["conversation_id"], "user_a")
        self.assertIsNotNone(failed_loaded)
        assert failed_loaded is not None
        failed_assistant = next(message for message in failed_loaded["messages"] if message.get("run_id") == failed["run_id"])
        self.assertEqual(failed_loaded["status"], "failed")
        self.assertEqual(failed_loaded["summary"], "boom")
        self.assertEqual(failed_assistant["status"], "failed")
        self.assertEqual(failed_assistant["content"], "boom")

    def test_summary_result_cancel_retry_options_and_stale_repair(self) -> None:
        from services import agent_run_maintenance, app_sqlite, task_store

        run = task_store.create_run_from_payload({
            "user_id": "user_a",
            "username": "user_a",
            "role": "operator",
            "agent_type": "title_writing",
            "prompt": "do it",
            "workflow_options": {"temperature": 0.2, "api_key": "not-in-summary"},
        })
        self.assertEqual(run["status"], "running")
        completed = task_store.update_run(run["run_id"], {"status": "completed", "progress": 100, "result": {"answer": "ok", "raw_response": "x" * 9000}}, "user_a")
        self.assertIsNotNone(completed)
        assert completed is not None
        summary = task_store.summarize_run(completed)
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertTrue(summary["result_has_more"])
        self.assertNotIn("raw_response", str(summary["result"]))
        stored = task_store.get_run(run["run_id"], "user_a", include_legacy=False)
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored["result"]["raw_response"], "x" * 9000)

        retry = task_store.clone_run_for_retry(run["run_id"], "user_a")
        self.assertIsNotNone(retry)
        assert retry is not None
        self.assertEqual(retry["workflow_options"], {"temperature": 0.2, "api_key": "not-in-summary"})

        cancel = task_store.create_run_from_payload({"user_id": "user_a", "username": "user_a", "role": "operator", "agent_type": "title_writing", "prompt": "cancel"})
        cancelled, error = task_store.cancel_run(cancel["run_id"], "user_a")
        self.assertIsNone(error)
        self.assertIsNotNone(cancelled)
        assert cancelled is not None
        self.assertEqual(cancelled["status"], "cancelled")

        stale = task_store.create_run_from_payload({"user_id": "user_a", "username": "user_a", "role": "operator", "agent_type": "title_writing", "prompt": "stale"})
        old = (datetime.now() - timedelta(minutes=180)).strftime("%Y-%m-%d %H:%M:%S")
        stale["updated_at"] = old
        with app_sqlite.connection() as conn:
            conn.execute("UPDATE agent_runs SET updated_at=?, metadata_json=? WHERE run_id=?", (old, app_sqlite.json_dump(stale), stale["run_id"]))
        repaired = agent_run_maintenance.repair_stale(timeout_minutes=1)
        self.assertGreaterEqual(repaired["repaired"], 1)
        repaired_run = task_store.get_run(stale["run_id"], "user_a", include_legacy=False)
        self.assertIsNotNone(repaired_run)
        assert repaired_run is not None
        self.assertEqual(repaired_run["status"], "failed")
        cleanup = agent_run_maintenance.cleanup(days=1, statuses=["completed", "failed", "running"], dry_run=True)
        self.assertNotIn("running", cleanup["statuses"])

    def test_terminal_status_updates_are_guarded(self) -> None:
        from services import task_store

        run = task_store.create_run_from_payload({"user_id": "user_a", "username": "user_a", "role": "operator", "agent_type": "title_writing", "prompt": "guard"})
        self.assertEqual(run["row_version"], 1)
        completed = task_store.update_run(run["run_id"], {"status": "completed", "progress": 100, "result": {"answer": "done"}}, "user_a")
        self.assertIsNotNone(completed)
        assert completed is not None
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["progress"], 100)
        self.assertGreater(completed["row_version"], run["row_version"])

        stale = task_store.update_run(run["run_id"], {"status": "running", "progress": 40, "current_step": "late worker", "result": {"answer": "late"}, "error": None}, "user_a")
        self.assertIsNotNone(stale)
        assert stale is not None
        self.assertEqual(stale["status"], "completed")
        self.assertEqual(stale["progress"], 100)
        self.assertNotEqual(stale.get("current_step"), "late worker")
        self.assertEqual(stale.get("result"), {"answer": "done"})
        self.assertIn("ignored stale status update running after completed", stale["logs"])

        cancel = task_store.create_run_from_payload({"user_id": "user_a", "username": "user_a", "role": "operator", "agent_type": "title_writing", "prompt": "cancel"})
        cancelled, error = task_store.cancel_run(cancel["run_id"], "user_a")
        self.assertIsNone(error)
        self.assertIsNotNone(cancelled)
        assert cancelled is not None
        self.assertEqual(cancelled["status"], "cancelled")
        ignored = task_store.update_run(cancel["run_id"], {"status": "completed", "result": {"answer": "too late"}, "completed_at": "2099-01-01"}, "user_a")
        self.assertIsNotNone(ignored)
        assert ignored is not None
        self.assertEqual(ignored["status"], "cancelled")
        self.assertNotEqual((ignored.get("result") or {}).get("answer"), "too late")
        self.assertIsNone(ignored.get("completed_at"))


if __name__ == "__main__":
    unittest.main()
