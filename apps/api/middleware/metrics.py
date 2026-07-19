import os
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest
except Exception:  # pragma: no cover - dependency can be absent in old dev envs
    Counter = Gauge = Histogram = None
    generate_latest = None


if Counter and Gauge and Histogram:
    HTTP_REQUESTS = Counter("meizhaiseek_http_requests_total", "HTTP requests", ["method", "path", "status"])
    HTTP_LATENCY = Histogram("meizhaiseek_http_request_duration_seconds", "HTTP request latency", ["method", "path"])
    DB_POOL_ACQUIRE_SECONDS = Histogram("app_db_pool_acquire_seconds", "PostgreSQL pool acquire wait seconds", buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5))
    DB_POOL_IN_USE = Gauge("app_db_pool_in_use", "PostgreSQL pool connections checked out")
    DB_POOL_IDLE = Gauge("app_db_pool_idle", "PostgreSQL pool idle connections")
    DB_POOL_OVERFLOW = Gauge("app_db_pool_overflow", "PostgreSQL pool overflow connections")
    DB_POOL_WAITERS = Gauge("app_db_pool_waiters", "PostgreSQL pool waiting acquire calls")
    DB_POOL_TIMEOUTS = Counter("app_db_pool_timeout_total", "PostgreSQL pool acquire timeouts")
    DB_POOL_DISCARDED = Counter("app_db_pool_discarded_total", "PostgreSQL pool discarded connections")
    DB_POOL_RECONNECTS = Counter("app_db_pool_reconnect_total", "PostgreSQL pool new connection attempts")
else:
    HTTP_REQUESTS = HTTP_LATENCY = None
    DB_POOL_ACQUIRE_SECONDS = DB_POOL_IN_USE = DB_POOL_IDLE = DB_POOL_OVERFLOW = DB_POOL_WAITERS = None
    DB_POOL_TIMEOUTS = DB_POOL_DISCARDED = DB_POOL_RECONNECTS = None


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        if HTTP_REQUESTS and HTTP_LATENCY:
            path = request.scope.get("route").path if request.scope.get("route") else request.url.path
            HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
            HTTP_LATENCY.labels(request.method, path).observe(time.perf_counter() - started)
        return response


def metrics_enabled() -> bool:
    return os.getenv("METRICS_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


def render_metrics() -> bytes:
    if not metrics_enabled() or generate_latest is None:
        return b""
    return generate_latest()


def observe_db_pool_acquire(seconds: float) -> None:
    if DB_POOL_ACQUIRE_SECONDS:
        DB_POOL_ACQUIRE_SECONDS.observe(max(0.0, seconds))


def inc_db_pool_timeout() -> None:
    if DB_POOL_TIMEOUTS:
        DB_POOL_TIMEOUTS.inc()


def inc_db_pool_discarded() -> None:
    if DB_POOL_DISCARDED:
        DB_POOL_DISCARDED.inc()


def inc_db_pool_reconnect() -> None:
    if DB_POOL_RECONNECTS:
        DB_POOL_RECONNECTS.inc()


def set_db_pool_gauges(stats: dict[str, int]) -> None:
    if DB_POOL_IN_USE:
        DB_POOL_IN_USE.set(stats.get("in_use", 0))
    if DB_POOL_IDLE:
        DB_POOL_IDLE.set(stats.get("idle", 0))
    if DB_POOL_OVERFLOW:
        DB_POOL_OVERFLOW.set(stats.get("overflow", 0))
    if DB_POOL_WAITERS:
        DB_POOL_WAITERS.set(stats.get("waiters", 0))
