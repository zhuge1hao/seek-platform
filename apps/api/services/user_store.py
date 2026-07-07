import os
from datetime import datetime, timezone
from typing import Any

from services import app_sqlite, security_config_service
from services.password_service import hash_password


VIDEO_AGENT_SESSION_ID = "019dd824-f4bb-7273-8ac3-6e19b195ff82"


class UserStoreError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_user() -> dict[str, Any]:
    now = _now()
    username = os.getenv("MEIZHAISEEK_ADMIN_USERNAME", "admin").strip() or "admin"
    password, password_source = security_config_service.get_initial_admin_password()
    return {
        "user_id": username,
        "username": username,
        "role": "admin",
        "enabled": True,
        "password_hash": hash_password(password),
        "auth_version": 1,
        "password_updated_at": now,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
        "remark": f"default admin ({password_source})",
    }


def _row_to_user(row: Any) -> dict[str, Any]:
    metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
    return {
        **metadata,
        "user_id": row["user_id"],
        "username": row["username"],
        "role": row["role"],
        "enabled": bool(row["is_enabled"]),
        "password_hash": row["password_hash"],
        "auth_version": int(row["auth_version"] or 1),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_login_at": row["last_login_at"],
    }


def _upsert_user(conn: Any, user: dict[str, Any]) -> None:
    username = str(user.get("username") or user.get("user_id") or "").strip()
    if not username or not user.get("password_hash"):
        raise UserStoreError("用户数据无效。")
    user_id = str(user.get("user_id") or username)
    conn.execute(
        """
        INSERT INTO users(user_id, username, display_name, password_hash, role, is_enabled, auth_version, created_at, updated_at, last_login_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, display_name=excluded.display_name, password_hash=excluded.password_hash,
          role=excluded.role, is_enabled=excluded.is_enabled, auth_version=excluded.auth_version, updated_at=excluded.updated_at,
          last_login_at=excluded.last_login_at, metadata_json=excluded.metadata_json
        """,
        (
            user_id,
            username,
            user.get("display_name") or user.get("remark") or "",
            user["password_hash"],
            user.get("role") or "viewer",
            1 if user.get("enabled", True) else 0,
            int(user.get("auth_version") or 1),
            user.get("created_at") or _now(),
            user.get("updated_at") or _now(),
            user.get("last_login_at"),
            app_sqlite.json_dump(user),
        ),
    )


def _ensure_default_admin() -> None:
    with app_sqlite.connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        if int(count) == 0:
            _upsert_user(conn, _default_user())


def load_users() -> dict[str, Any]:
    _ensure_default_admin()
    with app_sqlite.connection() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    users = {_row_to_user(row)["username"]: _row_to_user(row) for row in rows}
    return {"schema_version": "1.0", "updated_at": _now(), "users": users}


def get_user(username_or_id: str) -> dict[str, Any] | None:
    _ensure_default_admin()
    with app_sqlite.connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=? OR user_id=? LIMIT 1", (username_or_id, username_or_id)).fetchone()
    return _row_to_user(row).copy() if row else None


def save_users(document: dict[str, Any]) -> None:
    users = document.get("users") if isinstance(document, dict) else None
    if not isinstance(users, dict):
        raise UserStoreError("用户文件结构无效。")
    with app_sqlite.connection() as conn:
        for user in users.values():
            if isinstance(user, dict):
                user["updated_at"] = user.get("updated_at") or _now()
                _upsert_user(conn, user)


def mark_login(user_id: str) -> dict[str, Any]:
    user = get_user(user_id)
    if user is None:
        raise UserStoreError("用户不存在。")
    user["last_login_at"] = _now()
    user["updated_at"] = _now()
    with app_sqlite.connection() as conn:
        _upsert_user(conn, user)
    return user.copy()


def update_password(user_id: str, password_hash: str) -> dict[str, Any]:
    user = get_user(user_id)
    if user is None:
        raise UserStoreError("用户不存在。")
    user["password_hash"] = password_hash
    user["auth_version"] = int(user.get("auth_version") or 1) + 1
    user["password_updated_at"] = _now()
    user["updated_at"] = _now()
    with app_sqlite.connection() as conn:
        _upsert_user(conn, user)
    return user.copy()


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        key: user.get(key)
        for key in (
            "user_id",
            "username",
            "role",
            "enabled",
            "created_at",
            "updated_at",
            "last_login_at",
            "password_updated_at",
            "remark",
        )
    }
