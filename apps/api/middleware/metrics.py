import os
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

try:
    from prometheus_client import Counter, Histogram, generate_latest
except Exception:  # pragma: no cover - dependency can be absent in old dev envs
    Counter = Histogram = None
    generate_latest = None


if Counter and Histogram:
    HTTP_REQUESTS = Counter("meizhaiseek_http_requests_total", "HTTP requests", ["method", "path", "status"])
    HTTP_LATENCY = Histogram("meizhaiseek_http_request_duration_seconds", "HTTP request latency", ["method", "path"])
else:
    HTTP_REQUESTS = HTTP_LATENCY = None


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
