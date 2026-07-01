import asyncio
from typing import Any, Callable, TypeVar

from services import audit_log_service, conversation_store, task_store


T = TypeVar("T")


async def async_to_thread(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    return await asyncio.to_thread(fn, *args, **kwargs)


async def async_get_run(run_id: str, user_id: str | None = None, include_legacy: bool = True) -> dict[str, Any] | None:
    return await async_to_thread(task_store.get_run, run_id, user_id, include_legacy)


async def async_summarize_run(run: dict[str, Any] | None) -> dict[str, Any] | None:
    return await async_to_thread(task_store.summarize_run, run)


async def async_get_conversation(conversation_id: str, user_id: str, include_archived: bool = True, touch: bool = False) -> dict[str, Any] | None:
    return await async_to_thread(conversation_store.get_conversation, conversation_id, user_id, include_archived, touch)


async def async_list_conversations(user_id: str, limit: int = 50, include_archived: bool = False) -> list[dict[str, Any]]:
    return await async_to_thread(conversation_store.list_conversations, user_id, limit, include_archived)


async def async_record_audit_log(*args: Any, **kwargs: Any) -> None:
    await async_to_thread(audit_log_service.write_log, *args, **kwargs)
