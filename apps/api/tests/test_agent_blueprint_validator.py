import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentBlueprintValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _base(self) -> tuple[dict, dict]:
        blueprint = {"blueprint_id": "bp_v", "status": "draft"}
        version = {
            "input_schema": {"fields": [{"field_id": "video_file", "type": "video", "required": True}]},
            "methodology": {"steps": [{"step_id": "a", "order": 1, "failure_policy": "stop"}]},
            "prompt_config": {"user_prompt_template": "process {{ video_file }}", "variables": [{"name": "video_file"}]},
            "execution_config": {"execution_type": "mock"},
            "output_schema": {"sections": [{"section_id": "summary", "type": "summary"}]},
            "result_ui_config": {"renderer": "generic_structured"},
        }
        return blueprint, version

    def test_validates_schema_methodology_prompt_execution_and_renderer(self) -> None:
        from services.agent_blueprint_validator import validate_blueprint

        blueprint, version = self._base()
        result = validate_blueprint(blueprint, version, [{"name": "case", "input": {"video_file": "x.mp4"}}])
        self.assertTrue(result["valid"], result)

        bad = dict(version)
        bad["input_schema"] = {"fields": [{"field_id": "bad", "type": "shell"}]}
        bad["methodology"] = {"steps": [{"step_id": "b", "order": 2, "failure_policy": "explode"}, {"step_id": "a", "order": 1}]}
        bad["prompt_config"] = {"user_prompt_template": "{{ missing }}", "variables": [{"name": "unused"}]}
        bad["execution_config"] = {"execution_type": "http_connector", "connector_id": "missing_connector"}
        bad["result_ui_config"] = {"renderer": "unknown"}
        result = validate_blueprint(blueprint, bad, [])
        fields = {item["field"] for item in result["errors"]}
        self.assertIn("input_schema.fields[0].type", fields)
        self.assertIn("methodology.steps[0].failure_policy", fields)
        self.assertIn("prompt_config.variables", fields)
        self.assertIn("execution_config.connector_id", fields)
        self.assertIn("result_ui_config.renderer", fields)
        self.assertFalse(result["valid"])

    def test_sensitive_fields_are_rejected(self) -> None:
        from services.agent_blueprint_validator import validate_blueprint

        blueprint, version = self._base()
        version["prompt_config"] = {"api_key": "abc", "user_prompt_template": "x", "variables": []}
        result = validate_blueprint(blueprint, version, [])
        self.assertIn("version.prompt_config.api_key", {item["field"] for item in result["errors"]})


if __name__ == "__main__":
    unittest.main()
