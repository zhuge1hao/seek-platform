import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AsyncStoreUtilsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_LEGACY_JSON_FALLBACK"] = "false"
        os.environ["AUTH_TOKEN_SECRET"] = "test-secret"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        from services import app_sqlite
        app_sqlite._INIT_DONE = False
        self.tmp.cleanup()

    def test_concurrent_read_wrappers_use_thread_local_connections(self) -> None:
        from schemas.agent_runs import AgentRunCreate
        from services import async_store_utils, conversation_store, dataset_store, task_store

        user = {"user_id": "admin", "username": "admin", "role": "admin"}
        run = task_store.create_run(AgentRunCreate(agent_type="title_writing", prompt="async"), user)
        conversation = conversation_store.create_conversation("admin", "title_writing", "async")
        dataset = dataset_store.upsert_dataset({"dataset_id": "dataset_async", "user_id": "admin", "name": "Async", "status": "created", "row_count": 1})

        async def read_many() -> tuple[object, ...]:
            return await asyncio.gather(
                async_store_utils.async_get_run_summary(run["run_id"], "admin", False),
                async_store_utils.async_get_run_result(run["run_id"], "admin", False),
                async_store_utils.async_get_conversation(conversation["conversation_id"], "admin"),
                async_store_utils.async_list_conversations("admin"),
                async_store_utils.async_get_dataset(dataset["dataset_id"], "admin"),
                async_store_utils.async_list_datasets("admin"),
            )

        results = asyncio.run(read_many())
        run_summary, run_result, conversation_detail, conversation_items, dataset_detail, dataset_items = results
        assert isinstance(run_summary, dict)
        assert isinstance(run_result, dict)
        assert isinstance(conversation_detail, dict)
        assert isinstance(conversation_items, list)
        assert isinstance(dataset_detail, dict)
        assert isinstance(dataset_items, list)
        self.assertEqual(run_summary["run_id"], run["run_id"])
        self.assertEqual(run_result["run_id"], run["run_id"])
        self.assertEqual(conversation_detail["conversation_id"], conversation["conversation_id"])
        self.assertTrue(any(isinstance(item, dict) and item["conversation_id"] == conversation["conversation_id"] for item in conversation_items))
        self.assertEqual(dataset_detail["dataset_id"], dataset["dataset_id"])
        self.assertTrue(any(isinstance(item, dict) and item["dataset_id"] == dataset["dataset_id"] for item in dataset_items))
        self.assertGreaterEqual(async_store_utils.max_concurrency(), 1)


if __name__ == "__main__":
    unittest.main()
