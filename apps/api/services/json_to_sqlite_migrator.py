from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services import app_sqlite
from services.artifact_service import normalize_artifact_file
from services.config_backup_service import resolve_runtime_path


API_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = API_ROOT / "runtime"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _backup_dir() -> Path:
    root = resolve_runtime_path(os.getenv("APP_JSON_LEGACY_BACKUP_DIR", "apps/api/runtime/legacy_json_backups"))
    root.mkdir(parents=True, exist_ok=True)
    return root / _timestamp()


def backup_legacy_json() -> Path:
    target = _backup_dir()
    target.mkdir(parents=True, exist_ok=True)
    for path in RUNTIME_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if "legacy_json_backups" in path.parts or "runtime\\app" in str(path):
            continue
        if path.suffix.lower() not in {".json", ".jsonl", ".txt"}:
            continue
        relative = path.relative_to(RUNTIME_ROOT)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    return target


def _bump(report: dict[str, Any], key: str, amount: int = 1) -> None:
    report["migrated"][key] = int(report["migrated"].get(key, 0)) + amount


def _upsert_user(conn, user: dict[str, Any], report: dict[str, Any]) -> None:
    username = str(user.get("username") or user.get("user_id") or "").strip()
    if not username or not user.get("password_hash"):
        return
    user_id = str(user.get("user_id") or username)
    conn.execute(
        """
        INSERT INTO users(user_id, username, display_name, password_hash, role, is_enabled, auth_version, created_at, updated_at, last_login_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, display_name=excluded.display_name, password_hash=excluded.password_hash,
          role=excluded.role, is_enabled=excluded.is_enabled, auth_version=excluded.auth_version, updated_at=excluded.updated_at,
          last_login_at=excluded.last_login_at, metadata_json=excluded.metadata_json
        """,
        (
            user_id, username, user.get("display_name") or user.get("remark") or "", user["password_hash"],
            user.get("role") or "viewer", 1 if user.get("enabled", True) else 0, int(user.get("auth_version") or 1),
            user.get("created_at") or _now(), user.get("updated_at") or _now(), user.get("last_login_at"),
            app_sqlite.json_dump(user),
        ),
    )
    _bump(report, "users")


def _migrate_users(conn, report: dict[str, Any]) -> None:
    path = RUNTIME_ROOT / "auth" / "users.json"
    if not path.exists():
        return
    raw = _read_json(path)
    users = raw.get("users") if isinstance(raw, dict) else {}
    for user in (users or {}).values():
        if isinstance(user, dict):
            _upsert_user(conn, user, report)


