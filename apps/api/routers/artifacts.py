from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse

from services import app_sqlite, audit_log_service, task_store
from services.artifact_service import artifact_path_for_download, is_user_artifact_path
from services.auth_service import require_viewer_or_above


router = APIRouter()


@router.get("/artifacts/download")
def download_artifact(request: Request, path: str = Query(..., min_length=1), user: dict[str, Any] = Depends(require_viewer_or_above)) -> FileResponse:
    if not is_user_artifact_path(path, user):
        raise HTTPException(status_code=403, detail="文件不在当前账号允许下载的安全目录内。")
    file_path = artifact_path_for_download(path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在。")
    audit_log_service.write_log("artifact.download", "success", user, file_path.name, {"path": str(file_path)}, audit_log_service.client_ip(request))
    return FileResponse(path=file_path, filename=file_path.name)


@router.get("/agent-runs/{run_id}/artifacts/{artifact_id}/download")
def download_run_artifact(run_id: str, artifact_id: str, request: Request, user: dict[str, Any] = Depends(require_viewer_or_above)) -> FileResponse:
    run = task_store.get_run(run_id) if user.get("role") == "admin" else task_store.get_run(run_id, user["user_id"], include_legacy=False)
    if run is None:
        raise HTTPException(status_code=404, detail="任务不存在。")
    with app_sqlite.connection() as conn:
        row = conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id=? AND run_id=? LIMIT 1",
            (artifact_id, run_id),
        ).fetchone()
    if row is None or (user.get("role") != "admin" and row["user_id"] != user["user_id"]):
        raise HTTPException(status_code=404, detail="文件不存在或无权访问。")
    storage_path = row["storage_path"]
    if not is_user_artifact_path(storage_path, user):
        raise HTTPException(status_code=403, detail="文件不在当前账号允许下载的安全目录内。")
    file_path = artifact_path_for_download(storage_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在。")
    audit_action = "agent.video.artifact_download" if run.get("agent_type") == "video_script_breakdown" else "artifact.download"
    audit_log_service.write_log(audit_action, "success", user, artifact_id, {"run_id": run_id, "file_type": row["content_type"]}, audit_log_service.client_ip(request))
    return FileResponse(path=file_path, filename=row["filename"] or file_path.name)
