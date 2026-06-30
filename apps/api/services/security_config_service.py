import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.config_backup_service import resolve_runtime_path


DEFAULT_AUTH_TOKEN_SECRET = "meizhaiseek-dev-secret"
DEFAULT_ADMIN_PASSWORD = "admin123"
GENERATED_SECRET_PATH = "apps/api/runtime/app/generated_secrets.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _secret_path() -> Path:
    return resolve_runtime_path(os.getenv("GENERATED_SECRETS_PATH", GENERATED_SECRET_PATH))


def mask_secret_preview(value: str) -> str:
    if not value:
        return ""
    return f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"


def ensure_generated_secret() -> dict[str, Any]:
    path = _secret_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("auth_token_secret"):
                return data
        except (OSError, ValueError, TypeError):
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "auth_token_secret": secrets.token_urlsafe(48),
        "created_at": _now(),
        "source": "generated",
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def get_auth_token_secret() -> str:
    configured = os.getenv("AUTH_TOKEN_SECRET", "").strip()
    if configured:
        return configured
    return str(ensure_generated_secret()["auth_token_secret"])


def validate_initial_password_policy() -> list[str]:
    password = os.getenv("MEIZHAISEEK_ADMIN_INITIAL_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    if password == DEFAULT_ADMIN_PASSWORD:
        return ["初始管理员密码仍为默认值，请修改 MEIZHAISEEK_ADMIN_INITIAL_PASSWORD 或登录后立即改密。"]
    return []


def get_security_warnings() -> list[str]:
    warnings: list[str] = []
    configured = os.getenv("AUTH_TOKEN_SECRET", "").strip()
    if configured == DEFAULT_AUTH_TOKEN_SECRET:
        warnings.append("AUTH_TOKEN_SECRET 使用默认开发值，请在生产环境修改。")
    elif not configured:
        ensure_generated_secret()
        warnings.append("AUTH_TOKEN_SECRET 未在 .env 设置，已使用 runtime 生成密钥；生产环境建议显式配置。")
    warnings.extend(validate_initial_password_policy())
    return warnings
