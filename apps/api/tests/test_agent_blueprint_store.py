import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentBlueprintStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_LEGACY_JSON_FALLBACK"] = "false"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_store_lifecycle_version_release_and_test_case(self) -> None:
        from services import agent_blueprint_store as store

        blueprint = store.create_blueprint({"blueprint_id": "bp_store", "name": "store", "display_name": "Store"}, "admin")
        self.assertEqual(blueprint["status"], "draft")

        v1 = store.create_version("bp_store", {"input_schema": {"fields": []}}, "admin")
        v2 = store.create_version("bp_store", {"input_schema": {"fields": []}}, "admin")
        self.assertEqual(v1["version_number"], 1)
        self.assertEqual(v2["version_number"], 2)
        stored_blueprint = store.get_blueprint("bp_store")
        self.assertIsNotNone(stored_blueprint)
        assert stored_blueprint is not None
        self.assertEqual(stored_blueprint["current_version_id"], v2["version_id"])

        case = store.save_test_case("bp_store", {"name": "case", "input": {"prompt": "hello"}}, "admin")
        store.set_test_case_run_result(case["test_case_id"], "run_1", {"status": "PASS"})
        stored_case = store.get_test_case_by_run_id("run_1")
        self.assertIsNotNone(stored_case)
        assert stored_case is not None
        self.assertEqual(stored_case["last_result"]["status"], "PASS")

        store.mark_version_published("bp_store", v1["version_id"])
        store.update_blueprint("bp_store", {"status": "published", "published_version_id": v1["version_id"]}, "admin")
        release = store.create_release("bp_store", v1["version_id"], "publish", "admin")
        self.assertEqual(release["action"], "publish")
        self.assertFalse(store.delete_blueprint("bp_store"))


if __name__ == "__main__":
    unittest.main()
