import os
from urllib.parse import urlsplit, urlunsplit
from typing import Any


KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "meizhaiseek:")
_CLIENTS: dict[tuple[str, bool], Any] = {}


def backend_enabled() -> bool:
    return os.getenv("REDIS_URL", "").strip() != ""


def redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _timeout_seconds(name: str, default: str) -> float:
    try:
        return max(0.1, float(os.getenv(name, default)))
    except ValueError:
        return float(default)


def _make_client(decode_responses: bool) -> Any:
    try:
        import redis
    except Exception as exc:  # pragma: no cover - dependency is optional in sqlite dev mode
        raise RuntimeError("redis package is not installed") from exc
    return redis.Redis.from_url(
        redis_url(),
        decode_responses=decode_responses,
        socket_connect_timeout=_timeout_seconds("REDIS_CONNECT_TIMEOUT_SECONDS", "1"),
        socket_timeout=_timeout_seconds("REDIS_SOCKET_TIMEOUT_SECONDS", "2"),
        health_check_interval=30,
    )


def _cached_client(decode_responses: bool) -> Any:
    cache_key = (redis_url(), decode_responses)
    cached = _CLIENTS.get(cache_key)
    if cached is None:
        cached = _make_client(decode_responses)
        _CLIENTS[cache_key] = cached
    return cached


def client() -> Any:
    return _cached_client(True)


def binary_client() -> Any:
    return _cached_client(False)


def reset_clients_for_test() -> None:
    _CLIENTS.clear()


def key(*parts: str) -> str:
    return KEY_PREFIX + ":".join(str(part).strip(":") for part in parts if part)


def _redact(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value
    if parsed.password is None:
        return value
    username = parsed.username or ""
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{username}:***@{host}{port}" if username else f"***@{host}{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def health_check() -> dict[str, Any]:
    if not backend_enabled():
        return {"status": "disabled", "backend": "memory"}
    try:
        value = client().ping()
        return {"status": "ok" if value else "failed", "backend": "redis"}
    except Exception as exc:
        return {"status": "failed", "backend": "redis", "error": _redact(str(exc))}
