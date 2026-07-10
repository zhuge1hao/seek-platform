import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentBlueprintRegistrySyncTest(unittest.TestCase):
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
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "admin123"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        from services import app_sqlite
        app_sqlite._INIT_DONE = False
        self.tmp.cleanup()

    def _token(self, client, username: str, password: str) -> dict[str, str]:
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['token']}"}

    def test_preview_permissions_and_apply_creates_only_draft(self) -> None:
        from fastapi.testclient import TestClient
        from main import app
        from services import agent_blueprint_store, user_admin_service

        user_admin_service.create_user("operator", "password123", "operator")
        user_admin_service.create_user("viewer", "password123", "viewer")
        with TestClient(app) as client:
            admin = self._token(client, "admin", "admin123")
            operator = self._token(client, "operator", "password123")
            viewer = self._token(client, "viewer", "password123")

            self.assertEqual(client.get("/api/agent-blueprints/registry-sync/preview", headers=viewer).status_code, 403)
            preview = client.get("/api/agent-blueprints/registry-sync/preview", headers=operator)
            self.assertEqual(preview.status_code, 200, preview.text)
            self.assertGreater(len(preview.json()["registry_only"]), 0)
            agent_id = preview.json()["registry_only"][0]["agent_type"]

            denied = client.post("/api/agent-blueprints/registry-sync/apply", headers=operator, json={"agent_ids": [agent_id], "create_as": "draft"})
            self.assertEqual(denied.status_code, 403)
            applied = client.post("/api/agent-blueprints/registry-sync/apply", headers=admin, json={"agent_ids": [agent_id], "create_as": "draft"})
            self.assertEqual(applied.status_code, 200, applied.text)
            created = applied.json()["created"][0]
            self.assertEqual(created["agent_id"], agent_id)
            self.assertEqual(created["status"], "draft")
            self.assertIsNone(created["published_version_id"])
            stored_blueprint = agent_blueprint_store.get_blueprint(created["blueprint_id"])
            self.assertIsNotNone(stored_blueprint)
            assert stored_blueprint is not None
            self.assertEqual(stored_blueprint["status"], "draft")


if __name__ == "__main__":
    unittest.main()
