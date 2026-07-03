import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentRunsApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_LEGACY_JSON_FALLBACK"] = "false"
        os.environ["APP_SQLITE_AUTO_MIGRATE"] = "false"
        os.environ["AUTH_TOKEN_SECRET"] = "test-secret"
        os.environ["MEIZHAISEEK_ADMIN_USERNAME"] = "admin"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "admin123"
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_health_and_video_status_disconnected(self) -> None:
        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as client:
            self.assertEqual(client.get("/health").json()["service"], "meizhaiseek-api")
            token = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            runtime = client.get("/api/admin/runtime/health", headers=headers).json()
            self.assertEqual(runtime["version"], "v1.7.1")
            self.assertFalse(runtime["legacy_json_fallback_enabled"])
            status = client.get("/api/agents/video-script/status", headers=headers)
            self.assertNotEqual(status.status_code, 500)

    def test_create_agent_run_persists_conversation(self) -> None:
        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as client:
            token = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            with patch("services.orchestrator.schedule_run", lambda run_id, background_tasks, user_id: None):
                created = client.post(
                    "/api/agent-runs",
                    headers=headers,
                    json={"agent_type": "video_script_breakdown", "prompt": "拆解测试视频", "video_path": "E:\\USE\\codexhome\\fenge\\videos\\test\\1.mp4"},
                )
            self.assertEqual(created.status_code, 200, created.text)
            body = created.json()
            self.assertTrue(body["run_id"].startswith("run_"))
            self.assertTrue(body["conversation_id"].startswith("conv_"))

            conversations = client.get("/api/conversations", headers=headers).json()["conversations"]
            self.assertIn(body["conversation_id"], [item["conversation_id"] for item in conversations])

            detail = client.get(f"/api/conversations/{body['conversation_id']}", headers=headers).json()
            self.assertEqual(detail["latest_run"]["run_id"], body["run_id"])
            messages = detail["conversation"]["messages"]
            self.assertEqual([message["role"] for message in messages], ["user", "assistant"])
            self.assertEqual(messages[0]["content"], "拆解测试视频")
            self.assertEqual(messages[1]["run_id"], body["run_id"])
            self.assertEqual(messages[1]["status"], "running")


if __name__ == "__main__":
    unittest.main()
