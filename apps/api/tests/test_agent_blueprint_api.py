import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentBlueprintApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_LEGACY_JSON_FALLBACK"] = "false"
        os.environ["AUTH_TOKEN_SECRET"] = "test-secret"
        os.environ["MEIZHAISEEK_ADMIN_USERNAME"] = "admin"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "admin123"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

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
            token = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["token"]
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
            op_headers = {"Authorization": f"Bearer {self._token(user_store.get_user('operator'))}"}
            viewer_headers = {"Authorization": f"Bearer {self._token(user_store.get_user('viewer'))}"}

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
