import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ArtifactServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        os.environ["APP_DB_BACKEND"] = "sqlite"
        os.environ["APP_SQLITE_PATH"] = str(root / "app.sqlite3")
        os.environ["LOCAL_AGENT_OUTPUT_DIR"] = str(root / "artifacts")
        os.environ["AUTH_TOKEN_SECRET"] = "artifact-secret-123456789012345678"
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "AdminTest123!"
        from services import app_sqlite

        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        from services import app_sqlite

        app_sqlite._INIT_DONE = False
        for key in ("APP_DB_BACKEND", "APP_SQLITE_PATH", "LOCAL_AGENT_OUTPUT_DIR", "ARTIFACT_STORAGE_BACKEND", "S3_BUCKET", "S3_SECRET_ACCESS_KEY"):
            os.environ.pop(key, None)
        self.tmp.cleanup()

    def test_local_registration_checksum_content_type_and_user_isolation(self) -> None:
        from services import artifact_service
        from services.user_context import artifacts_dir

        path = artifacts_dir("alice", "run1") / "result.json"
        path.write_text('{"ok": true}', encoding="utf-8")
        records = artifact_service.register_run_artifacts("alice", "run1", [{"path": str(path), "type": "json"}])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["storage_backend"], "local")
        self.assertEqual(len(records[0]["checksum"]), 64)
        self.assertTrue(artifact_service.is_user_artifact_path(str(path), {"user_id": "alice", "role": "operator"}))
        self.assertFalse(artifact_service.is_user_artifact_path(str(path), {"user_id": "bob", "role": "operator"}))
        self.assertTrue(artifact_service.is_user_artifact_path(str(path), {"user_id": "admin", "role": "admin"}))
        self.assertFalse(artifact_service.is_safe_artifact_path(str(path.with_suffix(".exe"))))
        self.assertRaises(FileNotFoundError, artifact_service.artifact_path_for_download, str(path.parent / "missing.json"))

    def test_storage_backends_reject_traversal_and_do_not_leak_s3_secret(self) -> None:
        from storage.local import LocalArtifactStorage
        from storage.s3 import S3ArtifactStorage

        source = Path(self.tmp.name) / "file.txt"
        source.write_text("hello", encoding="utf-8")
        self.assertRaises(ValueError, LocalArtifactStorage().put_file, source, "../escape.txt")
        os.environ["S3_BUCKET"] = "test-bucket"
        os.environ["S3_SECRET_ACCESS_KEY"] = "super-secret"

        class FakeS3:
            def upload_file(self, *_args, **_kwargs) -> None:
                return None

        with patch.object(S3ArtifactStorage, "_client", return_value=FakeS3()):
            info = S3ArtifactStorage().put_file(source, "artifacts/alice/run1/file.txt", "text/plain")
        self.assertEqual(info["storage_backend"], "s3")
        self.assertNotIn("super-secret", str(info))
        self.assertRaises(ValueError, S3ArtifactStorage().put_file, source, "artifacts/../file.txt")


if __name__ == "__main__":
    unittest.main()
