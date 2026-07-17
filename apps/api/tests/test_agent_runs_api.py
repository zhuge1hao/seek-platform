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
        os.environ["APP_DB_BACKEND"] = "sqlite"
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["APP_LEGACY_JSON_FALLBACK"] = "false"
        os.environ["APP_SQLITE_AUTO_MIGRATE"] = "false"
        os.environ.pop("APP_ENV", None)
        os.environ["INITIAL_ADMIN_PASSWORD"] = "admin123"
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
            self.assertEqual(runtime["version"], "v1.8.5")
            self.assertEqual(runtime["model"], "meizhaiseek 2.0")
            self.assertEqual(runtime["validation"]["browser_agent_smoke_verified"], "not_run")
            self.assertIn("database", runtime)
            self.assertIn("redis", runtime)
            self.assertIn("queue", runtime)
            self.assertEqual(client.get("/health/live").json()["status"], "ok")
            self.assertIn(client.get("/health/ready").json()["status"], {"ok", "degraded"})
            self.assertFalse(runtime["legacy_json_fallback_enabled"])
            self.assertEqual(runtime["legacy_json_fallback_usage_count"], 0)
            self.assertEqual(runtime["async_store"]["max_concurrency"], 8)
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
                    json={"agent_type": "video_script_breakdown", "prompt": "鎷嗚В娴嬭瘯瑙嗛", "video_path": "E:\\USE\\codexhome\\fenge\\videos\\test\\1.mp4"},
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
            self.assertEqual(messages[0]["content"], "鎷嗚В娴嬭瘯瑙嗛")
            self.assertEqual(messages[1]["run_id"], body["run_id"])
            self.assertEqual(messages[1]["status"], "running")

            from services import task_store

            task_store.update_run(body["run_id"], {"status": "failed", "progress": 100, "error": "local agent disconnected"}, "admin")
            failed_detail = client.get(f"/api/conversations/{body['conversation_id']}", headers=headers).json()
            failed_message = next(message for message in failed_detail["conversation"]["messages"] if message.get("run_id") == body["run_id"])
            self.assertEqual(failed_detail["conversation"]["status"], "failed")
            self.assertEqual(failed_message["status"], "failed")
            self.assertEqual(failed_message["content"], "local agent disconnected")

    def test_video_run_dispatches_workflow_and_writes_failure_to_conversation(self) -> None:
        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as client:
            token = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            with patch("workflows.video_script_workflow.video_agent_status_service.check_status", return_value={"status": "disconnected", "message": "local agent disconnected"}):
                created = client.post(
                    "/api/agent-runs",
                    headers=headers,
                    json={"agent_type": "video_script_breakdown", "prompt": "break video", "video_path": "E:\\USE\\codexhome\\fenge\\videos\\test\\1.mp4"},
                )
            self.assertEqual(created.status_code, 200, created.text)
            body = created.json()
            detail = client.get(f"/api/conversations/{body['conversation_id']}", headers=headers).json()
            self.assertEqual(detail["latest_run"]["run_id"], body["run_id"])
            self.assertEqual(detail["latest_run"]["status"], "failed")
            failed_message = next(message for message in detail["conversation"]["messages"] if message.get("run_id") == body["run_id"])
            self.assertEqual(failed_message["status"], "failed")
            self.assertIn("local agent disconnected", failed_message["content"])

    def test_user_isolation_summary_result_and_blueprint_state_blocks(self) -> None:
        from fastapi.testclient import TestClient
        from main import app
        from services import agent_blueprint_service, task_store, user_admin_service

        user_admin_service.create_user("other", "password123", "operator")

        with TestClient(app) as client:
            admin_token = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["token"]
            admin = {"Authorization": f"Bearer {admin_token}"}
            other_token = client.post("/api/auth/login", json={"username": "other", "password": "password123"}).json()["token"]
            other = {"Authorization": f"Bearer {other_token}"}

            with patch("services.orchestrator.schedule_run", lambda run_id, background_tasks, user_id: None):
                created = client.post("/api/agent-runs", headers=admin, json={"agent_type": "title_writing", "prompt": "hello"})
            self.assertEqual(created.status_code, 200, created.text)
            run_id = created.json()["run_id"]
            task_store.update_run(run_id, {"status": "completed", "progress": 100, "result": {"answer": "ok", "raw_response": "hidden"}}, "admin")
            summary = client.get(f"/api/agent-runs/{run_id}/summary", headers=admin)
            self.assertEqual(summary.status_code, 200, summary.text)
            self.assertNotIn("raw_response", str(summary.json()))
            result = client.get(f"/api/agent-runs/{run_id}/result", headers=admin)
            self.assertEqual(result.json()["result"]["raw_response"], "hidden")
            self.assertIn(client.get(f"/api/agent-runs/{run_id}/summary", headers=other).status_code, {403, 404})

            user = {"user_id": "admin", "username": "admin", "role": "admin"}
            agent_blueprint_service.create_draft({"blueprint_id": "bp_block_title", "agent_id": "title_writing", "name": "block", "display_name": "Block"}, user)
            agent_blueprint_service.set_state("bp_block_title", "disable", "disabled", user)
            blocked = client.post("/api/agent-runs", headers=admin, json={"agent_type": "title_writing", "prompt": "blocked"})
            self.assertEqual(blocked.status_code, 403)
            agent_blueprint_service.set_state("bp_block_title", "enable", "published", user)
            with patch("services.orchestrator.schedule_run", lambda run_id, background_tasks, user_id: None):
                restored = client.post("/api/agent-runs", headers=admin, json={"agent_type": "title_writing", "prompt": "restored"})
            self.assertEqual(restored.status_code, 200, restored.text)


if __name__ == "__main__":
    unittest.main()
