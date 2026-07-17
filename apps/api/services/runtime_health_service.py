import os
from typing import Any

from services import agent_run_event_bus, app_sqlite, redis_service, security_config_service
from tasks import queue as task_queue


VERSION = "v1.8.6"
MODEL = "meizhaiseek 2.0"
VALIDATION_VALUES = {"not_run", "failed", "passed"}


def _validation_status(env_name: str) -> str:
    value = os.getenv(env_name, "not_run").lower()
    return value if value in VALIDATION_VALUES else "failed"


def database_health() -> dict[str, Any]:
    backend = os.getenv("APP_DB_BACKEND", "sqlite").lower()
    if backend == "postgres":
        result = app_sqlite.health_check()
        return {"backend": "postgres", "status": result.get("status", "failed"), "pool_size": int(os.getenv("APP_DB_POOL_SIZE", "20")), "tables": result.get("tables", {})}
    result = app_sqlite.health_check()
    return {"backend": "sqlite", "status": result.get("status", "failed"), "sqlite_exists": result.get("sqlite_exists")}


def artifact_health() -> dict[str, Any]:
    return {"backend": os.getenv("ARTIFACT_STORAGE_BACKEND", "local"), "status": "ok"}


def rag_health() -> dict[str, Any]:
    try:
        from rag.factory import provider
        return provider().health_check()
    except Exception as exc:
        return {"backend": os.getenv("RAG_BACKEND", "sqlite"), "status": "failed", "error": str(exc)}


def component_health() -> dict[str, Any]:
    redis = redis_service.health_check()
    queue = task_queue.health_check()
    events = agent_run_event_bus.health_check()
    return {
        "database": database_health(),
        "redis": redis,
        "queue": queue,
        "events": {**events, "transport": "sse", "polling_fallback": True},
        "artifact_storage": artifact_health(),
        "rag": rag_health(),
        "security": security_config_service.health_status(),
        "capacity_profile": "500-users" if os.getenv("APP_DB_BACKEND", "sqlite").lower() == "postgres" else "local-dev",
    }


def readiness() -> dict[str, Any]:
    components = component_health()
    required = [components["database"]]
    if os.getenv("APP_DB_BACKEND", "sqlite").lower() == "postgres":
        required.append(components["redis"])
        required.append(components["queue"])
    if components["security"].get("token_secret_status") == "invalid":
        required.append({"status": "failed"})
    if security_config_service.production_mode() and components["security"].get("default_admin_password_detected"):
        required.append({"status": "failed"})
    failed = [item for item in required if item.get("status") not in {"ok", "configured", "disabled"}]
    return {"status": "ok" if not failed else "degraded", **components}


def runtime_health(warnings: list[str] | None = None) -> dict[str, Any]:
    components = component_health()
    return {
        "status": "ok" if not warnings else "warning",
        "version": VERSION,
        "model": MODEL,
        "service": "meizhaiseek-api",
        **components,
        "validation": {
            "multi_instance_sse_verified": _validation_status("MULTI_INSTANCE_SSE_VERIFIED"),
            "redis_recovery_verified": _validation_status("REDIS_RECOVERY_VERIFIED"),
            "worker_recovery_verified": _validation_status("WORKER_RECOVERY_VERIFIED"),
            "video_queue_50_verified": _validation_status("VIDEO_QUEUE_50_VERIFIED"),
            "dataset_queue_verified": _validation_status("DATASET_QUEUE_VERIFIED"),
            "knowledge_queue_verified": _validation_status("KNOWLEDGE_QUEUE_VERIFIED"),
            "blueprint_queue_verified": _validation_status("BLUEPRINT_QUEUE_VERIFIED"),
            "artifact_s3_verified": _validation_status("ARTIFACT_S3_VERIFIED"),
            "pgvector_migration_verified": _validation_status("PGVECTOR_MIGRATION_VERIFIED"),
            "browser_agent_smoke_verified": _validation_status("BROWSER_AGENT_SMOKE_VERIFIED"),
            "capacity_last_verified_users": int(os.getenv("CAPACITY_LAST_VERIFIED_USERS", "0")),
            "capacity_last_test_passed": _validation_status("CAPACITY_LAST_TEST_PASSED"),
        },
        "warnings": warnings or [],
    }
