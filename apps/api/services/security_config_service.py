import json
import os
import secrets
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.config_backup_service import resolve_runtime_path


LEGACY_DEV_TOKEN_VALUE = "meizhaiseek-" + "dev-" + "secret"
LEGACY_ADMIN_PASSWORD = "admin" + "123"
GENERATED_AUTH_PATH = "apps/api/runtime/security/generated_secrets.json"
GENERATED_ADMIN_PATH = "apps/api/runtime/security/initial_admin.json"
WEAK_SECRETS = {LEGACY_DEV_TOKEN_VALUE, "", "change-me", "changeme", "secret"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _secure_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def production_mode() -> bool:
    return os.getenv("APP_ENV", "").lower() == "production" or os.getenv("APP_DB_BACKEND", "sqlite").lower() == "postgres"


def _secret_path() -> Path:
    return resolve_runtime_path(os.getenv("GENERATED_SECRETS_PATH", GENERATED_AUTH_PATH))


def _admin_path() -> Path:
    return resolve_runtime_path(os.getenv("GENERATED_ADMIN_PATH", GENERATED_ADMIN_PATH))


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
    data = {"auth_token_secret": secrets.token_urlsafe(48), "created_at": _now(), "source": "generated"}
    _secure_write(path, data)
    return data


def token_secret_status() -> str:
    configured = os.getenv("AUTH_TOKEN_SECRET", "").strip()
    if configured:
        return "invalid" if configured in WEAK_SECRETS or len(configured) < 32 else "configured"
    return "invalid" if production_mode() else "generated"


def get_auth_token_secret() -> str:
    configured = os.getenv("AUTH_TOKEN_SECRET", "").strip()
    if configured:
        if token_secret_status() == "invalid" and production_mode():
            raise RuntimeError("AUTH_TOKEN_SECRET is weak or invalid")
        return configured
    if production_mode():
        raise RuntimeError("AUTH_TOKEN_SECRET is required in production")
    return str(ensure_generated_secret()["auth_token_secret"])


def validate_admin_password(password: str) -> bool:
    return (
        len(password) >= 12
        and any(ch.islower() for ch in password)
        and any(ch.isupper() for ch in password)
        and any(ch.isdigit() for ch in password)
        and any(not ch.isalnum() for ch in password)
    )


def get_initial_admin_password() -> tuple[str, str]:
    configured = os.getenv("INITIAL_ADMIN_PASSWORD") or os.getenv("MEIZHAISEEK_ADMIN_INITIAL_PASSWORD")
    if configured:
        if not validate_admin_password(configured) and production_mode():
            raise RuntimeError("initial admin password does not meet policy")
        return configured, "configured"
    if production_mode():
        raise RuntimeError("INITIAL_ADMIN_PASSWORD is required in production")
    path = _admin_path()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        password = str(data.get("password") or "")
        if password:
            return password, "generated"
    password = f"{secrets.token_urlsafe(9)}aA1!"
    _secure_write(path, {"password": password, "created_at": _now(), "source": "generated", "message": "Change this password immediately."})
    return password, "generated"


def default_admin_password_detected() -> bool:
    if (os.getenv("INITIAL_ADMIN_PASSWORD") or os.getenv("MEIZHAISEEK_ADMIN_INITIAL_PASSWORD") or "") == LEGACY_ADMIN_PASSWORD:
        return True
    try:
        from services import user_store
        from services.password_service import verify_password

        username = os.getenv("MEIZHAISEEK_ADMIN_USERNAME", "admin").strip() or "admin"
        user = user_store.get_user(username)
        return bool(user and verify_password(LEGACY_ADMIN_PASSWORD, str(user.get("password_hash") or "")))
    except Exception:
        return False


def validate_initial_password_policy() -> list[str]:
    password = os.getenv("INITIAL_ADMIN_PASSWORD") or os.getenv("MEIZHAISEEK_ADMIN_INITIAL_PASSWORD") or ""
    if password == LEGACY_ADMIN_PASSWORD:
        return ["Initial admin password is still the default; change it before production."]
    if password and not validate_admin_password(password):
        return ["Initial admin password does not meet the v1.8.1 strength policy."]
    if production_mode() and not password:
        return ["INITIAL_ADMIN_PASSWORD is required in production before creating the first admin."]
    return []


def get_security_warnings() -> list[str]:
    warnings: list[str] = []
    status = token_secret_status()
    if status == "invalid":
        warnings.append("AUTH_TOKEN_SECRET is missing or weak for this runtime mode.")
    elif status == "generated":
        ensure_generated_secret()
        warnings.append("AUTH_TOKEN_SECRET is generated for local development; configure it explicitly for production.")
    warnings.extend(validate_initial_password_policy())
    return warnings


def health_status() -> dict[str, Any]:
    return {
        "token_secret_status": token_secret_status(),
        "default_admin_password_detected": default_admin_password_detected(),
    }
