import os
import warnings


_WARNED: set[str] = set()


def enabled() -> bool:
    return os.getenv("APP_LEGACY_JSON_FALLBACK", "false").strip().lower() in {"1", "true", "yes", "on"}


def warn_once(source: str) -> None:
    if source in _WARNED:
        return
    _WARNED.add(source)
    warnings.warn(f"legacy JSON fallback enabled for {source}", RuntimeWarning, stacklevel=2)
