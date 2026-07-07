from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from services import audit_log_service, rate_limit_service, token_service, user_store
from services.auth_service import authenticate, get_current_user
from services.password_service import hash_password, verify_password


router = APIRouter()


class LoginPayload(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ChangePasswordPayload(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


@router.post("/auth/login")
def login(payload: LoginPayload, background_tasks: BackgroundTasks, request: Request) -> dict[str, Any]:
    ip = audit_log_service.client_ip(request)
    username = payload.username.strip()
    limit = rate_limit_service.check_login(ip, username)
    if not limit.allowed:
        audit_log_service.write_log("auth.login.rate_limited", "failed", None, username, {"reason": "rate_limited"}, ip)
        raise HTTPException(status_code=429, detail="登录尝试过多，请稍后再试。", headers={"Retry-After": str(limit.retry_after)})
    user, error = authenticate(username, payload.password)
    if error == "disabled":
        audit_log_service.write_log("auth.login.failed", "failed", user, payload.username, {"reason": "disabled"}, ip)
        raise HTTPException(status_code=403, detail="当前账号已被禁用。")
    if error or user is None:
        audit_log_service.write_log("auth.login.failed", "failed", None, payload.username, {"reason": "invalid_credentials"}, ip)
        raise HTTPException(status_code=401, detail="账号或密码错误。")
    token, expires_at = token_service.create_token(user)
    background_tasks.add_task(user_store.mark_login, user["user_id"])
    background_tasks.add_task(audit_log_service.write_log, "auth.login.success", "success", user, user["user_id"], {}, ip)
    return {"token": token, "token_type": "bearer", "expires_at": expires_at, "user": user_store.public_user(user)}


@router.post("/auth/logout")
def logout(request: Request, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, str]:
    audit_log_service.write_log("auth.logout", "success", user, user["user_id"], {}, audit_log_service.client_ip(request))
    return {"status": "success", "message": "已退出登录"}


@router.get("/auth/me")
def me(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return user


@router.post("/auth/change-password")
def change_password(payload: ChangePasswordPayload, request: Request, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, str]:
    stored = user_store.get_user(user["user_id"])
    if stored is None or not verify_password(payload.old_password, str(stored.get("password_hash") or "")):
        raise HTTPException(status_code=400, detail="原密码错误。")
    user_store.update_password(user["user_id"], hash_password(payload.new_password))
    audit_log_service.write_log("auth.password.change", "success", user, user["user_id"], {}, audit_log_service.client_ip(request))
    return {"status": "success", "message": "密码修改成功，请重新登录"}
