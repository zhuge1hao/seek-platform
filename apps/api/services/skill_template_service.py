import json
import os
from pathlib import Path
from typing import Any

from services.config_guard import guard_skill_templates
from services.config_migration_service import wrap_skill_templates


API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class SkillTemplateStoreError(RuntimeError):
    pass


DEFAULT_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "competitor_low_cost_ratio",
        "name": "低费比高成交分析",
        "agent_types": ["competitor_analysis", "smart_selection"],
        "description": "用于筛选低费比、高成交、高市场占比的竞品链接",
        "required_inputs": ["excel", "text"],
        "prompt_template": "请基于上传的竞品表格，按低费比、高成交、高市场占比筛选值得参考的链接，并输出 TOP5。分析时需要结合成交金额、付费花费、费比、价格带、规格条数、单条价、主面料、核心卖点、视觉表达和人群定位。",
        "output_format": "TOP5 结构化分析",
        "enabled": True,
    },
    {
        "id": "smart_selection_basic",
        "name": "智能选款分析",
        "agent_types": ["smart_selection"],
        "description": "用于商品和竞品选款分析",
        "required_inputs": ["excel", "text"],
        "prompt_template": "请根据我上传的商品表格或竞品表格，筛选值得参考的款式，输出推荐款式、推荐理由、不建议款式、风险点和适合 meizhaiseek 落地的选款建议。",
        "output_format": "结构化选款建议",
        "enabled": True,
    },
    {
        "id": "detail_page_10_screen",
        "name": "详情页10屏策划",
        "agent_types": ["detail_page_planning", "brand_detail_page_planning"],
        "description": "用于生成详情页 10 屏结构",
        "required_inputs": ["text", "image"],
        "prompt_template": "请基于产品卖点和目标人群，生成 10 张详情页结构。每张包含主题、画面建议、核心卖点文案、辅助说明、拍摄建议和 AI 生成提示词。",
        "output_format": "10 屏详情页策划",
        "enabled": True,
    },
    {
        "id": "main_image_breakdown",
        "name": "爆款主图拆解",
        "agent_types": ["hot_main_image_breakdown", "search_main_image", "main_image_planning"],
        "description": "用于拆解主图点击点和视觉结构",
        "required_inputs": ["image", "text"],
        "prompt_template": "请拆解上传主图或竞品主图的视觉结构，分析点击点、产品展示、模特姿势、背景、文案表达、卖点层级，并输出可复制的改版方向。",
        "output_format": "主图拆解报告",
        "enabled": True,
    },
    {
        "id": "title_writing_basic",
        "name": "标题制作",
        "agent_types": ["title_writing"],
        "description": "用于电商标题生成",
        "required_inputs": ["text"],
        "prompt_template": "请根据产品卖点和搜索词，生成符合电商搜索逻辑的标题。标题需要避免重复同义词，突出核心搜索词，品牌词不要出现在最终标题中。",
        "output_format": "标题候选列表",
        "enabled": True,
    },
    {
        "id": "review_painpoint_cluster",
        "name": "评价痛点聚类",
        "agent_types": ["review_analysis", "qa_analysis"],
        "description": "用于评价和问大家内容聚类",
        "required_inputs": ["excel", "text"],
        "prompt_template": "请对用户评价或问大家内容进行聚类，输出满意点、痛点、惊喜点、差评原因、产品改进建议和可转化为卖点的表达。",
        "output_format": "评价痛点聚类结论",
        "enabled": True,
    },
]


def _store_path() -> Path:
    configured = os.getenv("SKILL_TEMPLATE_STORE_PATH", "runtime/configs/skill_templates.json")
    path = Path(configured)
    if not path.is_absolute():
        if len(path.parts) >= 2 and path.parts[0] == "apps" and path.parts[1] == "api":
            path = PROJECT_ROOT / path
        else:
            path = API_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_templates(templates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _store_path().write_text(json.dumps(wrap_skill_templates(templates), ensure_ascii=False, indent=2), encoding="utf-8")
    return templates


def _load_templates() -> list[dict[str, Any]]:
    try:
        return guard_skill_templates(_store_path(), [template.copy() for template in DEFAULT_TEMPLATES])["items"]
    except Exception as exc:
        raise SkillTemplateStoreError(f"技能模板配置读取失败：{exc}") from exc


def reset_templates() -> list[dict[str, Any]]:
    return _write_templates([template.copy() for template in DEFAULT_TEMPLATES])


def guard_templates() -> dict[str, Any]:
    return guard_skill_templates(_store_path(), [template.copy() for template in DEFAULT_TEMPLATES])


def list_templates(agent_type: str | None = None, enabled_only: bool = True) -> list[dict[str, Any]]:
    templates = _load_templates()
    result: list[dict[str, Any]] = []
    for template in templates:
        if enabled_only and not template.get("enabled", True):
            continue
        if agent_type and agent_type not in (template.get("agent_types") or []):
            continue
        result.append(template)
    return result


def get_template(skill_id: str) -> dict[str, Any] | None:
    return next((template for template in _load_templates() if template.get("id") == skill_id), None)


def get_templates_by_ids(skill_ids: list[str]) -> list[dict[str, Any]]:
    wanted = set(skill_ids)
    return [template for template in _load_templates() if template.get("id") in wanted and template.get("enabled", True)]


def upsert_template(payload: dict[str, Any]) -> dict[str, Any]:
    skill_id = payload.get("id")
    if not skill_id:
        raise SkillTemplateStoreError("技能模板 id 不能为空。")
    templates = _load_templates()
    for index, template in enumerate(templates):
        if template.get("id") == skill_id:
            merged = {**template, **payload}
            templates[index] = merged
            _write_templates(templates)
            return merged
    created = {**payload, "enabled": payload.get("enabled", True)}
    templates.append(created)
    _write_templates(templates)
    return created


def disable_template(skill_id: str) -> dict[str, Any] | None:
    templates = _load_templates()
    for index, template in enumerate(templates):
        if template.get("id") == skill_id:
            updated = {**template, "enabled": False}
            templates[index] = updated
            _write_templates(templates)
            return updated
    return None
