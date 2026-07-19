import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import smoke_minimal  # noqa: E402


class SmokeMinimalTest(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("APP_EXPECTED_VERSION", None)
        os.environ.pop("APP_EXPECTED_MODEL", None)

    def test_runtime_identity_requires_exact_version_and_model(self) -> None:
        smoke_minimal.assert_runtime_identity({"version": "v1.8.8", "model": "meizhaiseek 2.0"}, "v1.8.8", "meizhaiseek 2.0")
        with self.assertRaisesRegex(AssertionError, "version mismatch"):
            smoke_minimal.assert_runtime_identity({"version": "v1.8.7", "model": "meizhaiseek 2.0"}, "v1.8.8", "meizhaiseek 2.0")
        with self.assertRaisesRegex(AssertionError, "version is missing"):
            smoke_minimal.assert_runtime_identity({"model": "meizhaiseek 2.0"}, "v1.8.8", "meizhaiseek 2.0")
        with self.assertRaisesRegex(AssertionError, "model mismatch"):
            smoke_minimal.assert_runtime_identity({"version": "v1.8.8", "model": "wrong"}, "v1.8.8", "meizhaiseek 2.0")

    def test_cli_overrides_env_and_runtime_defaults(self) -> None:
        os.environ["APP_EXPECTED_VERSION"] = "v-env"
        os.environ["APP_EXPECTED_MODEL"] = "model-env"
        self.assertEqual(smoke_minimal.configured_expected_version("v-cli"), "v-cli")
        self.assertEqual(smoke_minimal.configured_expected_model("model-cli"), "model-cli")
        self.assertEqual(smoke_minimal.configured_expected_version(), "v-env")
        self.assertEqual(smoke_minimal.configured_expected_model(), "model-env")

    def test_request_error_does_not_include_auth_token(self) -> None:
        response = Mock()
        response.ok = False
        response.status_code = 503
        response.json.return_value = {"detail": "down"}
        with patch("scripts.smoke_minimal.requests.request", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "503") as ctx:
                smoke_minimal.request_json("GET", "/health", token="secret-token")
        self.assertNotIn("secret-token", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
