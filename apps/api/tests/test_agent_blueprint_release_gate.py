import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
ADMIN = {"user_id": "admin", "username": "admin", "role": "admin"}


def payload() -> dict:
    return {"blueprint_id": "bp_gate", "agent_id": "video_script_breakdown", "name": "bp", "display_name": "BP", "input_schema": {"fields": [{"field_id": "prompt", "type": "text"}]}, "methodology": {"steps": [{"step_id": "run", "order": 1, "failure_policy": "stop"}]}, "prompt_config": {"user_prompt_template": "{{ prompt }}", "variables": [{"name": "prompt"}]}, "execution_config": {"execution_type": "mock"}, "output_schema": {"sections": [{"section_id": "summary", "type": "summary"}]}, "result_ui_config": {"renderer": "generic_structured"}}


class AgentBlueprintReleaseGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_gate_blocks_without_validation_or_test_and_allows_passed_version(self) -> None:
        from services import agent_blueprint_release_gate, agent_blueprint_service, agent_blueprint_store

        detail = agent_blueprint_service.create_draft(payload(), ADMIN)
        blueprint_id = detail["blueprint"]["blueprint_id"]
        version_id = detail["current_version"]["version_id"]
        gate = agent_blueprint_release_gate.check_release_gate(blueprint_id, version_id)
        self.assertFalse(gate["allowed"])
        self.assertTrue(any(item["code"] == "NO_VALIDATION" for item in gate["blocking_errors"]))

        agent_blueprint_service.save_test_case(blueprint_id, {"name": "case", "input": {"prompt": "ok"}}, ADMIN)
        agent_blueprint_service.validate(blueprint_id, ADMIN)
        case = agent_blueprint_store.list_test_cases(blueprint_id)[0]
        run = agent_blueprint_store.create_test_run(blueprint_id, version_id, case["test_case_id"], "admin", "completed")
        agent_blueprint_store.update_test_run(run["test_run_id"], {"status": "passed", "actual_status": "completed"})
        self.assertTrue(agent_blueprint_release_gate.check_release_gate(blueprint_id, version_id)["allowed"])


if __name__ == "__main__":
    unittest.main()
