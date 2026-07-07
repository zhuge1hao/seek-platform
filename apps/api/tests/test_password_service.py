import logging
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class PasswordServiceTest(unittest.TestCase):
    def test_pbkdf2_verify_salt_empty_and_legacy_format(self) -> None:
        from services.password_service import hash_password, verify_password

        encoded = hash_password("CorrectHorse123!")
        self.assertTrue(verify_password("CorrectHorse123!", encoded))
        self.assertFalse(verify_password("wrong", encoded))
        self.assertNotEqual(encoded, hash_password("CorrectHorse123!"))
        empty = hash_password("")
        self.assertTrue(verify_password("", empty))
        self.assertFalse(verify_password("anything", "sha1$legacy"))

    def test_admin_password_policy_and_no_plaintext_logging(self) -> None:
        from services.security_config_service import validate_admin_password

        secret = "PlainTextPassword123!"
        records: list[str] = []

        class Handler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record.getMessage())

        handler = Handler()
        root = logging.getLogger()
        root.addHandler(handler)
        try:
            self.assertTrue(validate_admin_password(secret))
            self.assertFalse(validate_admin_password("short"))
        finally:
            root.removeHandler(handler)
        self.assertNotIn(secret, "\n".join(records))


if __name__ == "__main__":
    unittest.main()