def _migrate_audit(conn, report: dict[str, Any]) -> None:
    path = RUNTIME_ROOT / "audit" / "audit_logs.jsonl"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            created_at = item.get("time") or item.get("created_at") or _now()
            audit_id = hashlib.sha1(line.encode("utf-8")).hexdigest()
            detail = dict(item.get("detail") or {})
            if item.get("status") is not None:
                detail.setdefault("status", item.get("status"))
            conn.execute(
                """
                INSERT OR IGNORE INTO audit_logs(audit_id, user_id, username, action, resource_type, resource_id, detail_json, ip, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (audit_id, item.get("user_id"), item.get("username"), item.get("action") or "unknown", "", item.get("target") or "", app_sqlite.json_dump(detail), item.get("ip"), "", created_at),
            )
            _bump(report, "audit_logs")
        except Exception as exc:
            report["errors"].append({"path": str(path), "error": str(exc)})


def _migrate_qa(conn, report: dict[str, Any]) -> None:
    for path in (RUNTIME_ROOT / "users").glob("*/qa_conversations/qa_conversations.json"):
        user_id = path.parents[1].name
        try:
            raw = _read_json(path)
            for conv in raw.get("conversations") or []:
                if not isinstance(conv, dict) or not conv.get("conversation_id"):
                    continue
                metadata = {key: value for key, value in conv.items() if key not in {"messages"}}
                conn.execute(
                    """
                    INSERT INTO qa_conversations(conversation_id, user_id, title, status, is_archived, created_at, updated_at, last_opened_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(conversation_id) DO UPDATE SET title=excluded.title, status=excluded.status, is_archived=excluded.is_archived,
                      updated_at=excluded.updated_at, last_opened_at=excluded.last_opened_at, metadata_json=excluded.metadata_json
                    """,
                    (conv["conversation_id"], user_id, conv.get("title"), conv.get("status"), 1 if conv.get("is_archived") else 0, conv.get("created_at"), conv.get("updated_at"), conv.get("last_opened_at"), app_sqlite.json_dump(metadata)),
                )
                _bump(report, "qa_conversations")
                for msg in conv.get("messages") or []:
                    if not isinstance(msg, dict) or not msg.get("message_id"):
                        continue
                    conn.execute(
                        """
                        INSERT INTO qa_messages(message_id, conversation_id, user_id, role, content, status, sources_json, warnings_json, error, created_at, updated_at, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(message_id) DO UPDATE SET content=excluded.content, status=excluded.status, sources_json=excluded.sources_json,
                          warnings_json=excluded.warnings_json, error=excluded.error, updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
                        """,
                        (msg["message_id"], conv["conversation_id"], user_id, msg.get("role"), msg.get("content"), msg.get("status"), app_sqlite.json_dump(msg.get("sources") or []), app_sqlite.json_dump(msg.get("warnings") or []), msg.get("error"), msg.get("created_at"), msg.get("updated_at") or msg.get("created_at"), app_sqlite.json_dump(msg)),
                    )
                    _bump(report, "qa_messages")
        except Exception as exc:
            report["errors"].append({"path": str(path), "error": str(exc)})


def _migrate_agent_conversations(conn, report: dict[str, Any]) -> None:
    for path in (RUNTIME_ROOT / "users").glob("*/conversations/conversations.json"):
        user_id = path.parents[1].name
        try:
            raw = _read_json(path)
            for conv in raw.get("conversations") or []:
                if not isinstance(conv, dict) or not conv.get("conversation_id"):
                    continue
                metadata = {key: value for key, value in conv.items() if key not in {"messages"}}
                conn.execute(
                    """
                    INSERT INTO agent_conversations(conversation_id, user_id, title, type, selected_agent_id, agent_type, latest_run_id, status, is_archived, created_at, updated_at, last_opened_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(conversation_id) DO UPDATE SET title=excluded.title, agent_type=excluded.agent_type, latest_run_id=excluded.latest_run_id,
                      status=excluded.status, is_archived=excluded.is_archived, updated_at=excluded.updated_at, last_opened_at=excluded.last_opened_at, metadata_json=excluded.metadata_json
                    """,
                    (conv["conversation_id"], user_id, conv.get("title"), conv.get("type") or "agent", conv.get("selected_agent_id"), conv.get("agent_type"), conv.get("latest_run_id"), conv.get("status"), 1 if conv.get("is_archived") else 0, conv.get("created_at"), conv.get("updated_at"), conv.get("last_opened_at"), app_sqlite.json_dump(metadata)),
                )
                _bump(report, "agent_conversations")
                for msg in conv.get("messages") or []:
                    if not isinstance(msg, dict) or not msg.get("message_id"):
                        continue
                    conn.execute(
                        """
                        INSERT INTO agent_messages(message_id, conversation_id, user_id, role, content, status, run_id, created_at, updated_at, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(message_id) DO UPDATE SET content=excluded.content, status=excluded.status, run_id=excluded.run_id,
                          updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
                        """,
                        (msg["message_id"], conv["conversation_id"], user_id, msg.get("role"), msg.get("content"), msg.get("status"), msg.get("run_id"), msg.get("created_at"), msg.get("updated_at") or msg.get("created_at"), app_sqlite.json_dump(msg)),
                    )
                    _bump(report, "agent_messages")
        except Exception as exc:
            report["errors"].append({"path": str(path), "error": str(exc)})


def _run_paths() -> list[Path]:
    paths = list((RUNTIME_ROOT / "agent_runs").glob("*.json"))
    paths.extend((RUNTIME_ROOT / "users").glob("*/agent_runs/*.json"))
    return paths


def _migrate_agent_runs(conn, report: dict[str, Any]) -> None:
    for path in _run_paths():
        try:
            run = _read_json(path)
            if not isinstance(run, dict) or not run.get("run_id"):
                continue
            user_id = run.get("user_id") or (path.parents[1].name if path.parent.name == "agent_runs" and path.parents[1].name != "runtime" else "admin")
            artifacts = (run.get("result") or {}).get("files") or []
            conn.execute(
                """
                INSERT INTO agent_runs(run_id, user_id, conversation_id, agent_id, agent_type, status, mode, input_json, workflow_options_json, result_json, error, artifacts_json, created_at, updated_at, started_at, completed_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET status=excluded.status, result_json=excluded.result_json, error=excluded.error,
                  artifacts_json=excluded.artifacts_json, updated_at=excluded.updated_at, completed_at=excluded.completed_at, metadata_json=excluded.metadata_json
                """,
                (run["run_id"], user_id, run.get("conversation_id"), run.get("agent_id"), run.get("agent_type"), run.get("status"), run.get("mode"), app_sqlite.json_dump(run), app_sqlite.json_dump(run.get("workflow_options") or {}), app_sqlite.json_dump(run.get("result")), run.get("error"), app_sqlite.json_dump(artifacts), run.get("created_at"), run.get("updated_at"), run.get("started_at"), run.get("completed_at"), app_sqlite.json_dump(run)),
            )
            _bump(report, "agent_runs")
            for index, artifact in enumerate(artifacts if isinstance(artifacts, list) else []):
                if not isinstance(artifact, dict):
                    continue
                storage_path = artifact.get("path") or artifact.get("file_path")
                if not storage_path:
                    continue
                artifact_id = hashlib.sha1(f"{run['run_id']}:{index}:{storage_path}".encode("utf-8")).hexdigest()
                conn.execute(
                    """
                    INSERT OR IGNORE INTO artifacts(artifact_id, user_id, run_id, filename, storage_path, download_url, content_type, size_bytes, created_at, updated_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (artifact_id, user_id, run["run_id"], artifact.get("name"), storage_path, artifact.get("download_url"), artifact.get("type"), None, run.get("created_at"), run.get("updated_at"), app_sqlite.json_dump(artifact)),
                )
                _bump(report, "artifacts")
        except Exception as exc:
            report["errors"].append({"path": str(path), "error": str(exc)})


def _migrate_connectors(conn, report: dict[str, Any]) -> None:
    path = RUNTIME_ROOT / "connectors" / "agent_connectors.json"
    if not path.exists():
        return
    raw = _read_json(path)
    connectors = raw.get("connectors", raw) if isinstance(raw, dict) else {}
    for connector in (connectors or {}).values():
        if not isinstance(connector, dict) or not connector.get("connector_id"):
            continue
        conn.execute(
            """
            INSERT INTO local_agent_connectors(connector_id, name, connector_type, enabled, base_url, command, timeout_seconds, created_by, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(connector_id) DO UPDATE SET name=excluded.name, connector_type=excluded.connector_type, enabled=excluded.enabled,
              base_url=excluded.base_url, command=excluded.command, timeout_seconds=excluded.timeout_seconds, updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
            """,
            (connector["connector_id"], connector.get("name") or connector["connector_id"], connector.get("mode"), 1 if connector.get("enabled", True) else 0, connector.get("base_url"), connector.get("cli_command"), connector.get("timeout_seconds"), connector.get("created_by"), connector.get("created_at"), connector.get("updated_at"), app_sqlite.json_dump(connector)),
        )
        _bump(report, "connectors")


def _migrate_debug_payloads(conn, report: dict[str, Any]) -> None:
    roots = [RUNTIME_ROOT / "debug_payloads"]
    roots.extend(path for path in (RUNTIME_ROOT / "users").glob("*/debug_payloads") if path.is_dir())
    for root in roots:
        for directory in root.iterdir() if root.exists() else []:
            if not directory.is_dir():
                continue
            try:
                metadata_path = directory / "metadata.json"
                request_path = directory / "request.json"
                response_path = directory / "response.json"
                error_path = directory / "error.txt"
                metadata = _read_json(metadata_path) if metadata_path.exists() else {}
                request = _read_json(request_path) if request_path.exists() else None
                response = _read_json(response_path) if response_path.exists() else None
                if error_path.exists():
                    metadata["error"] = error_path.read_text(encoding="utf-8")
                user_id = metadata.get("user_id") or (root.parent.name if root.parent.name != "runtime" else None)
                conn.execute(
                    """
                    INSERT INTO debug_payloads(payload_id, user_id, connector_id, agent_id, request_json, response_json, status, created_at, updated_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(payload_id) DO UPDATE SET response_json=excluded.response_json, status=excluded.status, updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
                    """,
                    (directory.name, user_id, metadata.get("connector_id"), metadata.get("agent_id") or metadata.get("agent_type"), app_sqlite.json_dump(request), app_sqlite.json_dump(response), metadata.get("status"), metadata.get("created_at"), metadata.get("updated_at") or metadata.get("created_at"), app_sqlite.json_dump(metadata)),
                )
                _bump(report, "debug_payloads")
            except Exception as exc:
                report["errors"].append({"path": str(directory), "error": str(exc)})


def _migrate_files(conn, report: dict[str, Any]) -> None:
    paths = list((RUNTIME_ROOT / "users").glob("*/files/files.json"))
    paths.append(RUNTIME_ROOT / "files" / "files.json")
    for path in paths:
        if not path.exists():
            continue
        try:
            raw = _read_json(path)
            items = raw.get("items", raw) if isinstance(raw, dict) else raw
            user_id = path.parents[1].name if path.parent.name == "files" and path.parents[1].name != "runtime" else "legacy"
            for record in items or []:
                if not isinstance(record, dict) or not record.get("file_id"):
                    continue
                owner = record.get("user_id") or user_id
                conn.execute(
                    """
                    INSERT INTO files(file_id, user_id, filename, storage_path, content_type, size_bytes, source, created_at, updated_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(file_id) DO UPDATE SET user_id=excluded.user_id, filename=excluded.filename, storage_path=excluded.storage_path,
                      content_type=excluded.content_type, size_bytes=excluded.size_bytes, updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
                    """,
                    (record["file_id"], owner, record.get("filename"), record.get("saved_path") or record.get("storage_path"), record.get("file_type") or record.get("content_type"), record.get("size"), record.get("source"), record.get("created_at"), record.get("updated_at") or record.get("created_at"), app_sqlite.json_dump(record)),
                )
                _bump(report, "files")
        except Exception as exc:
            report["errors"].append({"path": str(path), "error": str(exc)})


def _dataset_output_files(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    user_id = dataset.get("user_id")
    dataset_id = dataset.get("dataset_id")
    if not user_id or not dataset_id:
        return []
    cleaned_dir = RUNTIME_ROOT / "users" / str(user_id) / "datasets" / str(dataset_id) / "cleaned"
    items: list[dict[str, Any]] = []
    for name in ("cleaned_data.xlsx", "excluded_data.xlsx", "data_profile.json", "metrics_summary.json"):
        path = cleaned_dir / name
        if path.exists():
            suffix = path.suffix.lower()
            items.append(normalize_artifact_file(str(path), file_type="excel" if suffix in {".xlsx", ".xls"} else "json", name=name))
    return items


def _upsert_dataset(conn, dataset: dict[str, Any], report: dict[str, Any]) -> None:
    profile = dataset.get("profile") or {}
    metrics = dataset.get("metrics") or dataset.get("metrics_summary") or {}
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
            dataset["dataset_id"], dataset["user_id"], dataset.get("name"), dataset.get("description"),
            dataset.get("source_filename") or dataset.get("filename") or dataset.get("name"), dataset.get("source_path"),
            dataset.get("status"), int(dataset.get("row_count") or profile.get("raw_count") or 0),
            int(dataset.get("valid_row_count") or profile.get("valid_count") or 0),
            int(dataset.get("excluded_row_count") or profile.get("excluded_count") or 0),
            app_sqlite.json_dump(dataset.get("columns") or []), app_sqlite.json_dump(dataset.get("field_mapping") or {}),
            app_sqlite.json_dump(dataset.get("cleaning_rules") or {}), app_sqlite.json_dump(profile),
            app_sqlite.json_dump(metrics), dataset.get("created_at") or _now(), dataset.get("updated_at") or _now(),
            app_sqlite.json_dump(dataset),
        ),
    )
    _bump(report, "datasets")


def _upsert_dataset_file(conn, dataset: dict[str, Any], file: dict[str, Any], report: dict[str, Any]) -> None:
    storage_path = file.get("path") or file.get("storage_path")
    if not storage_path:
        return
    path = Path(str(storage_path))
    file_id = file.get("file_id") or hashlib.sha1(f"{dataset['dataset_id']}:{storage_path}".encode("utf-8")).hexdigest()
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
    _bump(report, "dataset_files")


def _migrate_datasets(conn, report: dict[str, Any]) -> None:
    for path in (RUNTIME_ROOT / "users").glob("*/datasets/datasets.json"):
        user_id = path.parents[1].name
        try:
            raw = _read_json(path)
            datasets = raw.get("datasets") if isinstance(raw, dict) else raw
        except Exception as exc:
            report["errors"].append({"path": str(path), "error": str(exc)})
            continue
        for item in datasets or []:
            try:
                if not isinstance(item, dict) or not item.get("dataset_id"):
                    continue
                dataset = {**item, "user_id": item.get("user_id") or user_id}
                _upsert_dataset(conn, dataset, report)
                for file in _dataset_output_files(dataset):
                    _upsert_dataset_file(conn, dataset, file, report)
            except Exception as exc:
                report["errors"].append({"path": str(path), "dataset_id": item.get("dataset_id") if isinstance(item, dict) else None, "error": str(exc)})


def migrate_json_to_sqlite(force: bool = False) -> dict[str, Any]:
    if app_sqlite.get_kv("json_migration_completed", False) and app_sqlite.get_kv("dataset_migration_completed", False) and not force:
        return app_sqlite.get_kv("json_migration_report", {"status": "success", "skipped": ["migration already completed"], "errors": []})
    app_sqlite.init_app_db()
    backup_dir = backup_legacy_json()
    report: dict[str, Any] = {
        "status": "success",
        "backup_dir": str(backup_dir),
        "migrated": {
            "users": 0, "audit_logs": 0, "qa_conversations": 0, "qa_messages": 0,
            "agent_conversations": 0, "agent_messages": 0, "agent_runs": 0,
            "connectors": 0, "debug_payloads": 0, "files": 0, "artifacts": 0,
            "datasets": 0, "dataset_files": 0, "dataset_jobs": 0,
        },
        "skipped": [],
        "errors": [],
    }
    with app_sqlite.connection() as conn:
        for step in (_migrate_users, _migrate_audit, _migrate_qa, _migrate_agent_conversations, _migrate_agent_runs, _migrate_connectors, _migrate_debug_payloads, _migrate_files, _migrate_datasets):
            try:
                step(conn, report)
            except Exception as exc:
                report["errors"].append({"step": step.__name__, "error": str(exc)})
        if report["errors"]:
            report["status"] = "warning"
    app_sqlite.set_kv("json_migration_completed", True)
    app_sqlite.set_kv("json_migration_at", _now())
    app_sqlite.set_kv("dataset_migration_completed", True)
    app_sqlite.set_kv("dataset_migration_at", _now())
    app_sqlite.set_kv("json_migration_backup_dir", str(backup_dir))
    app_sqlite.set_kv("json_migration_report", report)
    return report
