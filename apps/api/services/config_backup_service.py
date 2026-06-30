import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def resolve_runtime_path(configured: str, default_base: Path = API_ROOT) -> Path:
    path = Path(configured)
    if path.is_absolute():
        return path
    if len(path.parts) >= 2 and path.parts[0] == "apps" and path.parts[1] == "api":
        return PROJECT_ROOT / path
    return default_base / path


def _backup_dir() -> Path:
    path = resolve_runtime_path(os.getenv("RUNTIME_BACKUP_DIR", "runtime/backups"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _corrupted_dir() -> Path:
    path = resolve_runtime_path(os.getenv("RUNTIME_CORRUPTED_DIR", "runtime/corrupted"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_reason(reason: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in reason.strip()) or "runtime"


def backup_file(path: Path, reason: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    target = _backup_dir() / f"{path.stem}_{_stamp()}_{_safe_reason(reason)}{path.suffix}"
    shutil.copy2(path, target)
    return {"source": str(path), "backup_path": str(target), "reason": reason}


def move_to_corrupted(path: Path, reason: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    target = _corrupted_dir() / f"{path.stem}_{_stamp()}_{_safe_reason(reason)}{path.suffix}"
    shutil.move(str(path), str(target))
    return {"source": str(path), "corrupted_path": str(target), "reason": reason}


def list_backups() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for root in (_backup_dir(), _corrupted_dir()):
        for path in root.glob("*"):
            if path.is_file():
                items.append({"path": str(path), "size": path.stat().st_size, "updated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat()})
    items.sort(key=lambda item: item["updated_at"], reverse=True)
    return items
