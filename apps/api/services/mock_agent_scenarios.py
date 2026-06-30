from pathlib import Path
from typing import Any

from schemas.agent_runs import DEFAULT_VIDEO_SCRIPT_SESSION_ID


def _base(payload: dict[str, Any], answer: str, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "status": "success",
        "session_id": payload.get("session_id"),
        "answer": answer,
        "summary": summary or {"agent_type": payload.get("agent_type"), "agent_name": payload.get("agent_name"), "mode": payload.get("mode") or "default"},
        "files": [],
        "quality_warnings": [],
        "skill_suggestions": [],
    }


def mock_video_script(payload: dict[str, Any]) -> dict[str, Any]:
    output_dir = Path(payload.get("output_dir") or "E:/USE/codexhome/fenge/outputs/run_mock")
    return {
        "status": "success",
        "session_id": payload.get("session_id") or DEFAULT_VIDEO_SCRIPT_SESSION_ID,
        "answer": "当前为 mock 模式，未调用真实本地 agent。已模拟完成视频脚本拆解。",
        "summary": {
            "mode": payload.get("mode") or "standard_breakdown",
            "video_duration": "00:15",
            "shot_count": 12,
            "subtitle_count": 10,
            "excel_layout": "horizontal_by_shot",
            "quality_status": "mock_passed",
        },
        "files": [
            {"name": "mock_视频拆解报告.xlsx", "path": str(output_dir / "mock_视频拆解报告.xlsx"), "type": "excel"},
            {"name": "mock_校验联排图.jpg", "path": str(output_dir / "mock_校验联排图.jpg"), "type": "contact_sheet"},
            {"name": "mock_拆解日志.json", "path": str(output_dir / "mock_拆解日志.json"), "type": "json"},
        ],
        "quality_warnings": ["mock：第 4 个镜头字幕疑似与画面错位", "mock：第 7 个镜头疑似混入包装文字"],
        "skill_suggestions": ["mock：建议将本次字幕过滤经验沉淀到 white_subtitle_filter.md"],
    }


def mock_generic(payload: dict[str, Any]) -> dict[str, Any]:
    agent_type = payload.get("agent_type") or "generic"
    agent_name = payload.get("agent_name") or agent_type
    skill_templates = payload.get("skill_templates") or []
    skill_names = [template.get("name") for template in skill_templates if template.get("name")]
    skill_text = "、".join(skill_names) if skill_names else "未选择"
    dataset_profiles = payload.get("dataset_profiles") or []
    dataset_text = "、".join(str(item.get("name") or item.get("dataset_id")) for item in dataset_profiles) if dataset_profiles else "未选择"

    scenarios = {
        "smart_selection": "当前为 mock 模式，未调用真实本地 agent。智能选款模拟结果：推荐款式 TOP5 已生成，包含推荐理由、不建议参考方向、风险点和适合 meizhaiseek 的落地建议。",
        "competitor_analysis": "当前为 mock 模式，未调用真实本地 agent。竞品分析模拟结果：已输出低费比高成交组合、价格带机会、标签组合、值得参考链接和风险提醒。",
        "detail_page_planning": "当前为 mock 模式，未调用真实本地 agent。详情页策划模拟结果：已生成 10 屏详情页结构，每屏包含主题、画面建议、文案和 AI 生成提示词。",
        "brand_detail_page_planning": "当前为 mock 模式，未调用真实本地 agent。品牌级详情页策划模拟结果：已生成 10 屏品牌化详情页结构和视觉表达建议。",
        "main_image_breakdown": "当前为 mock 模式，未调用真实本地 agent。主图拆解模拟结果：已输出主图视觉结构、点击点、卖点层级、产品展示方式和可复制改版方向。",
        "hot_main_image_breakdown": "当前为 mock 模式，未调用真实本地 agent。爆款主图拆解模拟结果：已输出主图视觉结构、点击点、卖点层级、产品展示方式和可复制改版方向。",
        "search_main_image": "当前为 mock 模式，未调用真实本地 agent。搜索主图分析模拟结果：已输出搜索场景点击点、主图结构和改版方向。",
        "title_writing": "当前为 mock 模式，未调用真实本地 agent。标题制作模拟结果：已输出标题建议、核心搜索词、剔除词，并提醒最终标题不要出现品牌词。",
        "review_analysis": "当前为 mock 模式，未调用真实本地 agent。评价分析模拟结果：已输出满意点、痛点、差评原因、改进建议和可转化卖点。",
        "qa_analysis": "当前为 mock 模式，未调用真实本地 agent。问大家分析模拟结果：已输出用户疑虑、成交阻碍、痛点和可转化卖点。",
    }
    answer = scenarios.get(agent_type, f"当前为 mock 模式，未调用真实本地 agent。已模拟完成【{agent_name}】任务。")
    return _base(
        payload,
        f"{answer}\n\n选中技能：{skill_text}。\n使用数据集：{dataset_text}。",
        {
            "agent_type": agent_type,
            "agent_name": agent_name,
            "mode": payload.get("mode") or "default",
            "prompt_length": len(payload.get("prompt") or ""),
            "selected_skill_count": len(skill_templates),
            "file_preview_count": len(payload.get("file_previews") or []),
            "dataset_count": len(dataset_profiles),
            "dataset_valid_count": sum(int(item.get("valid_count") or 0) for item in dataset_profiles),
        },
    )
