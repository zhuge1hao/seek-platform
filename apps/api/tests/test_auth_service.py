import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AuthServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["MEIZHAISEEK_ADMIN_USERNAME"] = "admin"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "admin123"
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


if __name__ == "__main__":
    unittest.main()
