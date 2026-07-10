import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentBlueprintApiTest(unittest.TestCase):
    ADMIN_PASSWORD = "AdminBlueprint123!"

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_DB_BACKEND"] = "sqlite"
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_SQLITE_AUTO_MIGRATE"] = "false"
        os.environ["APP_LEGACY_JSON_FALLBACK"] = "false"
        os.environ.pop("APP_ENV", None)
        os.environ.pop("INITIAL_ADMIN_PASSWORD", None)
        os.environ["AUTH_TOKEN_SECRET"] = "test-secret"
        os.environ["MEIZHAISEEK_ADMIN_USERNAME"] = "admin"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = self.ADMIN_PASSWORD
        from services import app_sqlite
        app_sqlite._INIT_DONE = False
        from services import rate_limit_service
        rate_limit_service._WINDOWS.clear()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _token(self, user: dict) -> str:
        from services import token_service
        return token_service.create_token(user)[0]

    def test_api_permissions_and_agent_registry_enrichment(self) -> None:
        from fastapi.testclient import TestClient
        from main import app
        from services import user_store
        from services.password_service import hash_password

        with TestClient(app) as client:
            users = user_store.load_users()
            users["users"]["admin"]["password_hash"] = hash_password(self.ADMIN_PASSWORD)
            users["users"]["admin"]["enabled"] = True
            user_store.save_users(users)
            login = client.post("/api/auth/login", json={"username": "admin", "password": self.ADMIN_PASSWORD})
            self.assertEqual(login.status_code, 200, login.text)
            token = login.json()["token"]
            admin_headers = {"Authorization": f"Bearer {token}"}
            users = user_store.load_users()
            users["users"]["operator"] = {
                "user_id": "operator",
                "username": "operator",
                "role": "operator",
                "enabled": True,
                "password_hash": hash_password("operator123"),
                "auth_version": 1,
            }
            users["users"]["viewer"] = {
                "user_id": "viewer",
                "username": "viewer",
                "role": "viewer",
                "enabled": True,
                "password_hash": hash_password("viewer123"),
                "auth_version": 1,
            }
            user_store.save_users(users)
            operator_user = user_store.get_user("operator")
            viewer_user = user_store.get_user("viewer")
            self.assertIsNotNone(operator_user)
            self.assertIsNotNone(viewer_user)
            assert operator_user is not None
            assert viewer_user is not None
            op_headers = {"Authorization": f"Bearer {self._token(operator_user)}"}
            viewer_headers = {"Authorization": f"Bearer {self._token(viewer_user)}"}

            payload = {
                "blueprint_id": "bp_api",
                "agent_id": "video_script_breakdown",
                "name": "api",
                "display_name": "API",
                "execution_config": {"execution_type": "mock"},
                "result_ui_config": {"renderer": "generic_structured"},
            }
            created = client.post("/api/agent-blueprints", headers=op_headers, json=payload)
            self.assertEqual(created.status_code, 200, created.text)
            publish_by_operator = client.post("/api/agent-blueprints/bp_api/publish", headers=op_headers, json={})
            self.assertEqual(publish_by_operator.status_code, 403)

            viewer_list = client.get("/api/agent-blueprints", headers=viewer_headers)
            self.assertEqual(viewer_list.status_code, 200)
            self.assertNotIn("bp_api", [item["blueprint_id"] for item in viewer_list.json()["items"]])

            publish_blocked = client.post("/api/agent-blueprints/bp_api/publish", headers=admin_headers, json={})
            self.assertEqual(publish_blocked.status_code, 409)
            client.post("/api/agent-blueprints/bp_api/test-cases", headers=op_headers, json={"name": "case", "input": {"prompt": "ok"}})
            validation = client.post("/api/agent-blueprints/bp_api/validate", headers=op_headers)
            self.assertEqual(validation.status_code, 200, validation.text)
            from services import agent_blueprint_store
            detail = client.get("/api/agent-blueprints/bp_api", headers=admin_headers).json()
            version_id = detail["current_version"]["version_id"]
            case = agent_blueprint_store.list_test_cases("bp_api")[0]
            run = agent_blueprint_store.create_test_run("bp_api", version_id, case["test_case_id"], "operator", "completed")
            agent_blueprint_store.update_test_run(run["test_run_id"], {"status": "passed", "actual_status": "completed"})
            publish_by_admin = client.post("/api/agent-blueprints/bp_api/publish", headers=admin_headers, json={})
            self.assertEqual(publish_by_admin.status_code, 200, publish_by_admin.text)
            viewer_detail = client.get("/api/agent-blueprints/bp_api", headers=viewer_headers)
            self.assertEqual(viewer_detail.status_code, 200)
            self.assertNotIn("prompt_config", viewer_detail.json()["versions"][0])

            agents = client.get("/api/agents", headers=admin_headers)
            self.assertEqual(agents.status_code, 200)
            video = next(item for item in agents.json()["agents"] if item.get("type") == "video_script_breakdown" or item.get("agent_type") == "video_script_breakdown")
            self.assertIn(video["blueprint_status"], {"published", "unmanaged"})


if __name__ == "__main__":
    unittest.main()
