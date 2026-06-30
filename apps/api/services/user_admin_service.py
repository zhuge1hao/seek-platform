import re
from datetime import datetime, timezone
from typing import Any

from services import user_store
from services.password_service import hash_password


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
VALID_ROLES = {"admin", "operator", "viewer"}


class UserAdminError(RuntimeError):
    def __init__(self, message: str, code: str = "invalid") -> None:
        super().__init__(message)
        self.code = code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entry(document: dict[str, Any], user_id: str) -> dict[str, Any] | None:
    return next((item for item in document["users"].values() if item.get("user_id") == user_id), None)


def _enabled_admin_count(document: dict[str, Any]) -> int:
    return sum(1 for item in document["users"].values() if item.get("role") == "admin" and item.get("enabled", True))


def list_users(role: str | None = None, enabled: bool | None = None, keyword: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    if role and role not in VALID_ROLES:
        raise UserAdminError("角色参数无效。")
    query = (keyword or "").strip().lower()
    users = []
    for item in user_store.load_users()["users"].values():
        if role and item.get("role") != role:
            continue
        if enabled is not None and bool(item.get("enabled", True)) != enabled:
            continue
        if query and query not in str(item.get("username") or "").lower() and query not in str(item.get("remark") or "").lower():
            continue
        users.append(user_store.public_user(item))
    users.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return users[: max(1, min(limit, 500))]


def get_user(user_id: str) -> dict[str, Any]:
    user = user_store.get_user(user_id)
    if user is None:
        raise UserAdminError("用户不存在。", "not_found")
    return user_store.public_user(user)


def create_user(username: str, password: str, role: str, enabled: bool = True, remark: str = "") -> dict[str, Any]:
    username = username.strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise UserAdminError("用户名只能包含字母、数字、下划线和短横线。")
    if len(password) < 8:
        raise UserAdminError("密码至少需要 8 位。")
    if role not in VALID_ROLES:
        raise UserAdminError("角色只能是 admin、operator 或 viewer。")
    document = user_store.load_users()
    if username in document["users"] or any(item.get("username") == username for item in document["users"].values()):
        raise UserAdminError("用户名已存在。", "conflict")
    now = _now()
    entry = {
        "user_id": username,
        "username": username,
        "role": role,
        "enabled": bool(enabled),
        "password_hash": hash_password(password),
        "auth_version": 1,
        "password_updated_at": now,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
        "remark": remark.strip(),
    }
    document["users"][username] = entry
    user_store.save_users(document)
    return user_store.public_user(entry)


def update_user(user_id: str, updates: dict[str, Any], current_user_id: str) -> tuple[dict[str, Any], bool]:
    document = user_store.load_users()
    entry = _entry(document, user_id)
    if entry is None:
        raise UserAdminError("用户不存在。", "not_found")
    next_role = updates.get("role", entry.get("role"))
    next_enabled = bool(updates.get("enabled", entry.get("enabled", True)))
    if next_role not in VALID_ROLES:
        raise UserAdminError("角色只能是 admin、operator 或 viewer。")
    if user_id == current_user_id and not next_enabled:
        raise UserAdminError("不能禁用当前登录管理员账号。")
    removing_enabled_admin = entry.get("role") == "admin" and entry.get("enabled", True) and (next_role != "admin" or not next_enabled)
    if removing_enabled_admin and _enabled_admin_count(document) <= 1:
        raise UserAdminError("不能禁用或降级最后一个启用的管理员。")
    role_changed = next_role != entry.get("role")
    enabled_changed = next_enabled != bool(entry.get("enabled", True))
    entry["role"] = next_role
    entry["enabled"] = next_enabled
    if "remark" in updates:
        entry["remark"] = str(updates.get("remark") or "").strip()
    if role_changed or enabled_changed:
        entry["auth_version"] = int(entry.get("auth_version") or 1) + 1
    entry["updated_at"] = _now()
    user_store.save_users(document)
    return user_store.public_user(entry), role_changed


def enable_user(user_id: str, current_user_id: str) -> dict[str, Any]:
    return update_user(user_id, {"enabled": True}, current_user_id)[0]


def disable_user(user_id: str, current_user_id: str) -> dict[str, Any]:
    return update_user(user_id, {"enabled": False}, current_user_id)[0]


def reset_password(user_id: str, new_password: str) -> None:
    if len(new_password) < 8:
        raise UserAdminError("新密码至少需要 8 位。")
    if user_store.get_user(user_id) is None:
        raise UserAdminError("用户不存在。", "not_found")
    user_store.update_password(user_id, hash_password(new_password))
