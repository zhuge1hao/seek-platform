from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from services import audit_log_service, skill_template_service
from services.auth_service import require_admin, require_viewer_or_above
from services.skill_template_service import SkillTemplateStoreError


router = APIRouter()

MOCK_SKILLS = [
    {"id": "product-table-analysis", "name": "商品表格分析"},
    {"id": "competitor-tag-analysis", "name": "竞品标签分析"},
    {"id": "review-clustering", "name": "评论聚类分析"},
    {"id": "detail-page-planning", "name": "详情页策划"},
    {"id": "main-image-suggestions", "name": "主图优化建议"},
    {"id": "link-breakdown", "name": "链接拆解"},
]


@router.get("/skills")
def list_skills(_user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, list[dict[str, str]]]:
    return {"items": MOCK_SKILLS}


@router.get("/skills/templates")
def list_skill_templates(agent_type: str | None = Query(default=None), _user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, list[dict[str, Any]]]:
    try:
        return {"items": skill_template_service.list_templates(agent_type=agent_type)}
    except SkillTemplateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/skills/templates/{skill_id}")
def get_skill_template(skill_id: str, _user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    try:
        template = skill_template_service.get_template(skill_id)
    except SkillTemplateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if template is None:
        raise HTTPException(status_code=404, detail="技能模板不存在。")
    return template


@router.post("/skills/templates")
def save_skill_template(payload: dict[str, Any], request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        result = skill_template_service.upsert_template(payload)
        audit_log_service.write_log("skill_template.update", "success", user, str(result.get("id") or ""), {}, audit_log_service.client_ip(request))
        return result
    except SkillTemplateStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/skills/templates/{skill_id}")
def delete_skill_template(skill_id: str, request: Request, user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        template = skill_template_service.disable_template(skill_id)
    except SkillTemplateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if template is None:
        raise HTTPException(status_code=404, detail="技能模板不存在。")
    audit_log_service.write_log("skill_template.delete", "success", user, skill_id, {}, audit_log_service.client_ip(request))
    return template
