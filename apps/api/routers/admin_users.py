from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from services import audit_log_service, task_store, user_admin_service
from services.auth_service import require_admin


router = APIRouter(dependencies=[Depends(require_admin)])


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    role: str
    enabled: bool = True
    remark: str = ""


class UserUpdate(BaseModel):
    role: str | None = None
    enabled: bool | None = None
    remark: str | None = None


class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=8)


def _raise(exc: user_admin_service.UserAdminError) -> None:
    status = 404 if exc.code == "not_found" else 409 if exc.code == "conflict" else 400
    raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/admin/users")
def list_users(role: str | None = None, enabled: bool | None = None, keyword: str | None = None, limit: int = 100) -> dict[str, Any]:
    try:
        return {"users": user_admin_service.list_users(role, enabled, keyword, limit)}
    except user_admin_service.UserAdminError as exc:
        _raise(exc)


@router.post("/admin/users")
def create_user(payload: UserCreate, request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        created = user_admin_service.create_user(payload.username, payload.password, payload.role, payload.enabled, payload.remark)
    except user_admin_service.UserAdminError as exc:
        _raise(exc)
    audit_log_service.write_log("user.create", "success", user, created["user_id"], {"role": created["role"], "enabled": created["enabled"]}, audit_log_service.client_ip(request))
    return created


@router.get("/admin/users/{user_id}")
def get_user(user_id: str) -> dict[str, Any]:
    try:
        return user_admin_service.get_user(user_id)
    except user_admin_service.UserAdminError as exc:
        _raise(exc)


@router.post("/admin/users/{user_id}")
def update_user(user_id: str, payload: UserUpdate, request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    try:
        updated, role_changed = user_admin_service.update_user(user_id, updates, user["user_id"])
    except user_admin_service.UserAdminError as exc:
        _raise(exc)
    action = "user.role.update" if role_changed else "user.update"
    audit_log_service.write_log(action, "success", user, user_id, {"fields": list(updates), "role": updated["role"], "enabled": updated["enabled"]}, audit_log_service.client_ip(request))
    return updated


@router.post("/admin/users/{user_id}/enable")
def enable_user(user_id: str, request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        updated = user_admin_service.enable_user(user_id, user["user_id"])
    except user_admin_service.UserAdminError as exc:
        _raise(exc)
    audit_log_service.write_log("user.enable", "success", user, user_id, {}, audit_log_service.client_ip(request))
    return updated


@router.post("/admin/users/{user_id}/disable")
def disable_user(user_id: str, request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        updated = user_admin_service.disable_user(user_id, user["user_id"])
    except user_admin_service.UserAdminError as exc:
        _raise(exc)
    audit_log_service.write_log("user.disable", "success", user, user_id, {}, audit_log_service.client_ip(request))
    return updated


@router.post("/admin/users/{user_id}/reset-password")
def reset_password(user_id: str, payload: PasswordReset, request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, str]:
    try:
        user_admin_service.reset_password(user_id, payload.new_password)
    except user_admin_service.UserAdminError as exc:
        _raise(exc)
    audit_log_service.write_log("user.password.reset", "success", user, user_id, {}, audit_log_service.client_ip(request))
    return {"status": "success", "message": "密码已重置"}


@router.get("/admin/users/{user_id}/agent-runs")
def get_user_runs(user_id: str, status: str | None = None, agent_type: str | None = None, limit: int = 50) -> dict[str, Any]:
    try:
        user_admin_service.get_user(user_id)
    except user_admin_service.UserAdminError as exc:
        _raise(exc)
    return {"runs": task_store.list_runs(limit=limit, user_id=user_id, status=status, agent_type=agent_type)}


@router.get("/admin/agent-runs")
def get_all_runs(user_id: str | None = None, status: str | None = None, agent_type: str | None = None, limit: int = Query(default=100, ge=1, le=1000)) -> dict[str, Any]:
    return {"runs": task_store.list_runs(limit=limit, user_id=user_id, include_legacy=user_id is None, include_all_users=user_id is None, status=status, agent_type=agent_type)}
