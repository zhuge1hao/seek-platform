import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentSubmitTransactionBudgetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ.update({
            "APP_DB_BACKEND": "sqlite",
            "APP_SQLITE_PATH": str(Path(self.tmp.name) / "app.sqlite3"),
            "APP_LEGACY_JSON_FALLBACK": "false",
            "APP_DB_TRANSACTION_TRACE": "true",
            "INITIAL_ADMIN_PASSWORD": "admin123",
            "AUTH_TOKEN_SECRET": "test-secret",
            "MEIZHAISEEK_ADMIN_USERNAME": "admin",
            "MEIZHAISEEK_ADMIN_INITIAL_PASSWORD": "admin123",
        })
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        os.environ.pop("APP_DB_TRANSACTION_TRACE", None)
        self.tmp.cleanup()

    def test_successful_submit_stays_within_transaction_budget(self) -> None:
        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as client:
            token = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["token"]
            with patch("services.orchestrator.schedule_run", lambda *_args: {"job_id": _args[3]}):
                response = client.post(
                    "/api/agent-runs",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"agent_type": "competitor_analysis", "prompt": "transaction budget"},
                )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertLessEqual(int(response.headers["X-App-DB-Transactions"]), 5)
        self.assertLessEqual(int(response.headers["X-App-DB-Commits"]), 3)
        self.assertEqual(response.json()["queue_job_id"], f"agent-run-{response.json()['run_id']}")


if __name__ == "__main__":
    unittest.main()
