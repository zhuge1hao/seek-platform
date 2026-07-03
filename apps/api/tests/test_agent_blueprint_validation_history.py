import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
ADMIN = {"user_id": "admin", "username": "admin", "role": "admin"}


class AgentBlueprintValidationHistoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_validation_is_bound_to_version(self) -> None:
        from services import agent_blueprint_service, agent_blueprint_store
        detail = agent_blueprint_service.create_draft({"blueprint_id": "bp_val", "name": "bp", "display_name": "BP", "execution_config": {"execution_type": "mock"}, "result_ui_config": {"renderer": "generic_structured"}}, ADMIN)
        v1 = detail["current_version"]["version_id"]
        saved = agent_blueprint_service.validate("bp_val", ADMIN)
        self.assertEqual(saved["version_id"], v1)
        v2 = agent_blueprint_service.create_version("bp_val", {"change_summary": "new"}, ADMIN)
        self.assertIsNone(agent_blueprint_store.latest_validation_for_version("bp_val", v2["version_id"]))
        self.assertIsNotNone(agent_blueprint_store.latest_validation_for_version("bp_val", v1))


if __name__ == "__main__":
    unittest.main()
