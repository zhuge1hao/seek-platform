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


if __name__ == "__main__":
    unittest.main()
