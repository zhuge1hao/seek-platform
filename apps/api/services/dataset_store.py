import hashlib
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services import app_sqlite, legacy_json_fallback
from services.artifact_service import normalize_artifact_file
from services.field_mapping_service import preview_payload, write_json
from services.user_context import datasets_dir


class DatasetError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _store_path(user_id: str) -> Path:
    return datasets_dir(user_id) / "datasets.json"


def dataset_dir(user_id: str, dataset_id: str) -> Path:
    if not dataset_id.startswith("dataset_") or any(token in dataset_id for token in ("/", "\\", "..")):
        raise DatasetError("dataset_id 无效。")
    return datasets_dir(user_id) / dataset_id


def _new_id() -> str:
    return f"dataset_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _new_job_id() -> str:
    return f"dataset_job_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _legacy_load(user_id: str) -> list[dict[str, Any]]:
    path = _store_path(user_id)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = raw.get("datasets", []) if isinstance(raw, dict) else raw
        return [item for item in items if isinstance(item, dict)]
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetError(f"数据集记录读取失败：{exc}") from exc


def _metadata(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in record.items()
        if key not in {
            "dataset_id", "user_id", "name", "description", "source_filename", "source_path", "status",
            "row_count", "valid_row_count", "excluded_row_count", "columns", "field_mapping",
            "cleaning_rules", "profile", "metrics", "created_at", "updated_at",
        }
    }


def _row_to_dataset(row: Any) -> dict[str, Any]:
    metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
    profile = app_sqlite.json_load(row["profile_json"], None)
    metrics = app_sqlite.json_load(row["metrics_json"], None)
    record = {
        **metadata,
        "dataset_id": row["dataset_id"],
        "user_id": row["user_id"],
        "name": row["name"] or row["dataset_id"],
        "description": row["description"],
        "source_path": row["source_path"],
        "status": row["status"] or "created",
        "row_count": int(row["row_count"] or 0),
        "created_at": row["created_at"] or _now(),
        "updated_at": row["updated_at"] or _now(),
        "profile": profile or metadata.get("profile") or {
            "raw_count": int(row["row_count"] or 0),
            "valid_count": int(row["valid_row_count"] or 0),
            "excluded_count": int(row["excluded_row_count"] or 0),
        },
    }
    if row["source_filename"]:
        record.setdefault("source_filename", row["source_filename"])
    if metrics is not None:
        record["metrics"] = metrics
    return record


def _upsert_dataset(conn: Any, record: dict[str, Any]) -> None:
    profile = record.get("profile") or {}
    metrics = record.get("metrics") or record.get("metrics_summary")
    valid_count = record.get("valid_row_count", profile.get("valid_count"))
    excluded_count = record.get("excluded_row_count", profile.get("excluded_count"))
    conn.execute(
        """
        INSERT INTO datasets(dataset_id, user_id, name, description, source_filename, source_path, status, row_count, valid_row_count, excluded_row_count, columns_json, field_mapping_json, cleaning_rules_json, profile_json, metrics_json, created_at, updated_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(dataset_id) DO UPDATE SET user_id=excluded.user_id, name=excluded.name, description=excluded.description,
          source_filename=excluded.source_filename, source_path=excluded.source_path, status=excluded.status,
          row_count=excluded.row_count, valid_row_count=excluded.valid_row_count, excluded_row_count=excluded.excluded_row_count,
          columns_json=excluded.columns_json, field_mapping_json=excluded.field_mapping_json,
          cleaning_rules_json=excluded.cleaning_rules_json, profile_json=excluded.profile_json, metrics_json=excluded.metrics_json,
          updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
        """,
        (
            record["dataset_id"], record["user_id"], record.get("name"), record.get("description"),
            record.get("source_filename") or record.get("filename") or record.get("name"), record.get("source_path"),
            record.get("status"), int(record.get("row_count") or profile.get("raw_count") or 0),
            int(valid_count or 0), int(excluded_count or 0),
            app_sqlite.json_dump(record.get("columns") or []), app_sqlite.json_dump(record.get("field_mapping") or {}),
            app_sqlite.json_dump(record.get("cleaning_rules") or {}), app_sqlite.json_dump(profile),
            app_sqlite.json_dump(metrics or {}), record.get("created_at") or _now(), record.get("updated_at") or _now(),
            app_sqlite.json_dump(_metadata(record)),
        ),
    )


