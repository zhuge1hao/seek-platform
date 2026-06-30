import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from services import audit_log_service, file_store
from services.auth_service import require_operator_or_admin, require_viewer_or_above
from services.file_preview_service import FilePreviewError, preview_file
from services.user_context import uploads_dir


router = APIRouter()

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv"}
ALLOWED_GENERIC_EXTENSIONS = {
    ".xlsx",
    ".xls",
    ".csv",
    ".txt",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".mp4",
    ".mov",
    ".webm",
    ".mkv",
}


def _resolve_path(configured: str, default_base: Path = API_ROOT) -> Path:
    path = Path(configured)
    if not path.is_absolute():
        if len(path.parts) >= 2 and path.parts[0] == "apps" and path.parts[1] == "api":
            path = PROJECT_ROOT / path
        else:
            path = default_base / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve_upload_dir() -> Path:
    return _resolve_path(os.getenv("VIDEO_UPLOAD_DIR", "uploads/videos"))


def _resolve_generic_upload_dir(user_id: str) -> Path:
    return uploads_dir(user_id)


def _sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "file"
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    return name or "file"


def _unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    marker = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    return directory / f"{candidate.stem}_{marker}{candidate.suffix}"


def _file_type(extension: str) -> str:
    if extension in {".xlsx", ".xls", ".csv"}:
        return "excel"
    if extension in {".png", ".jpg", ".jpeg", ".webp"}:
        return "image"
    if extension in {".mp4", ".mov", ".webm", ".mkv"}:
        return "video"
    if extension == ".json":
        return "json"
    if extension == ".txt":
        return "text"
    return "unknown"


@router.post("/files/video/upload")
def upload_video(request: Request, file: UploadFile = File(...), user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, str]:
    safe_name = _sanitize_filename(file.filename or "video")
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 mp4、mov、webm、mkv 视频文件。")

    target_path = _unique_path(_resolve_generic_upload_dir(user["user_id"]), safe_name)
    try:
        with target_path.open("wb") as target:
            shutil.copyfileobj(file.file, target)
    finally:
        file.file.close()

    audit_log_service.write_log("file.upload", "success", user, target_path.name, {"file_type": "video"}, audit_log_service.client_ip(request))
    return {"filename": target_path.name, "saved_path": str(target_path), "message": "视频上传成功"}


@router.post("/files/upload")
def upload_file(request: Request, file: UploadFile = File(...), user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict:
    safe_name = _sanitize_filename(file.filename or "file")
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_GENERIC_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件格式。")

    target_path = _unique_path(_resolve_generic_upload_dir(user["user_id"]), safe_name)
    try:
        with target_path.open("wb") as target:
            shutil.copyfileobj(file.file, target)
    finally:
        file.file.close()

    file_id = f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    record = {
        "file_id": file_id,
        "filename": target_path.name,
        "file_type": _file_type(extension),
        "saved_path": str(target_path),
        "size": target_path.stat().st_size,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "preview_status": "pending",
        "message": "文件上传成功",
    }
    file_store.add_file_record(record, user["user_id"])
    audit_log_service.write_log("file.upload", "success", user, file_id, {"filename": target_path.name, "file_type": record["file_type"]}, audit_log_service.client_ip(request))
    return record


@router.get("/files")
def list_files(
    extensions: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    user: dict[str, Any] = Depends(require_viewer_or_above),
) -> dict[str, list[dict[str, Any]]]:
    allowed = {f".{item.strip().lower().lstrip('.')}" for item in extensions.split(",")} if extensions else set()
    records = file_store.list_file_records(user["user_id"], include_legacy=False, include_all_users=False)
    if allowed:
        records = [record for record in records if Path(str(record.get("filename") or "")).suffix.lower() in allowed]
    records.sort(key=lambda record: record.get("created_at") or "", reverse=True)
    return {"files": records[:limit]}


@router.get("/files/{file_id}/preview")
def get_file_preview(file_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict:
    try:
        return preview_file(file_id, user_id=user["user_id"], include_all_users=user.get("role") == "admin")
    except FilePreviewError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
