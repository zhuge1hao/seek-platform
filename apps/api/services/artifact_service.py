import os
import re
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import quote

from services import app_sqlite
from services.user_context import artifacts_dir, runtime_user_root, uploads_dir


API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]

ARTIFACT_PATH_PATTERNS = [
    r"[A-Za-z]:[\\/][^\s\"'<>|]+?\.(?:xlsx|xls|csv|json|txt|jpg|jpeg|png|webp)",
    r"/mnt/data/[^\s\"'<>|]+?\.(?:xlsx|xls|csv|json|txt|jpg|jpeg|png|webp)",
    r"\./outputs/[^\s\"'<>|]+?\.(?:xlsx|xls|csv|json|txt|jpg|jpeg|png|webp)",
]

DOWNLOADABLE_EXTENSIONS = {".xlsx", ".xls", ".csv", ".json", ".txt", ".jpg", ".jpeg", ".png", ".webp"}


def _resolve_configured_path(value: str, default_base: Path = API_ROOT) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if len(path.parts) >= 2 and path.parts[0] == "apps" and path.parts[1] == "api":
        return PROJECT_ROOT / path
    return default_base / path


def _allowed_roots() -> list[Path]:
    roots = [
        _resolve_configured_path(os.getenv("LOCAL_AGENT_OUTPUT_DIR", "runtime/artifacts")),
        API_ROOT / "runtime" / "artifacts",
        API_ROOT / "runtime" / "users",
        API_ROOT / "uploads",
        _resolve_configured_path(os.getenv("VIDEO_UPLOAD_DIR", "uploads/videos")),
    ]
    return [root.resolve() for root in roots]


def _file_name(path: str) -> str:
    if re.match(r"^[A-Za-z]:", path):
        return PureWindowsPath(path).name
    return PurePosixPath(path).name


def artifact_type_for_path(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".xlsx", ".xls", ".csv"}:
        return "excel"
    if suffix == ".json":
        return "json"
    if suffix == ".txt":
        return "txt"
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        lower = path.lower()
        if "contact" in lower or "sheet" in lower or "联排" in lower or "校验" in lower:
            return "contact_sheet"
        return "image"
    return "file"


def _safe_resolve(file_path: str) -> Path:
    path = Path(file_path)
    if not path.is_absolute():
        if file_path.startswith("./outputs/"):
            path = _resolve_configured_path(file_path.replace("./outputs/", "runtime/artifacts/", 1))
        else:
            path = _resolve_configured_path(file_path)
    return path.resolve()


def build_download_url(file_path: str) -> str:
    return f"/api/artifacts/download?path={quote(file_path, safe='')}"


def is_safe_artifact_path(file_path: str) -> bool:
    try:
        resolved = _safe_resolve(file_path)
    except (OSError, RuntimeError):
        return False

    if resolved.suffix.lower() not in DOWNLOADABLE_EXTENSIONS:
        return False

    allowed_roots = _allowed_roots()
    return any(resolved == root or root in resolved.parents for root in allowed_roots)


def is_user_artifact_path(file_path: str, user: dict) -> bool:
    if not is_safe_artifact_path(file_path):
        return False
    if user.get("role") == "admin":
        return True
    try:
        resolved = _safe_resolve(file_path)
        user_id = str(user.get("user_id") or "")
        roots = [runtime_user_root(user_id).resolve(), uploads_dir(user_id).resolve(), artifacts_dir(user_id).resolve()]
        return any(resolved == root or root in resolved.parents for root in roots)
    except (OSError, RuntimeError, ValueError):
        return False


def artifact_path_for_download(file_path: str) -> Path:
    return _safe_resolve(file_path)


def normalize_artifact_file(file_path: str, file_type: str | None = None, name: str | None = None) -> dict[str, str]:
    return {
        "name": name or _file_name(file_path),
        "path": file_path,
        "type": file_type or artifact_type_for_path(file_path),
        "download_url": build_download_url(file_path),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _content_type(path: Path, file_type: str) -> str:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if suffix == ".json":
        return "application/json"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    if file_type == "quality_report":
        return "text/plain"
    return "application/octet-stream"


def register_run_artifacts(user_id: str, run_id: str, files: list[dict]) -> list[dict]:
    registered: list[dict] = []
    seen: set[str] = set()
    manifest_dir = artifacts_dir(user_id, run_id)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    for item in files:
        path_value = str(item.get("path") or item.get("storage_path") or "")
        if not path_value or path_value in seen:
            continue
        seen.add(path_value)
        path = artifact_path_for_download(path_value)
        file_type = str(item.get("file_type") or item.get("type") or artifact_type_for_path(path_value))
        if path.is_dir():
            manifest_path = manifest_dir / f"{path.name}_manifest.json"
            children = [str(child) for child in sorted(path.rglob("*")) if child.is_file()]
            manifest_path.write_text(json.dumps({"folder": str(path), "files": children}, ensure_ascii=False, indent=2), encoding="utf-8")
            path = manifest_path
            path_value = str(path)
            file_type = "folder_manifest"
        if not path.exists() or not path.is_file():
            continue
        normalized = normalize_artifact_file(path_value, file_type=file_type, name=item.get("name") or item.get("filename"))
        artifact_id = str(item.get("artifact_id") or f"artifact_{uuid.uuid4().hex[:12]}")
        now = _now()
        record = {
            **normalized,
            "artifact_id": artifact_id,
            "filename": normalized["name"],
            "file_type": file_type,
            "storage_path": path_value,
            "size_bytes": path.stat().st_size,
            "created_at": item.get("created_at") or now,
        }
        with app_sqlite.connection() as conn:
            conn.execute(
                """
                INSERT INTO artifacts(artifact_id, user_id, run_id, filename, storage_path, download_url, content_type, size_bytes, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(artifact_id) DO UPDATE SET filename=excluded.filename, storage_path=excluded.storage_path,
                  download_url=excluded.download_url, content_type=excluded.content_type, size_bytes=excluded.size_bytes,
                  updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
                """,
                (
                    artifact_id, user_id, run_id, record["filename"], path_value, normalized["download_url"],
                    _content_type(path, file_type), record["size_bytes"], record["created_at"], now,
                    app_sqlite.json_dump(record),
                ),
            )
        registered.append(record)
    return registered


def normalize_artifact_files(files: list) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()

    for file in files:
        if isinstance(file, str):
            path = file
            name = None
            file_type = None
        elif isinstance(file, dict):
            path = file.get("path") or file.get("file_path") or file.get("url") or ""
            name = file.get("name")
            file_type = file.get("type")
        else:
            path = ""
            name = None
            file_type = None

        if not path or path in seen:
            continue

        seen.add(path)
        normalized.append(normalize_artifact_file(path, file_type=file_type, name=name))

    return normalized


def extract_files_from_text(text: str) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    seen: set[str] = set()

    for pattern in ARTIFACT_PATH_PATTERNS:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            cleaned = match.rstrip("。.，,；;)")
            if cleaned in seen:
                continue
            seen.add(cleaned)
            files.append(normalize_artifact_file(cleaned))

    return files
