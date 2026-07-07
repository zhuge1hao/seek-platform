import json
import logging
import os
import time
from typing import Any

from services import redis_service

try:
    from prometheus_client import Counter
except Exception:  # pragma: no cover
    Counter = None


_MEMORY: dict[str, tuple[float, Any]] = {}
LOGGER = logging.getLogger(__name__)
REDIS_FALLBACKS = Counter("meizhaiseek_cache_redis_fallbacks_total", "Redis cache fallback count", ["operation"]) if Counter else None


def backend() -> str:
    return os.getenv("CACHE_BACKEND", "memory").lower()


def get(key: str, default: Any = None) -> Any:
    if backend() == "redis":
        try:
            value = redis_service.client().get(redis_service.key("cache", key))
            return json.loads(value) if value else default
        except Exception as exc:
            if REDIS_FALLBACKS:
                REDIS_FALLBACKS.labels("get").inc()
            LOGGER.warning("cache_service get fallback: %s", type(exc).__name__)
            return default
    expires_at, value = _MEMORY.get(key, (0, default))
    if expires_at and expires_at < time.time():
        _MEMORY.pop(key, None)
        return default
    return value


def set(key: str, value: Any, ttl_seconds: int = 60) -> None:
    if backend() == "redis":
        try:
            redis_service.client().setex(redis_service.key("cache", key), ttl_seconds, json.dumps(value, ensure_ascii=False))
        except Exception as exc:
            if REDIS_FALLBACKS:
                REDIS_FALLBACKS.labels("set").inc()
            LOGGER.warning("cache_service set fallback: %s", type(exc).__name__)
            _MEMORY[key] = (time.time() + ttl_seconds, value)
        return
    _MEMORY[key] = (time.time() + ttl_seconds, value)


def delete(key: str) -> None:
    if backend() == "redis":
        try:
            redis_service.client().delete(redis_service.key("cache", key))
        except Exception as exc:
            if REDIS_FALLBACKS:
                REDIS_FALLBACKS.labels("delete").inc()
            LOGGER.warning("cache_service delete fallback: %s", type(exc).__name__)
    _MEMORY.pop(key, None)
