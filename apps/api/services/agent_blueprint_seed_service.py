from __future__ import annotations

import logging
from typing import Any

from services import app_sqlite
from services import agent_blueprint_service
from services import agent_blueprint_store as store


LOGGER = logging.getLogger(__name__)
SEED_VERSION = "v1.7_video_script_blueprint"
BLUEPRINT_ID = "bp_video_script_breakdown"


def seed_video_blueprint() -> dict[str, Any]:
    if store.get_blueprint(BLUEPRINT_ID):
        app_sqlite.set_kv("agent_blueprint_seed_version", SEED_VERSION)
        return {"status": "exists", "blueprint_id": BLUEPRINT_ID}
    user = {"user_id": "system", "username": "system", "role": "admin"}
    detail = agent_blueprint_service.create_draft({
        "blueprint_id": BLUEPRINT_ID,
        "agent_id": "video_script_breakdown",
        "name": "视频拆解智能体",
        "display_name": "视频拆解智能体",
        "description": "描述平台现有视频拆解链路：通过后端 Connector 调用本地 8001 Agent，生成镜头、字幕、证明帧和输出文件。",
        "category": "视频脚本",
        "status": "published",
        "input_schema": {
            "fields": [
                {"field_id": "video_file", "label": "视频文件", "type": "video", "required": True, "description": "选择视频文件或输入本地视频路径", "validation": {"extensions": [".mp4", ".mov", ".webm", ".mkv"], "max_size_mb": 2048}, "ui": {"group": "基础输入", "order": 1, "advanced": False}},
                {"field_id": "output_dir", "label": "输出目录", "type": "local_path", "required": False, "description": "输出文件保存目录", "ui": {"group": "基础输入", "order": 2, "advanced": False}},
                {"field_id": "mode", "label": "模式", "type": "select", "required": True, "default_value": "shot_text_excel", "options": ["shot_text_excel", "standard", "mock"], "ui": {"group": "执行参数", "order": 3, "advanced": False}},
                {"field_id": "subtitle_region", "label": "字幕区域", "type": "select", "required": False, "default_value": "bottom", "options": ["bottom", "top", "top-bottom", "wide", "middle", "center", "auto"], "ui": {"group": "执行参数", "order": 4, "advanced": True}},
                {"field_id": "ocr_workers", "label": "OCR 并发数", "type": "number", "required": False, "default_value": 6, "ui": {"group": "执行参数", "order": 5, "advanced": True}},
            ]
        },
        "methodology": {"steps": [
            {"step_id": "validate_input", "name": "校验输入", "description": "检查视频文件和输出目录", "order": 1, "required": True, "input_fields": ["video_file", "output_dir"], "output_fields": [], "skill_ids": [], "connector_id": None, "timeout_seconds": 30, "failure_policy": "stop", "acceptance_rules": ["video_file 必须存在"]},
            {"step_id": "check_connector", "name": "检查本地 Agent", "description": "检查 8001 /health", "order": 2, "required": True, "input_fields": [], "output_fields": ["connector_status"], "skill_ids": [], "connector_id": "video_script_agent", "timeout_seconds": 30, "failure_policy": "stop", "acceptance_rules": ["Connector 必须可用"]},
            {"step_id": "prepare_payload", "name": "准备 payload", "description": "映射为本地 Agent /run payload", "order": 3, "required": True, "input_fields": ["video_file", "output_dir", "subtitle_region", "ocr_workers"], "output_fields": ["payload"], "skill_ids": [], "connector_id": "video_script_agent", "timeout_seconds": 30, "failure_policy": "stop", "acceptance_rules": ["payload 只包含本地 Agent 支持字段"]},
            {"step_id": "call_local_agent", "name": "调用本地 Agent", "description": "真实 POST /run", "order": 4, "required": True, "input_fields": ["payload"], "output_fields": ["raw_response"], "skill_ids": [], "connector_id": "video_script_agent", "timeout_seconds": 1800, "failure_policy": "stop", "acceptance_rules": ["不得伪造 completed"]},
            {"step_id": "save_debug_payload", "name": "保存 Debug Payload", "description": "保存真实 request/response/error", "order": 5, "required": True, "input_fields": ["payload", "raw_response"], "output_fields": ["debug_payload"], "skill_ids": [], "connector_id": None, "timeout_seconds": 30, "failure_policy": "continue", "acceptance_rules": ["敏感字段脱敏"]},
            {"step_id": "normalize_result", "name": "标准化结果", "description": "标准化 summary、timeline、subtitles、proof frames", "order": 6, "required": True, "input_fields": ["raw_response"], "output_fields": ["result_json"], "skill_ids": [], "connector_id": None, "timeout_seconds": 60, "failure_policy": "stop", "acceptance_rules": ["summary 字段可读取"]},
            {"step_id": "collect_artifacts", "name": "收集产物", "description": "登记 Excel、JSON、图片和 folder manifest", "order": 7, "required": True, "input_fields": ["result_json"], "output_fields": ["artifacts"], "skill_ids": [], "connector_id": None, "timeout_seconds": 60, "failure_policy": "continue", "acceptance_rules": ["artifact 可下载"]},
            {"step_id": "quality_check", "name": "质量检查", "description": "保留质量警告", "order": 8, "required": False, "input_fields": ["result_json"], "output_fields": ["quality_warnings"], "skill_ids": [], "connector_id": None, "timeout_seconds": 60, "failure_policy": "continue", "acceptance_rules": []},
            {"step_id": "finalize", "name": "完成回写", "description": "写入 run、conversation、assistant message", "order": 9, "required": True, "input_fields": ["result_json", "artifacts"], "output_fields": ["conversation_message"], "skill_ids": [], "connector_id": None, "timeout_seconds": 30, "failure_policy": "stop", "acceptance_rules": ["状态和结果必须回写聊天记录"]},
        ]},
        "prompt_config": {
            "system_prompt": "本蓝图只描述平台调用本地视频拆解 Agent 的目的，不复制本地 Agent 内部 Prompt。",
            "user_prompt_template": "拆解视频：{video_file}",
            "variables": [{"name": "video_file", "required": True, "description": "待处理视频路径"}],
            "output_instructions": "输出镜头、字幕、证明帧、质量警告和文件产物。",
            "model_config": {"provider": "local_agent", "model": "video_script_agent", "temperature": None, "max_tokens": None},
        },
        "execution_config": {"execution_type": "http_connector", "agent_id": "video_script_breakdown", "workflow_type": "video_script_workflow", "connector_id": "video_script_agent", "timeout_seconds": 1800, "retry_policy": {"max_retries": 1, "retry_interval_seconds": 5}, "session_strategy": "fixed", "fixed_session_id": "019dd824-f4bb-7273-8ac3-6e19b195ff82", "output_dir_strategy": "user_input"},
        "output_schema": {"sections": [
            {"section_id": "summary", "type": "summary", "label": "任务概览", "required": True, "order": 1},
            {"section_id": "steps", "type": "steps", "label": "执行步骤", "required": True, "order": 2},
            {"section_id": "timeline", "type": "timeline", "label": "镜头时间轴", "required": False, "order": 3},
            {"section_id": "subtitles", "type": "subtitles", "label": "字幕 OCR", "required": False, "order": 4},
            {"section_id": "selling_points", "type": "selling_points", "label": "卖点", "required": False, "order": 5},
            {"section_id": "proof_frames", "type": "proof_frames", "label": "证明帧", "required": False, "order": 6},
            {"section_id": "warnings", "type": "warnings", "label": "质量警告", "required": False, "order": 7},
            {"section_id": "artifacts", "type": "artifacts", "label": "输出文件", "required": False, "order": 8},
        ]},
        "result_ui_config": {"renderer": "video_breakdown", "tabs": ["summary", "timeline", "subtitles", "proof_frames", "warnings", "artifacts"], "default_tab": "summary", "lazy_sections": ["timeline", "subtitles", "proof_frames"]},
        "acceptance_rules": {"required_result_fields": ["summary", "summary.raw_shot_count", "summary.model_optimized_shot_count"], "required_artifact_types": ["excel", "json"], "max_duration_seconds": 1800},
    }, user)
    blueprint_id = detail["blueprint"]["blueprint_id"]
    version_id = detail["blueprint"]["published_version_id"] or detail["blueprint"]["current_version_id"]
    agent_blueprint_service.save_test_case(blueprint_id, {
        "version_id": version_id,
        "name": "真实视频拆解基础用例",
        "description": "使用本地测试视频验证视频拆解链路。",
        "input": {"agent_type": "video_script_breakdown", "video_file": r"E:\USE\codexhome\fenge\videos\test\1.mp4", "output_dir": r"E:\USE\codexhome\fenge\output\test", "mode": "shot_text_excel", "subtitle_region": "bottom", "ocr_workers": 6},
        "expected_status": "completed",
        "expected_result_rules": {"required_result_fields": ["summary", "summary.raw_shot_count", "summary.model_optimized_shot_count"]},
        "expected_artifacts": {"required_artifact_types": ["excel", "json"]},
        "max_duration_seconds": 1800,
        "requires_connector": True,
    }, user)
    app_sqlite.set_kv("agent_blueprint_seed_version", SEED_VERSION)
    return {"status": "created", "blueprint_id": blueprint_id}


def safe_seed_video_blueprint() -> dict[str, Any]:
    try:
        return seed_video_blueprint()
    except Exception as exc:
        LOGGER.warning("agent blueprint seed failed: %s", exc)
        app_sqlite.set_kv("agent_blueprint_seed_warning", str(exc))
        return {"status": "warning", "warning": str(exc)}
