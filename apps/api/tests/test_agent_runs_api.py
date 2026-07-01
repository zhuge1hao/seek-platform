import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentRunsApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_LEGACY_JSON_FALLBACK"] = "false"
        os.environ["MEIZHAISEEK_ADMIN_USERNAME"] = "admin"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "admin123"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_health_and_video_status_disconnected(self) -> None:
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        self.assertEqual(client.get("/health").json()["service"], "meizhaiseek-api")
        token = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        runtime = client.get("/api/admin/runtime/health", headers=headers).json()
        self.assertEqual(runtime["version"], "v1.6.5")
        self.assertFalse(runtime["legacy_json_fallback_enabled"])
        status = client.get("/api/agents/video-script/status", headers=headers)
        self.assertNotEqual(status.status_code, 500)


if __name__ == "__main__":
    unittest.main()
