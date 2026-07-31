import os
import time
from collections import deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest
except Exception:  # pragma: no cover - dependency can be absent in old dev envs
    Counter = Gauge = Histogram = None
    generate_latest = None


_DB_OBSERVABILITY_LOCK = Lock()
_DB_EXECUTE_COUNT = 0
_DB_COMMIT_COUNT = 0
_DB_COMMIT_FAILURE_COUNT = 0
_DB_EXECUTE_WINDOW: deque[float] = deque(maxlen=1000)
_DB_COMMIT_WINDOW: deque[float] = deque(maxlen=1000)


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
    DB_EXECUTE_SECONDS = Histogram("app_db_execute_seconds", "Database execute latency", ["backend", "operation"], buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5))
    DB_COMMIT_SECONDS = Histogram("app_db_commit_seconds", "Database commit latency", ["backend"], buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5))
    DB_ROLLBACK_SECONDS = Histogram("app_db_rollback_seconds", "Database rollback latency", ["backend"], buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5))
    DB_COMMITS = Counter("app_db_commit_total", "Database commits", ["backend"])
    DB_ROLLBACKS = Counter("app_db_rollback_total", "Database rollbacks", ["backend"])
    DB_COMMIT_FAILURES = Counter("app_db_commit_failure_total", "Database commit failures", ["backend"])
    AGENT_SUBMIT_STAGE_SECONDS = Histogram("app_agent_submit_stage_seconds", "Agent submit stage latency", ["stage"], buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5))
    AGENT_SUBMIT_TRANSACTIONS = Histogram("app_agent_submit_transactions", "Transactions per agent submit", buckets=(1, 2, 3, 4, 5, 8, 13, 21))
    AGENT_SUBMIT_COMMITS = Histogram("app_agent_submit_commits", "Commits per agent submit", buckets=(1, 2, 3, 4, 5, 8, 13, 21))
    AGENT_SUBMIT_FAILURES = Counter("app_agent_submit_failures_total", "Agent submit failures")
else:
    HTTP_REQUESTS = HTTP_LATENCY = None
    DB_POOL_ACQUIRE_SECONDS = DB_POOL_IN_USE = DB_POOL_IDLE = DB_POOL_OVERFLOW = DB_POOL_WAITERS = None
    DB_POOL_TIMEOUTS = DB_POOL_DISCARDED = DB_POOL_RECONNECTS = None
    DB_EXECUTE_SECONDS = DB_COMMIT_SECONDS = DB_ROLLBACK_SECONDS = None
    DB_COMMITS = DB_ROLLBACKS = DB_COMMIT_FAILURES = None
    AGENT_SUBMIT_STAGE_SECONDS = AGENT_SUBMIT_TRANSACTIONS = AGENT_SUBMIT_COMMITS = AGENT_SUBMIT_FAILURES = None


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        trace_token = None
        trace_module = None
        is_agent_submit = request.method == "POST" and request.url.path.endswith("/api/agent-runs")
        if is_agent_submit:
            from services import app_sqlite
            trace_module = app_sqlite
            trace_token = app_sqlite.start_transaction_trace()
        try:
            response = await call_next(request)
        finally:
            if trace_module is not None and trace_token is not None:
                counts = trace_module.transaction_trace_snapshot()
                observe_agent_submit_counts(counts.get("transactions", 0), counts.get("commits", 0))
                trace_module.stop_transaction_trace(trace_token)
        if is_agent_submit and os.getenv("APP_DB_TRANSACTION_TRACE", "false").lower() in {"1", "true", "yes", "on"}:
            response.headers["X-App-DB-Transactions"] = str(counts.get("transactions", 0))
            response.headers["X-App-DB-Acquires"] = str(counts.get("acquires", 0))
            response.headers["X-App-DB-Executes"] = str(counts.get("executes", 0))
            response.headers["X-App-DB-Commits"] = str(counts.get("commits", 0))
            response.headers["X-App-DB-Rollbacks"] = str(counts.get("rollbacks", 0))
        if is_agent_submit and response.status_code >= 400:
            inc_agent_submit_failure()
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


def observe_db_execute(backend: str, operation: str, seconds: float) -> None:
    global _DB_EXECUTE_COUNT
    if DB_EXECUTE_SECONDS:
        DB_EXECUTE_SECONDS.labels(backend, operation).observe(max(0.0, seconds))
    with _DB_OBSERVABILITY_LOCK:
        _DB_EXECUTE_COUNT += 1
        _DB_EXECUTE_WINDOW.append(max(0.0, seconds))


def observe_db_commit(backend: str, seconds: float, failed: bool = False) -> None:
    global _DB_COMMIT_COUNT, _DB_COMMIT_FAILURE_COUNT
    if DB_COMMIT_SECONDS:
        DB_COMMIT_SECONDS.labels(backend).observe(max(0.0, seconds))
    if failed:
        if DB_COMMIT_FAILURES:
            DB_COMMIT_FAILURES.labels(backend).inc()
    elif DB_COMMITS:
        DB_COMMITS.labels(backend).inc()
    with _DB_OBSERVABILITY_LOCK:
        _DB_COMMIT_COUNT += 0 if failed else 1
        _DB_COMMIT_FAILURE_COUNT += 1 if failed else 0
        _DB_COMMIT_WINDOW.append(max(0.0, seconds))


def observe_db_rollback(backend: str, seconds: float) -> None:
    if DB_ROLLBACK_SECONDS:
        DB_ROLLBACK_SECONDS.labels(backend).observe(max(0.0, seconds))
    if DB_ROLLBACKS:
        DB_ROLLBACKS.labels(backend).inc()


def observe_agent_submit_stage(stage: str, seconds: float) -> None:
    if AGENT_SUBMIT_STAGE_SECONDS:
        AGENT_SUBMIT_STAGE_SECONDS.labels(stage).observe(max(0.0, seconds))


def observe_agent_submit_counts(transactions: int, commits: int) -> None:
    if AGENT_SUBMIT_TRANSACTIONS:
        AGENT_SUBMIT_TRANSACTIONS.observe(max(0, transactions))
    if AGENT_SUBMIT_COMMITS:
        AGENT_SUBMIT_COMMITS.observe(max(0, commits))


def inc_agent_submit_failure() -> None:
    if AGENT_SUBMIT_FAILURES:
        AGENT_SUBMIT_FAILURES.inc()


def db_observability_summary() -> dict[str, dict[str, int | float | None]]:
    with _DB_OBSERVABILITY_LOCK:
        execute = list(_DB_EXECUTE_WINDOW)
        commit = list(_DB_COMMIT_WINDOW)
        execute_count = _DB_EXECUTE_COUNT
        commit_count = _DB_COMMIT_COUNT
        failure_count = _DB_COMMIT_FAILURE_COUNT

    def p95_ms(values: list[float]) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        return round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))] * 1000, 3)

    return {
        "execute": {"count": execute_count, "last_p95_ms": p95_ms(execute), "last_window_samples": len(execute)},
        "commit": {"count": commit_count, "failure_count": failure_count, "last_p95_ms": p95_ms(commit), "last_window_samples": len(commit)},
    }
