import base64
import gc
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TokenServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_DB_BACKEND"] = "sqlite"
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_SQLITE_AUTO_MIGRATE"] = "false"
        os.environ["AUTH_TOKEN_SECRET"] = "token-test-secret-12345678901234567890"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "AdminTest123!"
        from services import app_sqlite

        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        from services import app_sqlite

        app_sqlite._INIT_DONE = False
        for key in ("APP_DB_BACKEND", "APP_SQLITE_PATH", "APP_SQLITE_AUTO_MIGRATE", "APP_ENV", "AUTH_TOKEN_SECRET", "AUTH_TOKEN_EXPIRE_HOURS"):
            os.environ.pop(key, None)
        for _ in range(5):
            try:
                self.tmp.cleanup()
                return
            except PermissionError:
                gc.collect()
                time.sleep(0.1)
        self.tmp.cleanup()

    def test_create_decode_expiry_signature_and_payload_safety(self) -> None:
        from services import token_service

        user = {"user_id": "u1", "username": "alice", "role": "operator", "auth_version": 3, "password_hash": "secret-hash"}
        token, expires_at = token_service.create_token(user)
        self.assertIn(".", token)
        self.assertTrue(expires_at)
        payload = token_service.decode_token(token)
        self.assertEqual(payload["username"], "alice")
        decoded = json.loads(base64.urlsafe_b64decode(token.split(".", 1)[0] + "==").decode("utf-8"))
        self.assertNotIn("password_hash", decoded)
        self.assertNotIn("secret", json.dumps(decoded).lower())
        self.assertRaises(token_service.TokenError, token_service.decode_token, token[:-2] + "xx")
        with patch("services.token_service.time.time", return_value=10_000_000_000):
            self.assertRaises(token_service.TokenError, token_service.decode_token, token)

    def test_auth_version_and_disabled_user_invalidate_existing_token(self) -> None:
        from fastapi.testclient import TestClient
        from main import app
        from services import token_service, user_admin_service, user_store

        user_admin_service.create_user("bob", "BobPassword123!", "operator")
        token = token_service.create_token(user_store.get_user("bob"))[0]
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code, 200)
            user_admin_service.disable_user("bob", "admin")
            self.assertEqual(client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code, 403)
            user_admin_service.enable_user("bob", "admin")
            self.assertEqual(client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code, 401)

    def test_weak_secret_rejected_in_production(self) -> None:
        from services import security_config_service

        os.environ["APP_ENV"] = "production"
        os.environ["AUTH_TOKEN_SECRET"] = "secret"
        self.assertEqual(security_config_service.token_secret_status(), "invalid")
        self.assertRaises(RuntimeError, security_config_service.get_auth_token_secret)


if __name__ == "__main__":
    unittest.main()
