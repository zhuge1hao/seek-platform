from __future__ import annotations

import argparse
import json
import os
import queue
import secrets
import sys
import threading
import time
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import app_sqlite, token_service, user_admin_service, user_store
from services.artifact_service import resolve_artifact_path


DEFAULT_VIDEO = r"E:\USE\codexhome\fenge\videos\test\1.mp4"
DEFAULT_OUTPUT_ROOT = r"E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api\runtime\video-agent-output"
SESSION_ID = "019dd824-f4bb-7273-8ac3-6e19b195ff82"


def request_json(method: str, api: str, path: str, token: str | None = None, timeout: int = 30, **kwargs: Any) -> Any:
    headers = dict(kwargs.pop("headers", {}) or {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, f"{api}{path}", headers=headers, timeout=timeout, **kwargs)
    try:
        data = response.json()
    except ValueError:
        data = response.text
    if not response.ok:
        raise RuntimeError(f"{method} {path} failed {response.status_code}: {data}")
    return data


def create_validation_token() -> tuple[str, str]:
    username = f"v184_p0_{int(time.time())}_{secrets.token_hex(3)}"
    password = f"V184-{secrets.token_urlsafe(18)}"
    user_admin_service.create_user(username, password, "admin", True, "v1.8.4 P0 validation")
    user = user_store.get_user(username)
    if user is None:
        raise RuntimeError("temporary validation user was not created")
    token, _expires = token_service.create_token(user)
    return username, token


def stream_sse(api: str, run_id: str, token: str, events: queue.Queue[dict[str, Any]]) -> None:
    headers = {"Authorization": f"Bearer {token}", "Accept": "text/event-stream"}
    try:
        with requests.get(f"{api}/api/agent-runs/{run_id}/events", headers=headers, stream=True, timeout=(10, 1900)) as response:
            response.raise_for_status()
            event = "message"
            data_lines: list[str] = []
            for raw_line in response.iter_lines(decode_unicode=True):
                line = raw_line or ""
                if line.startswith("event: "):
                    event = line[7:]
                elif line.startswith("data: "):
                    data_lines.append(line[6:])
                elif line == "" and data_lines:
                    data = json.loads("\n".join(data_lines))
                    events.put({"event": event, "status": data.get("status"), "progress": data.get("progress"), "step": data.get("current_step")})
                    if data.get("status") in {"completed", "failed", "cancelled"}:
                        break
                    event = "message"
                    data_lines = []
    except Exception as exc:
        events.put({"event": "sse_error", "error": type(exc).__name__, "message": str(exc)[:200]})


def db_counts(run_id: str, conversation_id: str) -> dict[str, int]:
    with app_sqlite.connection() as conn:
        return {
            "agent_runs": int(conn.execute("SELECT COUNT(*) AS count FROM agent_runs WHERE run_id=?", (run_id,)).fetchone()["count"]),
            "agent_conversations": int(conn.execute("SELECT COUNT(*) AS count FROM agent_conversations WHERE conversation_id=?", (conversation_id,)).fetchone()["count"]),
            "agent_messages": int(conn.execute("SELECT COUNT(*) AS count FROM agent_messages WHERE conversation_id=?", (conversation_id,)).fetchone()["count"]),
            "artifacts": int(conn.execute("SELECT COUNT(*) AS count FROM artifacts WHERE run_id=?", (run_id,)).fetchone()["count"]),
            "debug_payloads": int(conn.execute("SELECT COUNT(*) AS count FROM debug_payloads WHERE payload_id=?", (run_id,)).fetchone()["count"]),
        }


def download_artifact(api: str, run_id: str, item: dict[str, Any], token: str) -> dict[str, Any]:
    artifact_id = item.get("artifact_id")
    file_type = item.get("file_type") or item.get("type")
    filename = item.get("filename") or item.get("name") or artifact_id
    if not artifact_id:
        return {"filename": filename, "file_type": file_type, "download": "no_artifact_id", "ok": False}
    response = requests.get(
        f"{api}/api/agent-runs/{run_id}/artifacts/{artifact_id}/download",
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
        stream=True,
    )
    size = 0
    for chunk in response.iter_content(chunk_size=65536):
        if chunk:
            size += len(chunk)
            if size > 1024 * 1024:
                break
    return {
        "filename": filename,
        "file_type": file_type,
        "status_code": response.status_code,
        "sampled_bytes": size,
        "content_type": response.headers.get("content-type"),
        "ok": response.ok and size > 0,
    }


def select_downloads(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for kind in ("excel", "json", "image", "contact_sheet", "folder_manifest"):
        item = next((entry for entry in files if (entry.get("file_type") or entry.get("type")) == kind), None)
        artifact_id = str((item or {}).get("artifact_id") or "")
        if item and artifact_id not in seen:
            selected.append(item)
            seen.add(artifact_id)
    return selected


def list_output_files(output_dir: str) -> list[str]:
    root = resolve_artifact_path(output_dir)
    if not root.exists() or not root.is_dir():
        return []
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--video-path", default=os.getenv("VIDEO_AGENT_TEST_VIDEO", DEFAULT_VIDEO))
    parser.add_argument("--output-root", default=os.getenv("VIDEO_AGENT_TEST_OUTPUT_ROOT", DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()
    api = args.api_base.rstrip("/")
    output_dir = str(Path(args.output_root) / f"v184-p0-{int(time.time())}")

    username, token = create_validation_token()
    runtime = request_json("GET", api, "/api/admin/runtime/health", token)
    before = request_json("GET", api, "/api/conversations?limit=200", token).get("conversations") or []
    before_ids = {item.get("conversation_id") for item in before}
    created = request_json(
        "POST",
        api,
        "/api/agent-runs",
        token,
        json={
            "agent_type": "video_script_breakdown",
            "mode": "shot_text_excel",
            "prompt": "v1.8.4 P0 real video E2E acceptance",
            "video_path": args.video_path,
            "session_id": SESSION_ID,
            "workflow_options": {
                "output_dir": output_dir,
                "subtitle_region": "bottom",
                "subtitle_regions": ["bottom"],
                "ocr_workers": 6,
                "ocr_threads": 6,
                "export_json": True,
                "export_excel": True,
                "export_keyframes": True,
                "keep_debug_payload": True,
            },
        },
    )
    run_id = created["run_id"]
    conversation_id = created["conversation_id"]

    event_queue: queue.Queue[dict[str, Any]] = queue.Queue()
    thread = threading.Thread(target=stream_sse, args=(api, run_id, token, event_queue), daemon=True)
    thread.start()

    deadline = time.time() + args.timeout_seconds
    last_status = ""
    summary: dict[str, Any] = {}
    while time.time() < deadline:
        summary = request_json("GET", api, f"/api/agent-runs/{run_id}/summary", token)
        status = str(summary.get("status") or "")
        if status != last_status:
            print(json.dumps({"progress": True, "run_id": run_id, "status": status, "percent": summary.get("progress"), "step": summary.get("current_step")}, ensure_ascii=False))
            last_status = status
        if status in {"completed", "failed", "cancelled"}:
            break
        time.sleep(5)
    thread.join(timeout=5)
    events: list[dict[str, Any]] = []
    while not event_queue.empty():
        events.append(event_queue.get())

    detail = request_json("GET", api, f"/api/agent-runs/{run_id}/result", token)
    conversation = request_json("GET", api, f"/api/conversations/{conversation_id}", token)
    after = request_json("GET", api, "/api/conversations?limit=200", token).get("conversations") or []
    files = (detail.get("result") or {}).get("files") or []
    result_summary = (detail.get("result") or {}).get("summary") or {}
    messages = (conversation.get("conversation") or {}).get("messages") or []
    assistant = [item for item in messages if item.get("role") == "assistant" and item.get("run_id") == run_id]
    user_messages = [item for item in messages if item.get("role") == "user" and item.get("run_id") == run_id]
    downloads = [download_artifact(api, run_id, item, token) for item in select_downloads(files)]
    output_files = list_output_files(output_dir)
    final_shots = result_summary.get("model_optimized_shot_count")
    data_columns = result_summary.get("excel_column_count")
    embedded_images = result_summary.get("excel_image_count")
    evidence_files = [item for item in files if (item.get("file_type") or item.get("type")) in {"image", "contact_sheet"}]

    report = {
        "status": detail.get("status"),
        "runtime_version": runtime.get("version"),
        "runtime_model": runtime.get("model"),
        "validation": runtime.get("validation"),
        "temp_username": username,
        "run_id": run_id,
        "conversation_id": conversation_id,
        "queue_job_id": created.get("queue_job_id"),
        "db_counts": db_counts(run_id, conversation_id),
        "message_checks": {
            "user_messages_for_run": len(user_messages),
            "assistant_messages_for_run": len(assistant),
            "assistant_status": assistant[-1].get("status") if assistant else None,
        },
        "conversation_list_contains_new": conversation_id in {item.get("conversation_id") for item in after},
        "conversation_list_was_new": conversation_id not in before_ids,
        "sse_events": events,
        "summary_counts": {
            "final_shots": final_shots,
            "data_columns": data_columns,
            "embedded_images": embedded_images,
            "consistent": final_shots is not None and final_shots == data_columns == embedded_images,
        },
        "artifact_types": sorted({str(item.get("file_type") or item.get("type")) for item in files}),
        "artifact_count": len(files),
        "evidence_file_count": len(evidence_files),
        "downloads": downloads,
        "output_dir": output_dir,
        "output_file_count": len(output_files),
        "output_file_sample": output_files[:20],
        "error": detail.get("error"),
    }
    print("P0_RESULT_JSON=" + json.dumps(report, ensure_ascii=False, indent=2))
    ok = (
        report["status"] == "completed"
        and bool(report["run_id"] and report["conversation_id"] and report["queue_job_id"])
        and report["db_counts"]["agent_runs"] == 1
        and report["db_counts"]["agent_conversations"] == 1
        and report["db_counts"]["agent_messages"] >= 2
        and report["message_checks"]["assistant_status"] == "completed"
        and report["conversation_list_contains_new"]
        and report["summary_counts"]["consistent"]
        and any(item.get("file_type") == "excel" and item.get("ok") for item in downloads)
        and any(item.get("file_type") == "json" and item.get("ok") for item in downloads)
        and any(item.get("file_type") in {"image", "contact_sheet"} and item.get("ok") for item in downloads)
        and any(item.get("status") == "completed" or item.get("event") == "completed" for item in events)
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
