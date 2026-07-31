import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services import app_sqlite, legacy_json_fallback
from services.agent_config_store import get_config
from services.agent_registry import get_agent_by_type
from services.user_context import conversations_dir


SCHEMA_VERSION = "1.0"
LOGGER = logging.getLogger(__name__)


class ConversationError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _store_path(user_id: str) -> Path:
    return conversations_dir(user_id) / "conversations.json"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _safe_conversation_id(conversation_id: str) -> bool:
    return conversation_id.startswith("conv_") and not any(token in conversation_id for token in ("/", "\\", ".."))


def _agent_name(agent_type: str) -> str:
    config = get_config(agent_type) or {}
    agent = get_agent_by_type(agent_type) or {}
    return str(config.get("name") or agent.get("name") or agent_type or "智能体")


def _title(agent_name: str, prompt: str, fallback: str = "新对话") -> str:
    compact = " ".join(prompt.split())
    return f"{agent_name}：{compact[:20]}" if compact else fallback


def _normalize_message(message: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    return {
        "message_id": str(message.get("message_id") or _new_id("msg")),
        "role": str(message.get("role") or "assistant"),
        "content": str(message.get("content") or ""),
        "run_id": message.get("run_id"),
        "status": str(message.get("status") or "completed"),
        "result": message.get("result"),
        "error": message.get("error"),
        "progress": message.get("progress"),
        "current_step": message.get("current_step"),
        "logs": list(message.get("logs") or []),
        "created_at": str(message.get("created_at") or now),
        "updated_at": str(message.get("updated_at") or message.get("created_at") or now),
    }


def _normalize_conversation(value: dict[str, Any], user_id: str) -> dict[str, Any] | None:
    conversation_id = str(value.get("conversation_id") or "")
    if not _safe_conversation_id(conversation_id):
        return None
    agent_type = str(value.get("agent_type") or "")
    agent_name = str(value.get("agent_name") or _agent_name(agent_type))
    prompt = str(value.get("prompt") or "")
    messages = [_normalize_message(item) for item in value.get("messages", []) if isinstance(item, dict)]
    if not prompt:
        first_user = next((item for item in messages if item.get("role") == "user"), None)
        prompt = str((first_user or {}).get("content") or "")
    latest_run_id = value.get("latest_run_id") or value.get("last_run_id")
    run_ids = [str(item) for item in value.get("run_ids", []) if item]
    if latest_run_id and latest_run_id not in run_ids:
        run_ids.append(str(latest_run_id))
    last_assistant = next((item for item in reversed(messages) if item.get("role") == "assistant"), {})
    now = _now()
    return {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "title": str(value.get("title") or _title(agent_name, prompt)),
        "agent_type": agent_type,
        "agent_name": agent_name,
        "prompt": prompt,
        "latest_run_id": latest_run_id,
        "run_ids": run_ids,
        "status": str(value.get("status") or last_assistant.get("status") or "completed"),
        "summary": str(value.get("summary") or ""),
        "messages": messages,
        "created_at": str(value.get("created_at") or now),
        "updated_at": str(value.get("updated_at") or now),
        "last_opened_at": str(value.get("last_opened_at") or value.get("updated_at") or now),
        "is_archived": bool(value.get("is_archived", False)),
    }


def _legacy_load(user_id: str) -> list[dict[str, Any]]:
    path = _store_path(user_id)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        source = raw.get("conversations") if isinstance(raw, dict) else []
        if not isinstance(source, list):
            return []
        return [item for value in source if isinstance(value, dict) if (item := _normalize_conversation(value, user_id))]
    except Exception as exc:
        LOGGER.warning("conversation_store legacy load failed: %s", type(exc).__name__)
        return []


def _row_message(row: Any) -> dict[str, Any]:
    metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
    return {
        **metadata,
        "message_id": row["message_id"],
        "role": row["role"],
        "content": row["content"] or "",
        "run_id": row["run_id"],
        "status": row["status"] or "completed",
        "created_at": row["created_at"] or _now(),
        "updated_at": row["updated_at"] or row["created_at"] or _now(),
    }


def _row_conversation(row: Any, messages: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
    return {
        **metadata,
        "conversation_id": row["conversation_id"],
        "user_id": row["user_id"],
        "title": row["title"] or "新对话",
        "agent_type": row["agent_type"] or "",
        "agent_name": metadata.get("agent_name") or _agent_name(row["agent_type"] or ""),
        "latest_run_id": row["latest_run_id"],
        "status": row["status"] or "completed",
        "messages": messages or [],
        "created_at": row["created_at"] or _now(),
        "updated_at": row["updated_at"] or _now(),
        "last_opened_at": row["last_opened_at"] or row["updated_at"] or _now(),
        "is_archived": bool(row["is_archived"]),
    }


def _upsert_agent_conversation(conn: Any, user_id: str, conversation: dict[str, Any]) -> None:
    metadata = {key: value for key, value in conversation.items() if key not in {"messages"}}
    conn.execute(
        """
        INSERT INTO agent_conversations(conversation_id, user_id, title, type, selected_agent_id, agent_type, latest_run_id, status, is_archived, created_at, updated_at, last_opened_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(conversation_id) DO UPDATE SET user_id=excluded.user_id, title=excluded.title, type=excluded.type,
          selected_agent_id=excluded.selected_agent_id, agent_type=excluded.agent_type, latest_run_id=excluded.latest_run_id,
          status=excluded.status, is_archived=excluded.is_archived, updated_at=excluded.updated_at,
          last_opened_at=excluded.last_opened_at, metadata_json=excluded.metadata_json
        """,
        (
            conversation["conversation_id"], user_id, conversation.get("title"), "agent",
            conversation.get("selected_agent_id"), conversation.get("agent_type"), conversation.get("latest_run_id"),
            conversation.get("status"), 1 if conversation.get("is_archived") else 0, conversation.get("created_at"),
            conversation.get("updated_at"), conversation.get("last_opened_at"), app_sqlite.json_dump(metadata),
        ),
    )


def upsert_agent_conversation(user_id: str, conversation: dict[str, Any]) -> None:
    with app_sqlite.connection() as conn:
        _upsert_agent_conversation(conn, user_id, conversation)


def _insert_agent_message(conn: Any, user_id: str, conversation_id: str, message: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO agent_messages(message_id, conversation_id, user_id, role, content, status, run_id, created_at, updated_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(message_id) DO UPDATE SET content=excluded.content, status=excluded.status, run_id=excluded.run_id,
          updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
        """,
        (
            message["message_id"], conversation_id, user_id, message.get("role"), message.get("content"),
            message.get("status"), message.get("run_id"), message.get("created_at"),
            message.get("updated_at") or message.get("created_at"), app_sqlite.json_dump(message),
        ),
    )


def append_agent_message(user_id: str, conversation_id: str, message: dict[str, Any]) -> dict[str, Any]:
    with app_sqlite.connection() as conn:
        _insert_agent_message(conn, user_id, conversation_id, message)
    return json.loads(json.dumps(message, ensure_ascii=False))


def update_agent_message(user_id: str, conversation_id: str, message_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute(
            "SELECT * FROM agent_messages WHERE message_id=? AND conversation_id=? AND user_id=?",
            (message_id, conversation_id, user_id),
        ).fetchone()
        if row is None:
            return None
        message = _row_message(row)
        message.update({key: value for key, value in patch.items() if value is not None})
        message["updated_at"] = patch.get("updated_at") or _now()
        _insert_agent_message(conn, user_id, conversation_id, message)
    return json.loads(json.dumps(message, ensure_ascii=False))


def replace_user_agent_conversations_for_migration(user_id: str, items: list[dict[str, Any]]) -> None:
    # ponytail: bulk replace is only for legacy JSON migration/fallback, never normal API writes.
    with app_sqlite.connection() as conn:
        conn.execute("DELETE FROM agent_messages WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM agent_conversations WHERE user_id=?", (user_id,))
        for conversation in items:
            _upsert_agent_conversation(conn, user_id, conversation)
            for message in conversation.get("messages") or []:
                _insert_agent_message(conn, user_id, conversation["conversation_id"], message)


def _ensure_legacy_loaded(user_id: str) -> None:
    if not legacy_json_fallback.enabled():
        return
    legacy_json_fallback.warn_once("agent_conversations")
    with app_sqlite.connection() as conn:
        exists = conn.execute("SELECT 1 FROM agent_conversations WHERE user_id=? LIMIT 1", (user_id,)).fetchone()
    if not exists:
        migrated = _legacy_load(user_id)
        if migrated:
            replace_user_agent_conversations_for_migration(user_id, migrated)


def create_conversation(user_id: str, agent_type: str, prompt: str = "", title: str = "") -> dict[str, Any]:
    now = _now()
    agent_name = _agent_name(agent_type)
    conversation: dict[str, Any] = {
        "conversation_id": _new_id("conv"), "user_id": user_id, "title": title.strip() or _title(agent_name, prompt),
        "agent_type": agent_type, "agent_name": agent_name, "prompt": prompt, "latest_run_id": None, "run_ids": [],
        "status": "running", "summary": "", "messages": [], "created_at": now, "updated_at": now,
        "last_opened_at": now, "is_archived": False,
    }
    upsert_agent_conversation(user_id, conversation)
    return json.loads(json.dumps(conversation, ensure_ascii=False))


def get_conversation(conversation_id: str, user_id: str, include_archived: bool = True, touch: bool = False) -> dict[str, Any] | None:
    if not _safe_conversation_id(conversation_id):
        return None
    _ensure_legacy_loaded(user_id)
    with app_sqlite.connection() as conn:
        row = conn.execute(
            "SELECT * FROM agent_conversations WHERE conversation_id=? AND user_id=?",
            (conversation_id, user_id),
        ).fetchone()
        if row is None or (bool(row["is_archived"]) and not include_archived):
            return None
        messages = [
            _row_message(item)
            for item in conn.execute(
                "SELECT * FROM agent_messages WHERE conversation_id=? AND user_id=? ORDER BY created_at",
                (conversation_id, user_id),
            ).fetchall()
        ]
    conversation = _row_conversation(row, messages)
    if touch:
        conversation["last_opened_at"] = _now()
        upsert_agent_conversation(user_id, conversation)
    return json.loads(json.dumps(conversation, ensure_ascii=False))


def list_conversations(user_id: str, limit: int = 50, include_archived: bool = False) -> list[dict[str, Any]]:
    _ensure_legacy_loaded(user_id)
    safe_limit = max(1, min(limit, 200))
    with app_sqlite.connection() as conn:
        if include_archived:
            rows = conn.execute(
                "SELECT * FROM agent_conversations WHERE user_id=? ORDER BY updated_at DESC LIMIT ?",
                (user_id, safe_limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM agent_conversations WHERE user_id=? AND is_archived=0 ORDER BY updated_at DESC LIMIT ?",
                (user_id, safe_limit),
            ).fetchall()
    fields = ("conversation_id", "title", "agent_type", "agent_name", "latest_run_id", "status", "summary", "created_at", "updated_at", "is_archived")
    return [{key: _row_conversation(row).get(key) for key in fields} for row in rows]


def rename_conversation(conversation_id: str, user_id: str, title: str) -> dict[str, Any] | None:
    conversation = get_conversation(conversation_id, user_id)
    if conversation is None:
        return None
    conversation.update({"title": title.strip(), "updated_at": _now()})
    upsert_agent_conversation(user_id, conversation)
    return json.loads(json.dumps(conversation, ensure_ascii=False))


def archive_conversation(conversation_id: str, user_id: str) -> dict[str, Any] | None:
    conversation = get_conversation(conversation_id, user_id)
    if conversation is None:
        return None
    conversation.update({"is_archived": True, "updated_at": _now()})
    upsert_agent_conversation(user_id, conversation)
    return json.loads(json.dumps(conversation, ensure_ascii=False))


def attach_run_atomic(
    connection: Any,
    run: dict[str, Any],
    include_user_message: bool = True,
    user_message_id: str | None = None,
    assistant_message_id: str | None = None,
) -> tuple[dict[str, Any], bool]:
    user_id = str(run["user_id"])
    conversation_id = str(run.get("conversation_id") or "")
    row = connection.execute(
        "SELECT * FROM agent_conversations WHERE conversation_id=? AND user_id=?",
        (conversation_id, user_id),
    ).fetchone() if conversation_id else None
    conversation = _row_conversation(row) if row else None
    created = conversation is None
    if conversation is None:
        now = _now()
        agent_type = str(run.get("agent_type") or "")
        prompt = str(run.get("prompt") or "")
        agent_name = _agent_name(agent_type)
        conversation = {
            "conversation_id": conversation_id or _new_id("conv"), "user_id": user_id,
            "title": _title(agent_name, prompt), "agent_type": agent_type, "agent_name": agent_name,
            "prompt": prompt, "latest_run_id": None, "run_ids": [], "status": "running",
            "summary": "", "messages": [], "created_at": now, "updated_at": now,
            "last_opened_at": now, "is_archived": False,
        }
    now = _now()
    prompt = str(run.get("prompt") or "")
    if include_user_message:
        _insert_agent_message(connection, user_id, conversation["conversation_id"], {
            "message_id": user_message_id or _new_id("msg"), "role": "user", "content": prompt, "run_id": None,
            "status": "completed", "result": None, "error": None, "progress": 100,
            "current_step": "已提交", "logs": [], "created_at": now, "updated_at": now,
        })
    _insert_agent_message(connection, user_id, conversation["conversation_id"], {
        "message_id": assistant_message_id or _new_id("msg"), "role": "assistant", "content": "任务已提交，正在执行。",
        "run_id": run["run_id"], "status": "running", "result": None, "error": None,
        "progress": run.get("progress") or 0, "current_step": run.get("current_step") or "任务已创建",
        "logs": list(run.get("logs") or []), "created_at": now, "updated_at": now,
    })
    run_ids = list(conversation.get("run_ids") or [])
    if run["run_id"] not in run_ids:
        run_ids.append(run["run_id"])
    conversation.update({
        "agent_type": run.get("agent_type"), "agent_name": _agent_name(str(run.get("agent_type") or "")),
        "prompt": prompt, "latest_run_id": run["run_id"], "run_ids": run_ids, "status": "running",
        "summary": "", "updated_at": now, "is_archived": False,
    })
    _upsert_agent_conversation(connection, user_id, conversation)
    return json.loads(json.dumps(conversation, ensure_ascii=False)), created


def attach_run(run: dict[str, Any], include_user_message: bool = True) -> tuple[dict[str, Any], bool]:
    with app_sqlite.connection() as conn:
        return attach_run_atomic(conn, run, include_user_message=include_user_message)


def _summary_for_run(run: dict[str, Any]) -> str:
    if run.get("status") == "failed":
        return str(run.get("error") or "任务执行失败。")[:300]
    result = run.get("result") or {}
    answer = str(result.get("answer") or "").strip()
    if answer:
        return answer[:300]
    summary = result.get("summary")
    if summary:
        return json.dumps(summary, ensure_ascii=False)[:300] if not isinstance(summary, str) else summary[:300]
    return "任务执行完成" if run.get("status") == "completed" else ""


def update_latest_run(user_id: str, conversation_id: str, run_id: str, status: str) -> None:
    conversation = get_conversation(conversation_id, user_id)
    if conversation is None:
        return
    run_ids = list(conversation.get("run_ids") or [])
    if run_id not in run_ids:
        run_ids.append(run_id)
    conversation.update({"latest_run_id": run_id, "run_ids": run_ids, "status": status, "updated_at": _now()})
    upsert_agent_conversation(user_id, conversation)


def sync_run_to_conversation(run: dict[str, Any], connection: Any | None = None) -> None:
    conversation_id = str(run.get("conversation_id") or "")
    user_id = str(run.get("user_id") or "")
    run_id = str(run.get("run_id") or "")
    if not conversation_id or not user_id or not run_id:
        return
    with app_sqlite.connection(connection) as conn:
        row = conn.execute(
            """
            SELECT * FROM agent_messages
            WHERE conversation_id=? AND user_id=? AND run_id=? AND role='assistant'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (conversation_id, user_id, run_id),
        ).fetchone()
        conv_row = conn.execute(
            "SELECT * FROM agent_conversations WHERE conversation_id=? AND user_id=?",
            (conversation_id, user_id),
        ).fetchone()
        if row is None or conv_row is None:
            return
        message = _row_message(row)
        status = str(run.get("status") or "running")
        message.update({
            "status": status, "result": run.get("result"), "error": run.get("error"),
            "progress": run.get("progress"), "current_step": run.get("current_step"),
            "logs": list(run.get("logs") or []), "updated_at": run.get("updated_at") or _now(),
        })
        if status == "completed":
            message["content"] = str((run.get("result") or {}).get("answer") or "任务执行完成")
        elif status == "failed":
            message["content"] = str(run.get("error") or "任务执行失败。")[:300]
        elif status == "cancelled":
            message["content"] = "任务已取消"
        _insert_agent_message(conn, user_id, conversation_id, message)

        conversation = _row_conversation(conv_row)
        if conversation.get("latest_run_id") == run_id:
            conversation.update({"status": status, "summary": _summary_for_run(run), "updated_at": run.get("updated_at") or _now()})
            _upsert_agent_conversation(conn, user_id, conversation)


def sync_run(run: dict[str, Any]) -> None:
    sync_run_to_conversation(run)
