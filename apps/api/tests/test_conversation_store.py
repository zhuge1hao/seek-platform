import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ConversationStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_LEGACY_JSON_FALLBACK"] = "false"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_conversation_lifecycle_and_user_isolation(self) -> None:
        from services import conversation_store

        conv = conversation_store.create_conversation("user_a", "video_script_breakdown", "hello")
        conversation_store.append_agent_message("user_a", conv["conversation_id"], {"message_id": "msg_user", "role": "user", "content": "hello"})
        assistant = conversation_store.append_agent_message("user_a", conv["conversation_id"], {"message_id": "msg_assistant", "role": "assistant", "content": "running", "status": "running", "run_id": "run_1"})
        conversation_store.update_agent_message("user_a", conv["conversation_id"], assistant["message_id"], {"status": "completed", "content": "done"})

        loaded = conversation_store.get_conversation(conv["conversation_id"], "user_a")
        self.assertEqual(len(loaded["messages"]), 2)
        self.assertIsNone(conversation_store.get_conversation(conv["conversation_id"], "user_b"))

        conversation_store.archive_conversation(conv["conversation_id"], "user_a")
        self.assertEqual(conversation_store.list_conversations("user_a"), [])
        self.assertEqual(len(conversation_store.list_conversations("user_a", include_archived=True)), 1)

    def test_run_sync_states_do_not_duplicate_or_cross_users(self) -> None:
        from services import conversation_store, task_store

        run = task_store.create_run_from_payload({"user_id": "user_a", "username": "user_a", "role": "operator", "agent_type": "title_writing", "prompt": "one"})
        conv, _ = conversation_store.attach_run(run)
        task_store.update_run(run["run_id"], {"conversation_id": conv["conversation_id"]}, "user_a")
        task_store.update_run(run["run_id"], {"status": "cancelled", "progress": 100}, "user_a")
        task_store.update_run(run["run_id"], {"status": "cancelled", "progress": 100}, "user_a")

        other = conversation_store.create_conversation("user_b", "title_writing", "two")
        conversation_store.append_agent_message("user_b", other["conversation_id"], {"message_id": "user_b_msg", "role": "user", "content": "two"})

        loaded = conversation_store.get_conversation(conv["conversation_id"], "user_a")
        assistant_messages = [message for message in loaded["messages"] if message.get("run_id") == run["run_id"]]
        self.assertEqual(len(assistant_messages), 1)
        self.assertEqual(assistant_messages[0]["status"], "cancelled")
        self.assertEqual(loaded["latest_run_id"], run["run_id"])
        self.assertEqual(loaded["status"], "cancelled")
        self.assertIsNone(conversation_store.get_conversation(conv["conversation_id"], "user_b"))
        self.assertEqual(len(conversation_store.get_conversation(other["conversation_id"], "user_b")["messages"]), 1)


if __name__ == "__main__":
    unittest.main()
