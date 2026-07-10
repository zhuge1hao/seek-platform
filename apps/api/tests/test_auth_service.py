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
        os.environ["APP_DB_BACKEND"] = "sqlite"
        os.environ["APP_SQLITE_AUTO_MIGRATE"] = "false"
        os.environ.pop("APP_ENV", None)
        os.environ.pop("INITIAL_ADMIN_PASSWORD", None)
        os.environ["MEIZHAISEEK_ADMIN_USERNAME"] = "admin"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "AdminTest123!"
        os.environ["AUTH_TOKEN_SECRET"] = "test-secret-for-auth-service-123456"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False
        from services import rate_limit_service
        rate_limit_service._WINDOWS.clear()
        from services import user_store
        from services.password_service import hash_password
        users = user_store.load_users()
        users["users"]["admin"]["enabled"] = True
        users["users"]["admin"]["password_hash"] = hash_password("AdminTest123!")
        user_store.save_users(users)

    def tearDown(self) -> None:
        from services import app_sqlite
        app_sqlite._INIT_DONE = False
        os.environ.pop("LOGIN_RATE_LIMIT_PER_WINDOW", None)
        os.environ.pop("LOGIN_RATE_LIMIT_WINDOW_SECONDS", None)
        os.environ.pop("APP_DB_BACKEND", None)
        self.tmp.cleanup()

    def test_login_password_and_disabled_user(self) -> None:
        from services import auth_service, user_store

        user, error = auth_service.authenticate("admin", "AdminTest123!")
        self.assertIsNotNone(user)
        self.assertIsNone(error)
        bad, error = auth_service.authenticate("admin", "wrong")
        self.assertIsNone(bad)
        self.assertEqual(error, "invalid_credentials")

        doc = user_store.load_users()
        doc["users"]["admin"]["enabled"] = False
        user_store.save_users(doc)
        disabled, error = auth_service.authenticate("admin", "AdminTest123!")
        self.assertIsNotNone(disabled)
        self.assertEqual(error, "disabled")

    def test_token_role_and_public_api_safety(self) -> None:
        from fastapi.testclient import TestClient
        from main import app
        from services import token_service, user_admin_service, user_store
        from services.password_service import hash_password

        users = user_store.load_users()
        users["users"]["admin"]["enabled"] = True
        users["users"]["admin"]["auth_version"] = 1
        users["users"]["admin"]["password_hash"] = hash_password("AdminTest123!")
        user_store.save_users(users)
        user_admin_service.create_user("viewer", "ViewerPass123!", "viewer")
        user_admin_service.create_user("operator", "OperatorPass123!", "operator")

        admin_user = user_store.get_user("admin")
        self.assertIsNotNone(admin_user)
        assert admin_user is not None
        admin_token = token_service.create_token(admin_user)[0]
        with TestClient(app) as client:
            me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
            self.assertEqual(me.status_code, 200, me.text)
            self.assertNotIn("password_hash", me.json())

            viewer_token = client.post("/api/auth/login", json={"username": "viewer", "password": "ViewerPass123!"}).json()["token"]
            viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
            self.assertEqual(client.post("/api/conversations", headers=viewer_headers, json={"agent_type": "title_writing", "title": "x"}).status_code, 403)

            operator_token = client.post("/api/auth/login", json={"username": "operator", "password": "OperatorPass123!"}).json()["token"]
            operator_headers = {"Authorization": f"Bearer {operator_token}"}
            self.assertEqual(client.post("/api/agent-blueprints/missing/publish", headers=operator_headers, json={}).status_code, 403)

            self.assertEqual(client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"}).status_code, 200)
            user_store.update_password("admin", hash_password("NewPassword123!"))
            self.assertEqual(client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"}).status_code, 401)

            fresh_user = user_store.get_user("admin")
            self.assertIsNotNone(fresh_user)
            assert fresh_user is not None
            fresh_token = token_service.create_token(fresh_user)[0]
            with patch("services.token_service.time.time", return_value=10_000_000_000):
                self.assertRaises(token_service.TokenError, token_service.decode_token, fresh_token)
            runtime = client.get("/api/admin/runtime/health", headers={"Authorization": f"Bearer {fresh_token}"}).json()
            self.assertNotIn("AUTH_TOKEN_SECRET", str(runtime))
            self.assertNotIn("test-secret-for-auth-service-123456", str(runtime))

    def test_login_rate_limit_returns_retry_after_without_password_audit(self) -> None:
        from fastapi.testclient import TestClient
        from main import app
        from services import audit_log_service, rate_limit_service

        os.environ["LOGIN_RATE_LIMIT_PER_WINDOW"] = "1"
        os.environ["LOGIN_RATE_LIMIT_WINDOW_SECONDS"] = "60"
        rate_limit_service._WINDOWS.clear()

        with TestClient(app) as client:
            first = client.post("/api/auth/login", json={"username": "admin", "password": "wrong-password"})
            self.assertEqual(first.status_code, 401)
            second = client.post("/api/auth/login", json={"username": "admin", "password": "wrong-password"})
            self.assertEqual(second.status_code, 429)
            self.assertIn("Retry-After", second.headers)

        logs = audit_log_service.list_logs(limit=10, user="admin")
        self.assertNotIn("wrong-password", str(logs))


if __name__ == "__main__":
    unittest.main()
