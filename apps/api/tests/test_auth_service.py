import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AuthServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["MEIZHAISEEK_ADMIN_USERNAME"] = "admin"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "admin123"
        os.environ["AUTH_TOKEN_SECRET"] = "test-secret"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_login_password_and_disabled_user(self) -> None:
        from services import auth_service, user_store

        user, error = auth_service.authenticate("admin", "admin123")
        self.assertIsNotNone(user)
        self.assertIsNone(error)
        bad, error = auth_service.authenticate("admin", "wrong")
        self.assertIsNone(bad)
        self.assertEqual(error, "invalid_credentials")

        doc = user_store.load_users()
        doc["users"]["admin"]["enabled"] = False
        user_store.save_users(doc)
        disabled, error = auth_service.authenticate("admin", "admin123")
        self.assertIsNotNone(disabled)
        self.assertEqual(error, "disabled")

    def test_token_role_and_public_api_safety(self) -> None:
        from fastapi.testclient import TestClient
        from main import app
        from services import token_service, user_admin_service

        user_admin_service.create_user("viewer", "password123", "viewer")
        user_admin_service.create_user("operator", "password123", "operator")

        with TestClient(app) as client:
            admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
            self.assertEqual(admin_login.status_code, 200, admin_login.text)
            admin_token = admin_login.json()["token"]
            self.assertNotIn("password_hash", admin_login.json()["user"])

            viewer_token = client.post("/api/auth/login", json={"username": "viewer", "password": "password123"}).json()["token"]
            viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
            self.assertEqual(client.post("/api/conversations", headers=viewer_headers, json={"agent_type": "title_writing", "title": "x"}).status_code, 403)

            operator_token = client.post("/api/auth/login", json={"username": "operator", "password": "password123"}).json()["token"]
            operator_headers = {"Authorization": f"Bearer {operator_token}"}
            self.assertEqual(client.post("/api/agent-blueprints/missing/publish", headers=operator_headers, json={}).status_code, 403)

            self.assertEqual(client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"}).status_code, 200)
            changed = client.post("/api/auth/change-password", headers={"Authorization": f"Bearer {admin_token}"}, json={"old_password": "admin123", "new_password": "newpassword123"})
            self.assertEqual(changed.status_code, 200, changed.text)
            self.assertEqual(client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"}).status_code, 401)

            fresh_token = client.post("/api/auth/login", json={"username": "admin", "password": "newpassword123"}).json()["token"]
            with patch("services.token_service.time.time", return_value=10_000_000_000):
                self.assertRaises(token_service.TokenError, token_service.decode_token, fresh_token)
            runtime = client.get("/api/admin/runtime/health", headers={"Authorization": f"Bearer {fresh_token}"}).json()
            self.assertNotIn("AUTH_TOKEN_SECRET", str(runtime))
            self.assertNotIn("test-secret", str(runtime))


if __name__ == "__main__":
    unittest.main()
