import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
ADMIN = {"user_id": "admin", "username": "admin", "role": "admin"}


class AgentBlueprintDiffTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_diff_ignores_key_order_and_tracks_field_changes(self) -> None:
        from services import agent_blueprint_diff_service, agent_blueprint_service

        detail = agent_blueprint_service.create_draft({"blueprint_id": "bp_diff", "name": "bp", "display_name": "BP", "input_schema": {"fields": [{"field_id": "a", "type": "text", "label": "A"}]}, "execution_config": {"execution_type": "mock"}, "result_ui_config": {"renderer": "generic_structured"}}, ADMIN)
        v1 = detail["current_version"]
        v2 = agent_blueprint_service.create_version("bp_diff", {"input_schema": {"fields": [{"label": "A", "type": "text", "field_id": "a"}, {"field_id": "b", "type": "number"}]}}, ADMIN)
        diff = agent_blueprint_diff_service.compare_blueprint_versions("bp_diff", v1["version_id"], v2["version_id"])
        input_changes = next(item for item in diff["sections"] if item["section"] == "input_schema")["changes"]
        self.assertTrue(diff["has_changes"])
        self.assertTrue(any("fields.b" in item["path"] for item in input_changes))
        self.assertFalse(any("fields.a" in item["path"] and item["change_type"] == "changed" for item in input_changes))


if __name__ == "__main__":
    unittest.main()