def upsert_dataset(record: dict[str, Any]) -> dict[str, Any]:
    with app_sqlite.connection() as conn:
        _upsert_dataset(conn, record)
    return get_dataset(record["dataset_id"], record["user_id"]) or record


def _record_file(conn: Any, dataset: dict[str, Any], file: dict[str, Any]) -> None:
    storage_path = file.get("path") or file.get("storage_path")
    if not storage_path:
        return
    path = Path(str(storage_path))
    file_id = file.get("file_id") or hashlib.sha256(f"{dataset['dataset_id']}:{storage_path}".encode("utf-8")).hexdigest()
    conn.execute(
        """
        INSERT INTO dataset_files(file_id, dataset_id, user_id, file_type, filename, storage_path, content_type, size_bytes, created_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(file_id) DO UPDATE SET file_type=excluded.file_type, filename=excluded.filename, storage_path=excluded.storage_path,
          content_type=excluded.content_type, size_bytes=excluded.size_bytes, metadata_json=excluded.metadata_json
        """,
        (
            file_id, dataset["dataset_id"], dataset["user_id"], file.get("type") or file.get("file_type"),
            file.get("name") or path.name, str(storage_path), file.get("content_type"),
            path.stat().st_size if path.exists() else file.get("size_bytes"), file.get("created_at") or _now(),
            app_sqlite.json_dump(file),
        ),
    )


def record_dataset_files(dataset: dict[str, Any], files: list[dict[str, Any]]) -> None:
    with app_sqlite.connection() as conn:
        for file in files:
            _record_file(conn, dataset, file)


def replace_user_datasets_for_migration(user_id: str, items: list[dict[str, Any]]) -> None:
    # ponytail: bulk replace is only for legacy JSON migration/fallback, never normal API writes.
    with app_sqlite.connection() as conn:
        conn.execute("DELETE FROM dataset_files WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM dataset_jobs WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM datasets WHERE user_id=?", (user_id,))
        for item in items:
            record = {**item, "user_id": item.get("user_id") or user_id, "updated_at": item.get("updated_at") or _now()}
            _upsert_dataset(conn, record)
            for file in _disk_dataset_files(record):
                _record_file(conn, record, file)


def _ensure_legacy_loaded(user_id: str) -> None:
    if not legacy_json_fallback.enabled():
        return
    legacy_json_fallback.warn_once("datasets")
    with app_sqlite.connection() as conn:
        exists = conn.execute("SELECT 1 FROM datasets WHERE user_id=? LIMIT 1", (user_id,)).fetchone()
    if not exists and _store_path(user_id).exists():
        replace_user_datasets_for_migration(user_id, _legacy_load(user_id))


def create_dataset(user_id: str, file_record: dict[str, Any], name: str | None = None) -> dict[str, Any]:
    source = Path(str(file_record.get("saved_path") or ""))
    if source.suffix.lower() not in {".xlsx", ".xls", ".csv"}:
        raise DatasetError("仅支持 xlsx、xls、csv 文件创建数据集。")
    if not source.exists():
        raise DatasetError("上传文件不存在。")
    dataset_id = _new_id()
    root = dataset_dir(user_id, dataset_id)
    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = raw_dir / f"source{source.suffix.lower()}"
    shutil.copy2(source, target)
    try:
        preview = preview_payload(target)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    write_json(root / "preview" / "preview.json", {"dataset_id": dataset_id, **preview})
    now = _now()
    record = {
        "dataset_id": dataset_id, "user_id": user_id, "name": (name or file_record.get("filename") or dataset_id).strip(),
        "source_file_id": file_record.get("file_id"), "source_filename": file_record.get("filename"), "source_path": str(target),
        "original_source_path": str(source), "file_type": "excel" if source.suffix.lower() in {".xlsx", ".xls"} else "csv",
        "status": "created", "row_count": preview["row_count"], "preview_count": preview["preview_count"],
        "columns": preview.get("columns") or [], "created_at": now, "updated_at": now, "cleaned_at": None,
        "profile": {"raw_count": preview["row_count"], "valid_count": 0, "excluded_count": 0},
    }
    saved = upsert_dataset(record)
    return {**saved, "preview": preview, "detected_fields": preview["detected_fields"], "suggested_mapping": preview["suggested_mapping"]}


