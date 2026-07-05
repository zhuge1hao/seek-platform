import asyncio
import gc
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentRunEventsSseTest(unittest.TestCase):
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
        from services import app_sqlite

        app_sqlite._INIT_DONE = False
        for _ in range(5):
            try:
                self.tmp.cleanup()
                return
            except PermissionError:
                gc.collect()
                time.sleep(0.1)
        self.tmp.cleanup()

    def _token(self, client, username: str, password: str) -> dict[str, str]:
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['token']}"}

    def _create_run(self, user_id: str = "admin", status: str = "running") -> dict:
        from services import task_store

        run = task_store.create_run_from_payload(
            {
                "user_id": user_id,
                "username": user_id,
                "role": "operator" if user_id != "admin" else "admin",
                "agent_type": "title_writing",
                "prompt": "stream",
                "workflow_options": {"api_key": "secret", "token": "hidden", "safe": True},
            }
        )
        return task_store.update_run(
            run["run_id"],
            {
                "status": status,
                "progress": 55,
                "current_step": "halfway",
                "result": {"answer": "ok", "raw_response": "do not leak"} if status == "completed" else None,
                "error": "boom" if status == "failed" else None,
            },
            user_id,
        )

    def _collect_events(self, run_id: str, user: dict, max_events: int = 1) -> str:
        async def no_sleep(_seconds: float) -> None:
            return None

        async def collect() -> str:
            from routers.agent_runs import iter_agent_run_events

            chunks = []
            async for chunk in iter_agent_run_events(run_id, user, sleep_func=no_sleep, max_events=max_events):
                chunks.append(chunk)
            return "".join(chunks)

        return asyncio.run(collect())

    def test_auth_owner_payload_status_and_terminal_events(self) -> None:
        from fastapi.testclient import TestClient
        from main import app
        from services import task_store, user_admin_service

        user_admin_service.create_user("other", "password123", "operator")
        with TestClient(app) as client:
            admin = self._token(client, "admin", "admin123")
            other = self._token(client, "other", "password123")

            run = self._create_run()
            self.assertEqual(client.get(f"/api/agent-runs/{run['run_id']}/events").status_code, 401)
            self.assertIn(client.get(f"/api/agent-runs/{run['run_id']}/events", headers=other).status_code, {403, 404})

            admin_user = {"user_id": "admin", "username": "admin", "role": "admin"}
            text = self._collect_events(run["run_id"], admin_user, max_events=1)
            self.assertIn("event: status", text)
            self.assertIn('"progress": 55', text)
            self.assertIn('"current_step": "halfway"', text)
            self.assertNotIn("raw_response", text)
            self.assertNotIn("workflow_options", text)

            still_running = task_store.get_run(run["run_id"], "admin", include_legacy=False)
            self.assertEqual(still_running["status"], "running")

            for status, event in (("completed", "completed"), ("failed", "failed"), ("cancelled", "cancelled")):
                terminal = self._create_run(status=status)
                terminal_text = self._collect_events(terminal["run_id"], admin_user, max_events=1)
                self.assertIn(f"event: {event}", terminal_text)
                self.assertNotIn("raw_response", terminal_text)
                self.assertNotIn("api_key", terminal_text)

    def test_heartbeat_and_multiple_subscribers_do_not_mutate_run(self) -> None:
        from fastapi.testclient import TestClient
        from main import app
        from services import task_store

        with TestClient(app) as client:
            admin = self._token(client, "admin", "admin123")
            run = self._create_run()
            admin_user = {"user_id": "admin", "username": "admin", "role": "admin"}
            first = self._collect_events(run["run_id"], admin_user, max_events=2)
            second = self._collect_events(run["run_id"], admin_user, max_events=2)
            self.assertIn("event: heartbeat", first)
            self.assertIn("event: heartbeat", second)
            persisted = task_store.get_run(run["run_id"], "admin", include_legacy=False)
            self.assertEqual(persisted["status"], "running")
            self.assertEqual(persisted["progress"], 55)


if __name__ == "__main__":
    unittest.main()
