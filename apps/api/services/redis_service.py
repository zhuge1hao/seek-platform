import os
from typing import Any


KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "meizhaiseek:")


def backend_enabled() -> bool:
    return os.getenv("REDIS_URL", "").strip() != ""


def redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _timeout_seconds(name: str, default: str) -> float:
    try:
        return max(0.1, float(os.getenv(name, default)))
    except ValueError:
        return float(default)


def client() -> Any:
    try:
        import redis
    except Exception as exc:  # pragma: no cover - dependency is optional in sqlite dev mode
        raise RuntimeError("redis package is not installed") from exc
    return redis.Redis.from_url(
        redis_url(),
        decode_responses=True,
        socket_connect_timeout=_timeout_seconds("REDIS_CONNECT_TIMEOUT_SECONDS", "1"),
        socket_timeout=_timeout_seconds("REDIS_SOCKET_TIMEOUT_SECONDS", "2"),
        health_check_interval=30,
    )


def binary_client() -> Any:
    try:
        import redis
    except Exception as exc:  # pragma: no cover - dependency is optional in sqlite dev mode
        raise RuntimeError("redis package is not installed") from exc
    return redis.Redis.from_url(
        redis_url(),
        decode_responses=False,
        socket_connect_timeout=_timeout_seconds("REDIS_CONNECT_TIMEOUT_SECONDS", "1"),
        socket_timeout=_timeout_seconds("REDIS_SOCKET_TIMEOUT_SECONDS", "2"),
        health_check_interval=30,
    )


def key(*parts: str) -> str:
    return KEY_PREFIX + ":".join(str(part).strip(":") for part in parts if part)


def health_check() -> dict[str, Any]:
    if not backend_enabled():
        return {"status": "disabled", "backend": "memory"}
    try:
        value = client().ping()
        return {"status": "ok" if value else "failed", "backend": "redis"}
    except Exception as exc:
        return {"status": "failed", "backend": "redis", "error": str(exc)}
