import base64
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any


LOGGER = logging.getLogger(__name__)
DEFAULT_SECRET = "meizhaiseek-dev-secret"


class TokenError(RuntimeError):
    pass


def _secret() -> bytes:
    value = os.getenv("AUTH_TOKEN_SECRET", "").strip()
    if not value:
        LOGGER.warning("AUTH_TOKEN_SECRET 未配置，当前使用开发默认值。")
        value = DEFAULT_SECRET
    return value.encode("utf-8")


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_token(user: dict[str, Any]) -> tuple[str, str]:
    expire_hours = max(1, int(os.getenv("AUTH_TOKEN_EXPIRE_HOURS", "168")))
    expires_at = int(time.time()) + expire_hours * 3600
    payload = {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "auth_version": int(user.get("auth_version") or 1),
        "exp": expires_at,
    }
    encoded_payload = _encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    signature = _encode(hmac.new(_secret(), encoded_payload.encode("ascii"), hashlib.sha256).digest())
    expires_iso = datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()
    return f"{encoded_payload}.{signature}", expires_iso


def decode_token(token: str) -> dict[str, Any]:
    try:
        encoded_payload, provided_signature = token.split(".", 1)
        expected = _encode(hmac.new(_secret(), encoded_payload.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(provided_signature, expected):
            raise TokenError("token 签名无效。")
        payload = json.loads(_decode(encoded_payload).decode("utf-8"))
        if int(payload.get("exp") or 0) <= int(time.time()):
            raise TokenError("token 已过期。")
        return payload
    except TokenError:
        raise
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise TokenError("token 无效。") from exc
