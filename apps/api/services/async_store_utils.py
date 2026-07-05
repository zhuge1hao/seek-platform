import asyncio
import os
from typing import Any, Callable, TypeVar

from services import agent_blueprint_store, audit_log_service, conversation_store, dataset_store, qa_conversation_store, task_store


T = TypeVar("T")
_MAX_CONCURRENCY = max(1, int(os.getenv("APP_ASYNC_STORE_MAX_CONCURRENCY", "8")))
_SEMAPHORE = asyncio.Semaphore(_MAX_CONCURRENCY)


def max_concurrency() -> int:
    return _MAX_CONCURRENCY


async def async_to_thread(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    async with _SEMAPHORE:
        return await asyncio.to_thread(fn, *args, **kwargs)


async def async_get_run(run_id: str, user_id: str | None = None, include_legacy: bool = True) -> dict[str, Any] | None:
    return await async_to_thread(task_store.get_run, run_id, user_id, include_legacy)


async def async_get_run_summary(run_id: str, user_id: str | None = None, include_legacy: bool = True) -> dict[str, Any] | None:
    return await async_to_thread(lambda: task_store.summarize_run(task_store.get_run(run_id, user_id, include_legacy)))


async def async_get_run_result(run_id: str, user_id: str | None = None, include_legacy: bool = True) -> dict[str, Any] | None:
    return await async_get_run(run_id, user_id, include_legacy)


async def async_summarize_run(run: dict[str, Any] | None) -> dict[str, Any] | None:
    return await async_to_thread(task_store.summarize_run, run)


async def async_get_conversation(conversation_id: str, user_id: str, include_archived: bool = True, touch: bool = False) -> dict[str, Any] | None:
    return await async_to_thread(conversation_store.get_conversation, conversation_id, user_id, include_archived, touch)


async def async_list_conversations(user_id: str, limit: int = 50, include_archived: bool = False) -> list[dict[str, Any]]:
    return await async_to_thread(conversation_store.list_conversations, user_id, limit, include_archived)


async def async_list_agent_blueprints(include_internal: bool = False) -> list[dict[str, Any]]:
    return await async_to_thread(agent_blueprint_store.list_blueprints, include_internal)


async def async_get_agent_blueprint(blueprint_id: str) -> dict[str, Any] | None:
    return await async_to_thread(agent_blueprint_store.get_blueprint, blueprint_id)


async def async_list_blueprint_versions(blueprint_id: str, include_prompt: bool = True) -> list[dict[str, Any]]:
    return await async_to_thread(agent_blueprint_store.list_versions, blueprint_id, include_prompt)


async def async_list_test_runs(blueprint_id: str, limit: int = 20) -> list[dict[str, Any]]:
    return await async_to_thread(agent_blueprint_store.list_test_runs, blueprint_id, limit)


async def async_list_validation_results(blueprint_id: str, limit: int = 20) -> list[dict[str, Any]]:
    return await async_to_thread(agent_blueprint_store.list_validation_results, blueprint_id, limit)


async def async_list_audit_logs(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    return await async_to_thread(audit_log_service.list_logs, *args, **kwargs)


async def async_list_qa_conversations(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    return await async_to_thread(qa_conversation_store.list_conversations, user_id, limit)


async def async_get_qa_conversation(user_id: str, conversation_id: str, touch: bool = False) -> dict[str, Any] | None:
    return await async_to_thread(qa_conversation_store.get_conversation, user_id, conversation_id, touch)


async def async_list_datasets(user_id: str, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    return await async_to_thread(dataset_store.list_datasets, user_id, status, limit)


async def async_get_dataset(dataset_id: str, user_id: str | None = None, include_all_users: bool = False) -> dict[str, Any] | None:
    return await async_to_thread(dataset_store.get_dataset, dataset_id, user_id, include_all_users)


async def async_record_audit_log(*args: Any, **kwargs: Any) -> None:
    await async_to_thread(audit_log_service.write_log, *args, **kwargs)
