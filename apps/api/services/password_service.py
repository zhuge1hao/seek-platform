import base64
import hashlib
import hmac
import secrets


ALGORITHM = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 310_000


def hash_password(password: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "$".join(
        [
            ALGORITHM,
            str(iterations),
            base64.urlsafe_b64encode(salt).decode("ascii").rstrip("="),
            base64.urlsafe_b64encode(digest).decode("ascii").rstrip("="),
        ]
    )


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, expected_text = encoded.split("$", 3)
        if algorithm != ALGORITHM:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _decode(salt_text), int(iterations_text))
        return hmac.compare_digest(actual, _decode(expected_text))
    except (TypeError, ValueError):
        return False
