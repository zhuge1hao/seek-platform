import os
import warnings
from datetime import datetime, timezone


_WARNED: set[str] = set()
_USAGE_COUNT = 0
_LAST_USED_AT: str | None = None


def enabled() -> bool:
    return os.getenv("APP_LEGACY_JSON_FALLBACK", "false").strip().lower() in {"1", "true", "yes", "on"}


def warn_once(source: str) -> None:
    global _LAST_USED_AT, _USAGE_COUNT
    _USAGE_COUNT += 1
    _LAST_USED_AT = datetime.now(timezone.utc).isoformat()
    if source in _WARNED:
        return
    _WARNED.add(source)
    warnings.warn(f"legacy JSON fallback enabled for {source}", RuntimeWarning, stacklevel=2)


def usage_stats() -> dict[str, object]:
    return {"usage_count": _USAGE_COUNT, "last_used_at": _LAST_USED_AT}


def reset_usage_for_test() -> None:
    global _LAST_USED_AT, _USAGE_COUNT
    _WARNED.clear()
    _USAGE_COUNT = 0
    _LAST_USED_AT = None
