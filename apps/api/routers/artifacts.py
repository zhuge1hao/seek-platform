from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response, StreamingResponse

from services import app_sqlite, audit_log_service, task_store
from services.artifact_service import artifact_path_for_download, is_user_artifact_path
from services.auth_service import require_viewer_or_above
from storage.factory import provider as storage_provider


router = APIRouter()


def _content_disposition(filename: str) -> str:
    safe = "".join(char if 32 <= ord(char) < 127 and char not in {'"', "\\", ";"} else "_" for char in filename).strip("._")
    fallback = safe or "artifact"
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename)}"


def _artifact_row_or_error(run_id: str, artifact_id: str, user: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    with app_sqlite.connection() as conn:
        row = conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id=? AND run_id=? LIMIT 1",
            (artifact_id, run_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="artifact not found")
    if user.get("role") != "admin" and row["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="artifact access denied")
    run = task_store.get_run(run_id) if user.get("role") == "admin" else task_store.get_run(run_id, user["user_id"], include_legacy=False)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return row, run


@router.get("/artifacts/download")
def download_artifact(request: Request, path: str = Query(..., min_length=1), user: dict[str, Any] = Depends(require_viewer_or_above)) -> FileResponse:
    if not is_user_artifact_path(path, user):
        raise HTTPException(status_code=403, detail="artifact path is not allowed for current user")
    file_path = artifact_path_for_download(path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="artifact not found")
    audit_log_service.write_log("artifact.download", "success", user, file_path.name, {"path": str(file_path)}, audit_log_service.client_ip(request))
    return FileResponse(path=file_path, filename=file_path.name)


@router.get("/agent-runs/{run_id}/artifacts/{artifact_id}/download")
def download_run_artifact(run_id: str, artifact_id: str, request: Request, user: dict[str, Any] = Depends(require_viewer_or_above)) -> Response:
    row, run = _artifact_row_or_error(run_id, artifact_id, user)
    storage_backend = row["storage_backend"] if "storage_backend" in row.keys() else "local"
    object_key = row["object_key"] if "object_key" in row.keys() else ""
    audit_action = "agent.video.artifact_download" if run.get("agent_type") == "video_script_breakdown" else "artifact.download"
    if storage_backend == "s3":
        if not object_key:
            raise HTTPException(status_code=404, detail="artifact not found")
        audit_log_service.write_log(audit_action, "success", user, artifact_id, {"run_id": run_id, "file_type": row["content_type"], "storage_backend": "s3"}, audit_log_service.client_ip(request))
        body = storage_provider().open_file(object_key)
        return StreamingResponse(body.iter_chunks(), media_type=row["content_type"] or "application/octet-stream", headers={"Content-Disposition": _content_disposition(row["filename"] or artifact_id)})

    storage_path = row["storage_path"]
    if not is_user_artifact_path(storage_path, user):
        raise HTTPException(status_code=403, detail="artifact path is not allowed for current user")
    file_path = artifact_path_for_download(storage_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="artifact not found")
    audit_log_service.write_log(audit_action, "success", user, artifact_id, {"run_id": run_id, "file_type": row["content_type"]}, audit_log_service.client_ip(request))
    return FileResponse(path=file_path, filename=row["filename"] or file_path.name)


@router.get("/agent-runs/{run_id}/artifacts/{artifact_id}/signed-url")
def signed_run_artifact_url(run_id: str, artifact_id: str, request: Request, ttl_seconds: int = Query(60, ge=1, le=900), user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    row, run = _artifact_row_or_error(run_id, artifact_id, user)
    storage_backend = row["storage_backend"] if "storage_backend" in row.keys() else "local"
    object_key = row["object_key"] if "object_key" in row.keys() else ""
    if storage_backend == "s3":
        signer = getattr(storage_provider(), "presigned_download_url", None)
        if signer is None or not object_key:
            raise HTTPException(status_code=404, detail="artifact not found")
        url = signer(object_key, ttl_seconds)
    else:
        url = f"/api/agent-runs/{run_id}/artifacts/{artifact_id}/download"
    audit_action = "agent.video.artifact_signed_url" if run.get("agent_type") == "video_script_breakdown" else "artifact.signed_url"
    audit_log_service.write_log(audit_action, "success", user, artifact_id, {"run_id": run_id, "storage_backend": storage_backend, "ttl_seconds": ttl_seconds}, audit_log_service.client_ip(request))
    return {"artifact_id": artifact_id, "run_id": run_id, "storage_backend": storage_backend, "ttl_seconds": ttl_seconds, "url": url}
