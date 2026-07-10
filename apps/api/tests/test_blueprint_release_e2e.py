import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class BlueprintReleaseE2ETest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_DB_BACKEND"] = "sqlite"
        os.environ["APP_SQLITE_AUTO_MIGRATE"] = "false"
        os.environ["APP_LEGACY_JSON_FALLBACK"] = "false"
        os.environ.pop("APP_ENV", None)
        os.environ.pop("INITIAL_ADMIN_PASSWORD", None)
        os.environ["AUTH_TOKEN_SECRET"] = "test-secret"
        os.environ["MEIZHAISEEK_ADMIN_USERNAME"] = "admin"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "admin123456"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _token(self, client, username: str, password: str = "password123") -> dict[str, str]:
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['token']}"}

    def _version_payload(self, label: str) -> dict:
        return {
            "change_summary": label,
            "input_schema": {"fields": [{"field_id": "topic", "type": "text", "required": True}]},
            "methodology": {"steps": [{"step_id": "draft", "name": "Draft", "order": 1, "failure_policy": "stop"}]},
            "prompt_config": {"system_prompt": "Write title", "user_prompt_template": "Topic: {topic}", "variables": [{"name": "topic"}]},
            "execution_config": {"execution_type": "mock", "agent_id": "title_writing", "workflow_type": "generic_agent_workflow"},
            "output_schema": {"sections": [{"section_id": "summary", "type": "summary"}]},
            "result_ui_config": {"renderer": "generic_structured"},
            "acceptance_rules": {"required_result_fields": ["summary.title"]},
        }

    def test_release_gate_publish_rollback_permissions_and_run_blocking(self) -> None:
        from fastapi.testclient import TestClient
        from main import app
        from services import agent_blueprint_store, task_store, user_admin_service

        user_admin_service.create_user("operator", "password123", "operator")
        user_admin_service.create_user("viewer", "password123", "viewer")

        with TestClient(app) as client:
            admin = self._token(client, "admin", "admin123456")
            operator = self._token(client, "operator")
            viewer = self._token(client, "viewer")

            draft = client.post(
                "/api/agent-blueprints",
                headers=admin,
                json={"blueprint_id": "bp_title_e2e", "agent_id": "title_writing", "name": "title-e2e", "display_name": "Title E2E", **self._version_payload("initial")},
            )
            self.assertEqual(draft.status_code, 200, draft.text)
            version1 = draft.json()["current_version"]
            self.assertEqual(version1["execution_config"]["execution_type"], "mock")

            hidden = client.get("/api/agent-blueprints/bp_title_e2e", headers=viewer)
            self.assertEqual(hidden.status_code, 403)

            case = client.post(
                "/api/agent-blueprints/bp_title_e2e/test-cases",
                headers=operator,
                json={"version_id": version1["version_id"], "name": "happy path", "input": {"topic": "chairs"}, "expected_status": "completed", "expected_result_rules": {"required_result_fields": ["summary.title"]}},
            )
            self.assertEqual(case.status_code, 200, case.text)
            case_id = case.json()["test_case"]["test_case_id"]

            validation = client.post("/api/agent-blueprints/bp_title_e2e/validate", headers=operator)
            self.assertEqual(validation.status_code, 200, validation.text)
            self.assertTrue(validation.json()["valid"])
            validation_id = validation.json()["validation_id"]

            run1 = task_store.create_run_from_payload({"user_id": "operator", "username": "operator", "role": "operator", "agent_type": "title_writing", "prompt": "chairs", "result": {"summary": {"title": "Chair title"}}})
            test_run1 = agent_blueprint_store.create_test_run("bp_title_e2e", version1["version_id"], case_id, "operator", "completed")
            agent_blueprint_store.update_test_run(test_run1["test_run_id"], {"agent_run_id": run1["run_id"], "status": "passed", "actual_status": "completed", "result_summary": {"summary": {"title": "Chair title"}}})

            gate = client.post("/api/agent-blueprints/bp_title_e2e/release-gate", headers=operator, json={"version_id": version1["version_id"]})
            self.assertEqual(gate.status_code, 200, gate.text)
            self.assertTrue(gate.json()["allowed"])
            self.assertEqual(gate.json()["validation_id"], validation_id)
            self.assertEqual(gate.json()["test_run_id"], test_run1["test_run_id"])

            denied_publish = client.post("/api/agent-blueprints/bp_title_e2e/publish", headers=operator, json={"version_id": version1["version_id"]})
            self.assertEqual(denied_publish.status_code, 403)
            published1 = client.post("/api/agent-blueprints/bp_title_e2e/publish", headers=admin, json={"version_id": version1["version_id"]})
            self.assertEqual(published1.status_code, 200, published1.text)
            self.assertEqual(published1.json()["blueprint"]["status"], "published")
            self.assertEqual(published1.json()["blueprint"]["published_version_id"], version1["version_id"])

            releases = agent_blueprint_store.list_releases("bp_title_e2e")
            publish_release = next(item for item in releases if item["action"] == "publish" and item["version_id"] == version1["version_id"])
            self.assertEqual(publish_release["metadata"]["validation_id"], validation_id)
            self.assertEqual(publish_release["metadata"]["test_run_id"], test_run1["test_run_id"])

            visible = client.get("/api/agent-blueprints/bp_title_e2e", headers=viewer)
            self.assertEqual(visible.status_code, 200, visible.text)
            self.assertEqual(visible.json()["published_version"]["version_id"], version1["version_id"])
            self.assertNotIn("prompt_config", visible.json()["published_version"])
            self.assertEqual(visible.json()["test_cases"], [])

            version2 = client.post("/api/agent-blueprints/bp_title_e2e/versions", headers=operator, json={**self._version_payload("non-breaking title tweak"), "version_name": "v2"})
            self.assertEqual(version2.status_code, 200, version2.text)
            version2_id = version2.json()["version"]["version_id"]
            validation2 = client.post("/api/agent-blueprints/bp_title_e2e/validate", headers=operator)
            self.assertTrue(validation2.json()["valid"])
            run2 = task_store.create_run_from_payload({"user_id": "operator", "username": "operator", "role": "operator", "agent_type": "title_writing", "prompt": "tables"})
            test_run2 = agent_blueprint_store.create_test_run("bp_title_e2e", version2_id, case_id, "operator", "completed")
            agent_blueprint_store.update_test_run(test_run2["test_run_id"], {"agent_run_id": run2["run_id"], "status": "passed", "actual_status": "completed", "result_summary": {"summary": {"title": "Table title"}}})
            published2 = client.post("/api/agent-blueprints/bp_title_e2e/publish", headers=admin, json={"version_id": version2_id})
            self.assertEqual(published2.status_code, 200, published2.text)
            self.assertEqual(published2.json()["blueprint"]["published_version_id"], version2_id)

            rolled = client.post("/api/agent-blueprints/bp_title_e2e/rollback", headers=admin, json={"version_id": version1["version_id"]})
            self.assertEqual(rolled.status_code, 200, rolled.text)
            rollback_version_id = rolled.json()["blueprint"]["published_version_id"]
            rollback_version = agent_blueprint_store.get_version(rollback_version_id)
            self.assertIsNotNone(rollback_version)
            assert rollback_version is not None
            self.assertEqual(rollback_version["parent_version_id"], version1["version_id"])
            rollback_release = next(item for item in agent_blueprint_store.list_releases("bp_title_e2e") if item["action"] == "rollback")
            self.assertEqual(rollback_release["metadata"]["rollback_target_version_id"], version1["version_id"])
            self.assertIsNotNone(agent_blueprint_store.get_version(version1["version_id"]))
            self.assertIsNotNone(task_store.get_run(run1["run_id"], "operator", include_legacy=False))

            for action in ("disable", "deprecate"):
                changed = client.post(f"/api/agent-blueprints/bp_title_e2e/{action}", headers=admin, json={})
                self.assertEqual(changed.status_code, 200, changed.text)
                blocked = client.post("/api/agent-runs", headers=admin, json={"agent_type": "title_writing", "prompt": "blocked"})
                self.assertEqual(blocked.status_code, 403, blocked.text)
                if action == "disable":
                    enabled = client.post("/api/agent-blueprints/bp_title_e2e/enable", headers=admin, json={})
                    self.assertEqual(enabled.status_code, 200, enabled.text)

            client.post("/api/agent-blueprints/bp_title_e2e/enable", headers=admin, json={})
            with patch("services.orchestrator.schedule_run", lambda run_id, background_tasks, user_id: None):
                restored = client.post("/api/agent-runs", headers=admin, json={"agent_type": "title_writing", "prompt": "restored"})
            self.assertEqual(restored.status_code, 200, restored.text)
            self.assertTrue(restored.json()["run_id"].startswith("run_"))


if __name__ == "__main__":
    unittest.main()
