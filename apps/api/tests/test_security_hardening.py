import os
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class SecurityHardeningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["GENERATED_SECRETS_PATH"] = str(Path(self.tmp.name) / "generated_secrets.json")
        os.environ["GENERATED_ADMIN_PATH"] = str(Path(self.tmp.name) / "initial_admin.json")
        os.environ["APP_DB_BACKEND"] = "sqlite"
        os.environ.pop("APP_ENV", None)
        os.environ.pop("AUTH_TOKEN_SECRET", None)
        os.environ.pop("INITIAL_ADMIN_PASSWORD", None)
        os.environ.pop("MEIZHAISEEK_ADMIN_INITIAL_PASSWORD", None)
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        for key in ("APP_SQLITE_PATH", "GENERATED_SECRETS_PATH", "GENERATED_ADMIN_PATH", "APP_DB_BACKEND", "APP_ENV", "AUTH_TOKEN_SECRET", "INITIAL_ADMIN_PASSWORD", "MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"):
            os.environ.pop(key, None)
        self.tmp.cleanup()

    def test_local_secret_is_generated_and_not_leaked(self) -> None:
        from services import security_config_service

        secret = security_config_service.get_auth_token_secret()
        self.assertGreater(len(secret), 32)
        self.assertEqual(security_config_service.health_status()["token_secret_status"], "generated")
        self.assertNotIn(secret, str(security_config_service.health_status()))

    def test_production_requires_strong_secret_and_admin_password(self) -> None:
        from services import security_config_service

        os.environ["APP_ENV"] = "production"
        self.assertEqual(security_config_service.token_secret_status(), "invalid")
        with self.assertRaises(RuntimeError):
            security_config_service.get_auth_token_secret()
        os.environ["AUTH_TOKEN_SECRET"] = "meizhaiseek-dev-secret"
        self.assertEqual(security_config_service.token_secret_status(), "invalid")
        os.environ["AUTH_TOKEN_SECRET"] = "strong-secret-for-v181-tests-123456"
        with self.assertRaises(RuntimeError):
            security_config_service.get_initial_admin_password()
        os.environ["INITIAL_ADMIN_PASSWORD"] = "StrongAdmin123!"
        self.assertEqual(security_config_service.get_initial_admin_password()[1], "configured")

    def test_table_count_rejects_untrusted_table_names(self) -> None:
        from services import app_sqlite

        app_sqlite.init_app_db()
        self.assertIsInstance(app_sqlite.table_count("users"), int)
        for table in ("missing_table", "users; DROP TABLE users", "users where 1=1", '"users"'):
            with self.assertRaises(ValueError):
                app_sqlite.table_count(table)

    def test_cli_connector_rejects_shell_metacharacters(self) -> None:
        from services.local_agent_client import _safe_cli_args

        self.assertEqual(_safe_cli_args("python worker.py"), ["python", "worker.py"])
        for command in ("python worker.py & whoami", "python worker.py | more", "python worker.py; rm x", "python worker.py > out", "python `whoami`"):
            with self.assertRaises(ValueError):
                _safe_cli_args(command)

    def test_pip_audit_gate_reads_powershell_utf16_json(self) -> None:
        from scripts.check_pip_audit_report import _read_report

        path = Path(self.tmp.name) / "pip_audit.json"
        report = {"dependencies": [{"name": "setuptools", "version": "81.0.0", "vulns": [{"id": "PYSEC-2026-3447"}]}]}
        path.write_text(json.dumps(report), encoding="utf-16")
        self.assertEqual(_read_report(path), report)


if __name__ == "__main__":
    unittest.main()