def list_datasets(user_id: str, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    _ensure_legacy_loaded(user_id)
    clauses = ["user_id=?", "status!='deleted'"]
    params: list[Any] = [user_id]
    if status:
        clauses.append("status=?")
        params.append(status)
    safe_limit = max(1, min(limit, 200))
    with app_sqlite.connection() as conn:
        rows = conn.execute(  # nosec B608: clauses are fixed predicates, values are parameterized.
            f"SELECT * FROM datasets WHERE {' AND '.join(clauses)} ORDER BY updated_at DESC LIMIT ?",  # nosec B608
            (*params, safe_limit),
        ).fetchall()
    return [_row_to_dataset(row) for row in rows]


def list_all_datasets(status: str | None = None, limit: int = 50, user_id: str | None = None) -> list[dict[str, Any]]:
    if user_id:
        return list_datasets(user_id, status, limit)
    clauses = ["status!='deleted'"]
    params: list[Any] = []
    if status:
        clauses.append("status=?")
        params.append(status)
    safe_limit = max(1, min(limit, 200))
    with app_sqlite.connection() as conn:
        rows = conn.execute(  # nosec B608: clauses are fixed predicates, values are parameterized.
            f"SELECT * FROM datasets WHERE {' AND '.join(clauses)} ORDER BY updated_at DESC LIMIT ?",  # nosec B608
            (*params, safe_limit),
        ).fetchall()
    return [_row_to_dataset(row) for row in rows]


def get_dataset(dataset_id: str, user_id: str | None = None, include_all_users: bool = False) -> dict[str, Any] | None:
    if user_id:
        _ensure_legacy_loaded(user_id)
    with app_sqlite.connection() as conn:
        if user_id and not include_all_users:
            row = conn.execute("SELECT * FROM datasets WHERE dataset_id=? AND user_id=?", (dataset_id, user_id)).fetchone()
        elif user_id:
            row = conn.execute(
                "SELECT * FROM datasets WHERE dataset_id=? ORDER BY CASE WHEN user_id=? THEN 0 ELSE 1 END LIMIT 1",
                (dataset_id, user_id),
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM datasets WHERE dataset_id=?", (dataset_id,)).fetchone()
    return _row_to_dataset(row) if row else None


def update_dataset(dataset_id: str, owner_user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    current = get_dataset(dataset_id, owner_user_id)
    if current is None:
        raise DatasetError("数据集不存在。")
    next_record = {**current, **updates, "updated_at": _now()}
    return upsert_dataset(next_record)


def get_preview(dataset: dict[str, Any]) -> dict[str, Any]:
    path = dataset_dir(dataset["user_id"], dataset["dataset_id"]) / "preview" / "preview.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetError(f"数据集预览读取失败：{exc}") from exc


def read_json_file(dataset: dict[str, Any], relative_path: str) -> dict[str, Any]:
    path = dataset_dir(dataset["user_id"], dataset["dataset_id"]) / relative_path
    if not path.exists():
        raise DatasetError("数据集结果尚未生成。")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {"items": value}
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetError(f"数据集结果读取失败：{exc}") from exc


def _disk_dataset_files(dataset: dict[str, Any]) -> list[dict[str, str]]:
    cleaned = dataset_dir(dataset["user_id"], dataset["dataset_id"]) / "cleaned"
    names = ("cleaned_data.xlsx", "excluded_data.xlsx", "data_profile.json", "metrics_summary.json")
    return [normalize_artifact_file(str(cleaned / name)) for name in names if (cleaned / name).exists()]


def dataset_files(dataset: dict[str, Any]) -> list[dict[str, str]]:
    with app_sqlite.connection() as conn:
        rows = conn.execute(
            "SELECT * FROM dataset_files WHERE dataset_id=? AND user_id=? ORDER BY created_at",
            (dataset["dataset_id"], dataset["user_id"]),
        ).fetchall()
    files: list[dict[str, str]] = []
    for row in rows:
        metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
        files.append({
            **metadata,
            "name": metadata.get("name") or row["filename"] or Path(row["storage_path"] or "").name,
            "path": row["storage_path"],
            "type": metadata.get("type") or row["file_type"] or "file",
        })
    if files:
        return files
    disk_files = _disk_dataset_files(dataset)
    if disk_files:
        record_dataset_files(dataset, disk_files)
    return disk_files


def build_dataset_context(dataset_ids: list[str], user_id: str, include_all_users: bool = False) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    profiles: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    for dataset_id in dataset_ids:
        dataset = get_dataset(dataset_id, user_id, include_all_users=include_all_users)
        if not dataset or dataset.get("status") == "deleted":
            raise DatasetError(f"数据集不存在：{dataset_id}")
        if dataset.get("status") != "cleaned":
            raise DatasetError(f"数据集尚未完成清洗：{dataset_id}")
        profile_path = dataset_dir(dataset["user_id"], dataset_id) / "cleaned" / "data_profile.json"
        cleaned_path = dataset_dir(dataset["user_id"], dataset_id) / "cleaned" / "cleaned_data.xlsx"
        if not profile_path.exists() or not cleaned_path.exists():
            raise DatasetError(f"数据集清洗文件缺失：{dataset_id}")
        profiles.append({"dataset_id": dataset_id, "name": dataset.get("name"), **read_json_file(dataset, "cleaned/data_profile.json")})
        files.append({
            "dataset_id": dataset_id, "name": dataset.get("name"),
            "cleaned_data_path": str(cleaned_path), "data_profile_path": str(profile_path),
            "cleaned_data_download_url": normalize_artifact_file(str(cleaned_path))["download_url"],
            "data_profile_download_url": normalize_artifact_file(str(profile_path))["download_url"],
        })
    return profiles, files


def create_dataset_job(dataset_id: str, user_id: str, job_type: str, input_data: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    job_id = _new_job_id()
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            INSERT INTO dataset_jobs(job_id, dataset_id, user_id, job_type, status, input_json, result_json, error, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, dataset_id, user_id, job_type, "pending", app_sqlite.json_dump(input_data), "{}", "", now, now, "{}"),
        )
    return get_dataset_job(job_id, user_id) or {"job_id": job_id, "dataset_id": dataset_id, "user_id": user_id, "job_type": job_type, "status": "pending", "input": input_data}


def get_dataset_job(job_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        if user_id:
            row = conn.execute("SELECT * FROM dataset_jobs WHERE job_id=? AND user_id=?", (job_id, user_id)).fetchone()
        else:
            row = conn.execute("SELECT * FROM dataset_jobs WHERE job_id=?", (job_id,)).fetchone()
    if not row:
        return None
    return {
        "job_id": row["job_id"],
        "dataset_id": row["dataset_id"],
        "user_id": row["user_id"],
        "job_type": row["job_type"],
        "status": row["status"],
        "input": app_sqlite.json_load(row["input_json"], {}) or {},
        "result": app_sqlite.json_load(row["result_json"], {}) or {},
        "error": row["error"] or "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "metadata": app_sqlite.json_load(row["metadata_json"], {}) or {},
    }


def update_dataset_job(job_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    current = get_dataset_job(job_id)
    if current is None:
        return None
    next_job = {**current, **updates, "updated_at": _now()}
    with app_sqlite.connection() as conn:
        conn.execute(
            """
            UPDATE dataset_jobs SET status=?, result_json=?, error=?, updated_at=?, metadata_json=?
            WHERE job_id=?
            """,
            (
                next_job.get("status"),
                app_sqlite.json_dump(next_job.get("result") or {}),
                next_job.get("error") or "",
                next_job["updated_at"],
                app_sqlite.json_dump(next_job.get("metadata") or {}),
                job_id,
            ),
        )
    return get_dataset_job(job_id)


def cancel_dataset_job(job_id: str, user_id: str | None) -> dict[str, Any] | None:
    job = get_dataset_job(job_id, user_id)
    if not job:
        return None
    if job["status"] in {"completed", "failed", "cancelled"}:
        return job
    return update_dataset_job(job_id, {"status": "cancelled", "metadata": {**job.get("metadata", {}), "cancelled_at": _now()}})


def retry_dataset_job(job_id: str, user_id: str) -> dict[str, Any] | None:
    job = get_dataset_job(job_id, user_id)
    if not job:
        return None
    return create_dataset_job(job["dataset_id"], user_id, job["job_type"], job.get("input") or {})
