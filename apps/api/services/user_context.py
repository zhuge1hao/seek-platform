import os
import re
from pathlib import Path
from typing import Any


API_ROOT = Path(__file__).resolve().parents[1]


def safe_user_id(user_id: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]", "_", user_id.strip())
    if not value or value in {".", ".."}:
        raise ValueError("user_id 无效。")
    return value


def runtime_user_root(user_id: str) -> Path:
    path = API_ROOT / "runtime" / "users" / safe_user_id(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def agent_runs_dir(user_id: str) -> Path:
    path = runtime_user_root(user_id) / "agent_runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def conversations_dir(user_id: str) -> Path:
    path = runtime_user_root(user_id) / "conversations"
    path.mkdir(parents=True, exist_ok=True)
    return path


def files_dir(user_id: str) -> Path:
    path = runtime_user_root(user_id) / "files"
    path.mkdir(parents=True, exist_ok=True)
    return path


def datasets_dir(user_id: str) -> Path:
    path = runtime_user_root(user_id) / "datasets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifacts_dir(user_id: str, run_id: str | None = None) -> Path:
    configured = os.getenv("LOCAL_AGENT_OUTPUT_DIR", "").strip()
    root = Path(configured) / "users" / safe_user_id(user_id) if configured else runtime_user_root(user_id) / "artifacts"
    path = root / run_id if run_id else root
    path.mkdir(parents=True, exist_ok=True)
    return path


def debug_payload_dir(user_id: str, run_id: str | None = None) -> Path:
    root = runtime_user_root(user_id) / "debug_payloads"
    path = root / run_id if run_id else root
    path.mkdir(parents=True, exist_ok=True)
    return path


def uploads_dir(user_id: str) -> Path:
    path = API_ROOT / "uploads" / "users" / safe_user_id(user_id) / "files"
    path.mkdir(parents=True, exist_ok=True)
    return path


def can_access_owner(current_user: dict[str, Any], owner_user_id: str | None) -> bool:
    if current_user.get("role") == "admin":
        return True
    return bool(owner_user_id and owner_user_id == current_user.get("user_id"))
