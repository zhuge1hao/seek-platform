import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


ADMIN = {"user_id": "admin", "username": "admin", "role": "admin"}
OPERATOR = {"user_id": "op", "username": "op", "role": "operator"}


class AgentBlueprintServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _payload(self, blueprint_id: str = "bp_service") -> dict:
        return {
            "blueprint_id": blueprint_id,
            "agent_id": "video_script_breakdown",
            "name": blueprint_id,
            "display_name": "Service",
            "input_schema": {"fields": [{"field_id": "prompt", "type": "text"}]},
            "methodology": {"steps": [{"step_id": "run", "order": 1, "failure_policy": "stop"}]},
            "prompt_config": {"user_prompt_template": "{{ prompt }}", "variables": [{"name": "prompt"}]},
            "execution_config": {"execution_type": "mock"},
            "output_schema": {"sections": [{"section_id": "summary", "type": "summary"}]},
            "result_ui_config": {"renderer": "generic_structured"},
        }

    def test_publish_rollback_clone_seed_and_run_test_case(self) -> None:
        from fastapi import BackgroundTasks
        from services import agent_blueprint_seed_service, agent_blueprint_service, agent_blueprint_store

        detail = agent_blueprint_service.create_draft(self._payload(), ADMIN)
        blueprint_id = detail["blueprint"]["blueprint_id"]
        case = agent_blueprint_service.save_test_case(blueprint_id, {"name": "case", "input": {"prompt": "hello"}}, OPERATOR)

        published = agent_blueprint_service.publish(blueprint_id, {}, ADMIN)
        self.assertEqual(published["blueprint"]["status"], "published")
        with self.assertRaises(Exception):
            agent_blueprint_service.update_basic(blueprint_id, {"display_name": "Nope"}, ADMIN)

        v2 = agent_blueprint_service.create_version(blueprint_id, {"change_summary": "second"}, OPERATOR)
        agent_blueprint_service.publish(blueprint_id, {"version_id": v2["version_id"]}, ADMIN)
        rolled = agent_blueprint_service.rollback(blueprint_id, {"version_id": published["blueprint"]["published_version_id"]}, ADMIN)
        self.assertEqual(rolled["blueprint"]["status"], "published")
        self.assertTrue(any(item["action"] == "rollback" for item in agent_blueprint_store.list_releases(blueprint_id)))

        cloned = agent_blueprint_service.clone(blueprint_id, {}, OPERATOR)
        self.assertEqual(cloned["blueprint"]["status"], "draft")
        self.assertIsNone(cloned["blueprint"]["published_version_id"])

        with patch("services.orchestrator.schedule_run", lambda run_id, background_tasks, user_id: None):
            run = agent_blueprint_service.run_test_case(blueprint_id, case["test_case_id"], BackgroundTasks(), OPERATOR)
        self.assertTrue(run["run"]["run_id"].startswith("run_"))
        agent_blueprint_service.sync_test_run_result({"run_id": run["run"]["run_id"], "status": "completed", "result": {"summary": {"ok": True}}})
        self.assertEqual(agent_blueprint_store.get_test_case(case["test_case_id"])["last_result"]["status"], "PASS")

        agent_blueprint_seed_service.safe_seed_video_blueprint()
        agent_blueprint_seed_service.safe_seed_video_blueprint()
        self.assertEqual(len([item for item in agent_blueprint_store.list_blueprints() if item["blueprint_id"] == "bp_video_script_breakdown"]), 1)


if __name__ == "__main__":
    unittest.main()
