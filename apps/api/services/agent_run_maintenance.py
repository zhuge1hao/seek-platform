import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from services import task_store
from services.config_backup_service import resolve_runtime_path


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def stats() -> dict[str, int]:
    runs = task_store.list_runs(100000, include_legacy=True, include_all_users=True)
    result = {"total": len(runs), "running": 0, "completed": 0, "failed": 0, "cancelled": 0, "stale_running": 0, "missing_result_files": 0}
    stale_before = datetime.now() - timedelta(minutes=int(os.getenv("STALE_RUN_TIMEOUT_MINUTES", "120")))
    for summary in runs:
        status = summary.get("status") or "failed"
        if status in result:
            result[status] += 1
        updated = _parse_time(summary.get("updated_at"))
        if status == "running" and updated and updated < stale_before:
            result["stale_running"] += 1
        run = task_store.get_run(summary.get("run_id") or "")
        files = ((run or {}).get("result") or {}).get("files") or []
        for file in files:
            path = file.get("path")
            if path and not Path(path).exists():
                result["missing_result_files"] += 1
    return result


def repair_stale(timeout_minutes: int = 120) -> dict[str, Any]:
    threshold = datetime.now() - timedelta(minutes=max(1, timeout_minutes))
    repaired = 0
    for summary in task_store.list_runs(100000, include_legacy=True, include_all_users=True):
        if summary.get("status") != "running":
            continue
        updated = _parse_time(summary.get("updated_at") or summary.get("created_at"))
        if updated and updated > threshold:
            continue
        run_id = summary.get("run_id")
        if not run_id:
            continue
        message = "任务执行超时，已由系统自动修复为 failed。"
        task_store.append_log(run_id, message)
        task_store.update_run(run_id, {"status": "failed", "progress": 100, "current_step": "执行超时", "error": message})
        repaired += 1
    return {"repaired": repaired, "timeout_minutes": timeout_minutes}


def cleanup(days: int, statuses: list[str], dry_run: bool = True) -> dict[str, Any]:
    allowed_statuses = set(statuses or ["completed", "failed", "cancelled"]) - {"running"}
    threshold = datetime.now() - timedelta(days=max(1, days))
    archive_dir = resolve_runtime_path("runtime/archived_agent_runs")
    archive_dir.mkdir(parents=True, exist_ok=True)
    candidates: list[Path] = []
    for summary in task_store.list_runs(100000, include_legacy=True, include_all_users=True):
        if summary.get("status") not in allowed_statuses:
            continue
        updated = _parse_time(summary.get("updated_at") or summary.get("created_at"))
        if not updated or updated > threshold:
            continue
        run_id = summary.get("run_id")
        if run_id:
            path = task_store._run_path(run_id, summary.get("user_id"))  # type: ignore[attr-defined]
            if path.exists():
                candidates.append(path)
    if not dry_run:
        for path in candidates:
            owner = path.parents[1].name if path.parent.name == "agent_runs" and path.parents[1].name != "runtime" else "legacy"
            shutil.move(str(path), str(archive_dir / f"{owner}_{path.name}"))
    return {"days": days, "statuses": sorted(allowed_statuses), "dry_run": dry_run, "count": len(candidates)}
