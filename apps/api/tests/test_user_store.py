import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class UserStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_DB_BACKEND"] = "sqlite"
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["AUTH_TOKEN_SECRET"] = "user-store-secret-123456789012345678"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "AdminTest123!"
        from services import app_sqlite

        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        from services import app_sqlite

        app_sqlite._INIT_DONE = False
        for key in ("APP_DB_BACKEND", "APP_SQLITE_PATH"):
            os.environ.pop(key, None)
        self.tmp.cleanup()

    def test_create_unique_disable_auth_version_and_public_fields(self) -> None:
        from services import user_admin_service, user_store
        from services.password_service import hash_password

        created = user_admin_service.create_user("alice", "AlicePass123!", "operator")
        self.assertEqual(created["username"], "alice")
        self.assertRaises(user_admin_service.UserAdminError, user_admin_service.create_user, "alice", "AlicePass123!", "operator")
        user_admin_service.create_user("viewer1", "ViewerPass123!", "viewer")
        alice = user_store.get_user("alice")
        self.assertIsNotNone(alice)
        assert alice is not None
        self.assertEqual(alice["role"], "operator")
        disabled, _ = user_admin_service.update_user("alice", {"enabled": False}, "admin")
        self.assertFalse(disabled["enabled"])
        alice = user_store.get_user("alice")
        self.assertIsNotNone(alice)
        assert alice is not None
        self.assertEqual(alice["auth_version"], 2)
        viewer = user_store.get_user("viewer1")
        self.assertIsNotNone(viewer)
        assert viewer is not None
        before = viewer["auth_version"]
        user_store.update_password("viewer1", hash_password("NewViewerPass123!"))
        viewer = user_store.get_user("viewer1")
        self.assertIsNotNone(viewer)
        assert viewer is not None
        self.assertEqual(viewer["auth_version"], before + 1)
        public = user_store.public_user(viewer)
        self.assertNotIn("password_hash", public)
        self.assertEqual(set(public), {"user_id", "username", "role", "enabled", "created_at", "updated_at", "last_login_at", "password_updated_at", "remark"})

    def test_concurrent_username_conflict_has_single_winner(self) -> None:
        from services import user_admin_service

        successes: list[str] = []
        errors: list[str] = []

        def create() -> None:
            try:
                user_admin_service.create_user("race", "RacePass123!", "operator")
                successes.append("ok")
            except Exception as exc:
                errors.append(type(exc).__name__)

        threads = [threading.Thread(target=create) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(errors), 7)


if __name__ == "__main__":
    unittest.main()
