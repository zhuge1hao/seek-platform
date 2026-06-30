from typing import Any, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services import token_service, user_store
from services.password_service import verify_password


bearer_scheme = HTTPBearer(auto_error=False)


def authenticate(username: str, password: str) -> tuple[dict[str, Any] | None, str | None]:
    user = user_store.get_user(username)
    if user is None or not verify_password(password, str(user.get("password_hash") or "")):
        return None, "invalid_credentials"
    if not user.get("enabled", True):
        return user, "disabled"
    return user, None


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录。", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = token_service.decode_token(credentials.credentials)
    except token_service.TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc), headers={"WWW-Authenticate": "Bearer"}) from exc
    user = user_store.get_user(str(payload.get("user_id") or ""))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在。")
    if not user.get("enabled", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号已被禁用。")
    if int(payload.get("auth_version") or 0) != int(user.get("auth_version") or 1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态已失效，请重新登录。")
    return user_store.public_user(user)


def _require_roles(*roles: str) -> Callable[..., dict[str, Any]]:
    def dependency(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user.get("role") not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号无权限执行此操作。")
        return user
    return dependency


require_admin = _require_roles("admin")
require_operator_or_admin = _require_roles("admin", "operator")
require_viewer_or_above = _require_roles("admin", "operator", "viewer")
