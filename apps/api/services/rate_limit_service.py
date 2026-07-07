import os
import time
from dataclasses import dataclass

from services import redis_service


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after: int = 0


_WINDOWS: dict[str, tuple[int, float]] = {}


def _limit(name: str, default: int) -> int:
    return max(1, int(os.getenv(name, str(default))))


def check(key: str, limit: int, window_seconds: int) -> RateLimitResult:
    if os.getenv("CACHE_BACKEND", "memory").lower() == "redis" or os.getenv("RATE_LIMIT_BACKEND", "memory").lower() == "redis":
        redis_key = redis_service.key("rate", key)
        redis = redis_service.client()
        count = int(redis.incr(redis_key))
        if count == 1:
            redis.expire(redis_key, window_seconds)
        if count > limit:
            return RateLimitResult(False, max(1, int(redis.ttl(redis_key) or window_seconds)))
        return RateLimitResult(True, 0)
    now = time.time()
    count, expires_at = _WINDOWS.get(key, (0, now + window_seconds))
    if expires_at <= now:
        count, expires_at = 0, now + window_seconds
    count += 1
    _WINDOWS[key] = (count, expires_at)
    return RateLimitResult(count <= limit, max(1, int(expires_at - now)) if count > limit else 0)


def check_login(ip: str, username: str) -> RateLimitResult:
    limit = _limit("LOGIN_RATE_LIMIT_PER_WINDOW", 60)
    window = _limit("LOGIN_RATE_LIMIT_WINDOW_SECONDS", 60)
    if os.getenv("CACHE_BACKEND", "memory").lower() == "redis" or os.getenv("RATE_LIMIT_BACKEND", "memory").lower() == "redis":
        username_key = redis_service.key("rate", f"login:user:{username.lower()}")
        ip_key = redis_service.key("rate", f"login:ip:{ip}")
        redis = redis_service.client()
        pipe = redis.pipeline()
        pipe.incr(ip_key)
        pipe.incr(username_key)
        ip_count, username_count = [int(value) for value in pipe.execute()]
        expire_pipe = redis.pipeline()
        if ip_count == 1:
            expire_pipe.expire(ip_key, window)
        if username_count == 1:
            expire_pipe.expire(username_key, window)
        if len(expire_pipe.command_stack):
            expire_pipe.execute()
        if ip_count > limit * 3:
            return RateLimitResult(False, max(1, int(redis.ttl(ip_key) or window)))
        if username_count > limit:
            return RateLimitResult(False, max(1, int(redis.ttl(username_key) or window)))
        return RateLimitResult(True, 0)
    first = check(f"login:ip:{ip}", limit * 3, window)
    if not first.allowed:
        return first
    return check(f"login:user:{username.lower()}", limit, window)
