from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services import artifact_service, file_store, keyword_insight_service, task_store
from services.user_context import artifacts_dir


def _fail(run_id: str, user_id: str, error: str) -> None:
    task_store.append_log(run_id, f"关键词洞察失败：{error}", user_id)
    task_store.update_run(run_id, {"status": "failed", "progress": 100, "current_step": "执行失败", "result": None, "error": error}, user_id)


def _source_file(run: dict[str, Any], user_id: str) -> Path:
    file_ids = run.get("file_ids") or []
    if not file_ids:
        raise keyword_insight_service.KeywordInsightError("请上传关键词 Excel 文件。")
    record = file_store.get_file_record(str(file_ids[0]), user_id=user_id, include_legacy=False)
    if not record:
        raise keyword_insight_service.KeywordInsightError("找不到当前用户上传的关键词 Excel 文件。")
    path = Path(str(record.get("saved_path") or ""))
    if not path.is_file():
        raise keyword_insight_service.KeywordInsightError("上传的关键词 Excel 文件不存在。")
    return path


def run(run_id: str, user_id: str) -> None:
    current = task_store.get_run(run_id, user_id, include_legacy=False)
    if current is None or current.get("status") == "cancelled":
        return
    try:
        task_store.update_run(run_id, {"progress": 20, "current_step": "读取关键词数据"}, user_id)
        source = _source_file(current, user_id)
        options = dict(current.get("workflow_options") or {})
        business_context = dict(options.pop("business_context", {}) or {})
        result = keyword_insight_service.analyze_excel(source, business_context, options)
        output_dir = artifacts_dir(user_id, run_id)
        json_path = output_dir / "keyword_insight_result.json"
        excel_path = output_dir / "关键词洞察报告.xlsx"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        task_store.update_run(run_id, {"progress": 70, "current_step": "导出关键词策略"}, user_id)
        keyword_insight_service.export_excel(result, excel_path, bool(options.get("include_explanation_sheet", False)))
        files = artifact_service.register_run_artifacts(
            user_id,
            run_id,
            [
                {"path": str(excel_path), "type": "excel", "name": excel_path.name},
                {"path": str(json_path), "type": "json", "name": json_path.name},
            ],
        )
        answer = (
            f"关键词洞察完成：共 {result['summary']['total_keywords']} 个搜索词，"
            f"行业必争 {result['summary']['must_win_count']} 个，供给不足蓝海 {result['summary']['supply_gap_count']} 个，"
            f"小众高意向蓝海 {result['summary']['high_intent_count']} 个。"
        )
        task_store.append_log(run_id, "关键词洞察任务执行完成", user_id)
        task_store.update_run(run_id, {"status": "completed", "progress": 100, "current_step": "执行完成", "result": {"answer": answer, "summary": result["summary"], "benchmarks": result["benchmarks"], "files": files}, "error": None}, user_id)
    except Exception as exc:
        _fail(run_id, user_id, str(exc))
