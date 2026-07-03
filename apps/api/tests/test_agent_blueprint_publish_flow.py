import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentBlueprintPublishFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_publish_then_rollback_records_releases(self) -> None:
        from services import agent_blueprint_service, agent_blueprint_store
        user = {"user_id": "admin", "username": "admin", "role": "admin"}
        detail = agent_blueprint_service.create_draft({"blueprint_id": "bp_flow", "name": "bp", "display_name": "BP", "execution_config": {"execution_type": "mock"}, "result_ui_config": {"renderer": "generic_structured"}}, user)
        version_id = detail["current_version"]["version_id"]
        case = agent_blueprint_service.save_test_case("bp_flow", {"name": "case", "input": {}}, user)
        agent_blueprint_service.validate("bp_flow", user)
        run = agent_blueprint_store.create_test_run("bp_flow", version_id, case["test_case_id"], "admin", "completed")
        agent_blueprint_store.update_test_run(run["test_run_id"], {"status": "passed", "actual_status": "completed"})
        published = agent_blueprint_service.publish("bp_flow", {}, user)
        old_version = published["blueprint"]["published_version_id"]
        v2 = agent_blueprint_service.create_version("bp_flow", {"change_summary": "next"}, user)
        agent_blueprint_service.validate("bp_flow", user)
        run2 = agent_blueprint_store.create_test_run("bp_flow", v2["version_id"], case["test_case_id"], "admin", "completed")
        agent_blueprint_store.update_test_run(run2["test_run_id"], {"status": "passed", "actual_status": "completed"})
        agent_blueprint_service.publish("bp_flow", {"version_id": v2["version_id"]}, user)
        agent_blueprint_service.rollback("bp_flow", {"version_id": old_version}, user)
        actions = [item["action"] for item in agent_blueprint_store.list_releases("bp_flow")]
        self.assertIn("publish", actions)
        self.assertIn("rollback", actions)


if __name__ == "__main__":
    unittest.main()
