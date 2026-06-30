import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services import app_sqlite
from services.config_backup_service import resolve_runtime_path
from services.user_context import safe_user_id


SCHEMA_VERSION = "1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _root() -> Path:
    return resolve_runtime_path(os.getenv("QA_CONVERSATION_STORE_ROOT", "apps/api/runtime/users"))


def _store_path(user_id: str) -> Path:
    return _root() / safe_user_id(user_id) / "qa_conversations" / "qa_conversations.json"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _safe_conversation_id(conversation_id: str) -> bool:
    return conversation_id.startswith("qa_conv_") and not any(token in conversation_id for token in ("/", "\\", ".."))


def _normalize_message(message: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    normalized = {
        "message_id": str(message.get("message_id") or _new_id("msg")),
        "role": str(message.get("role") or "assistant"),
        "content": str(message.get("content") or ""),
        "sources": list(message.get("sources") or []),
        "warnings": list(message.get("warnings") or []),
        "status": str(message.get("status") or "completed"),
        "created_at": str(message.get("created_at") or now),
        "updated_at": str(message.get("updated_at") or message.get("created_at") or now),
    }
    if message.get("error"):
        normalized["error"] = str(message.get("error"))
    return normalized


def _normalize_conversation(value: dict[str, Any], user_id: str) -> dict[str, Any] | None:
    conversation_id = str(value.get("conversation_id") or "")
    if not _safe_conversation_id(conversation_id):
        return None
    messages = [_normalize_message(item) for item in value.get("messages", []) if isinstance(item, dict)]
    first_user = next((item for item in messages if item.get("role") == "user"), {})
    now = _now()
    return {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "type": "qa_chat",
        "title": str(value.get("title") or str(first_user.get("content") or "新对话")[:20]),
        "status": str(value.get("status") or (messages[-1]["status"] if messages else "empty")),
        "messages": messages,
        "created_at": str(value.get("created_at") or now),
        "updated_at": str(value.get("updated_at") or now),
        "last_opened_at": str(value.get("last_opened_at") or value.get("updated_at") or now),
        "is_archived": bool(value.get("is_archived", False)),
    }


def _row_message(row: Any) -> dict[str, Any]:
    metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
    message = {
        **metadata,
        "message_id": row["message_id"],
        "role": row["role"],
        "content": row["content"] or "",
        "sources": app_sqlite.json_load(row["sources_json"], []) or [],
        "warnings": app_sqlite.json_load(row["warnings_json"], []) or [],
        "status": row["status"] or "completed",
        "created_at": row["created_at"] or _now(),
        "updated_at": row["updated_at"] or row["created_at"] or _now(),
    }
    if row["error"]:
        message["error"] = row["error"]
    return message


def _row_conversation(row: Any, messages: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    metadata = app_sqlite.json_load(row["metadata_json"], {}) or {}
    return {
        **metadata,
        "conversation_id": row["conversation_id"],
        "user_id": row["user_id"],
        "type": "qa_chat",
        "title": row["title"] or "新对话",
        "status": row["status"] or "empty",
        "messages": messages or [],
        "created_at": row["created_at"] or _now(),
        "updated_at": row["updated_at"] or _now(),
        "last_opened_at": row["last_opened_at"] or row["updated_at"] or _now(),
        "is_archived": bool(row["is_archived"]),
    }


def _legacy_load(user_id: str) -> list[dict[str, Any]]:
    path = _store_path(user_id)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        source = raw.get("conversations") if isinstance(raw, dict) else []
        return [item for value in source if isinstance(value, dict) if (item := _normalize_conversation(value, user_id))]
    except Exception:
        return []


def replace_user_qa_conversations_for_migration(user_id: str, items: list[dict[str, Any]]) -> None:
    # ponytail: bulk replace is only for legacy JSON migration/fallback, never normal API writes.
    with app_sqlite.connection() as conn:
        conn.execute("DELETE FROM qa_messages WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM qa_conversations WHERE user_id=?", (user_id,))
        for conversation in items:
            _upsert_conversation(conn, user_id, conversation)
            for message in conversation.get("messages") or []:
                _insert_message(conn, user_id, conversation["conversation_id"], message)


def _ensure_legacy_loaded(user_id: str) -> None:
    with app_sqlite.connection() as conn:
        exists = conn.execute("SELECT 1 FROM qa_conversations WHERE user_id=? LIMIT 1", (user_id,)).fetchone()
    if not exists:
        migrated = _legacy_load(user_id)
        if migrated:
            replace_user_qa_conversations_for_migration(user_id, migrated)


def _upsert_conversation(conn: Any, user_id: str, conversation: dict[str, Any]) -> None:
    metadata = {key: value for key, value in conversation.items() if key not in {"messages"}}
    conn.execute(
        """
        INSERT INTO qa_conversations(conversation_id, user_id, title, status, is_archived, created_at, updated_at, last_opened_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(conversation_id) DO UPDATE SET user_id=excluded.user_id, title=excluded.title, status=excluded.status,
          is_archived=excluded.is_archived, updated_at=excluded.updated_at, last_opened_at=excluded.last_opened_at,
          metadata_json=excluded.metadata_json
        """,
        (
            conversation["conversation_id"], user_id, conversation.get("title"), conversation.get("status"),
            1 if conversation.get("is_archived") else 0, conversation.get("created_at"), conversation.get("updated_at"),
            conversation.get("last_opened_at"), app_sqlite.json_dump(metadata),
        ),
    )


def upsert_conversation(user_id: str, conversation: dict[str, Any]) -> None:
    with app_sqlite.connection() as conn:
        _upsert_conversation(conn, user_id, conversation)


def _insert_message(conn: Any, user_id: str, conversation_id: str, message: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO qa_messages(message_id, conversation_id, user_id, role, content, status, sources_json, warnings_json, error, created_at, updated_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(message_id) DO UPDATE SET content=excluded.content, status=excluded.status, sources_json=excluded.sources_json,
          warnings_json=excluded.warnings_json, error=excluded.error, updated_at=excluded.updated_at, metadata_json=excluded.metadata_json
        """,
        (
            message["message_id"], conversation_id, user_id, message.get("role"), message.get("content"),
            message.get("status"), app_sqlite.json_dump(message.get("sources") or []), app_sqlite.json_dump(message.get("warnings") or []),
            message.get("error"), message.get("created_at"), message.get("updated_at") or message.get("created_at"), app_sqlite.json_dump(message),
        ),
    )


def append_message(user_id: str, conversation_id: str, message: dict[str, Any]) -> dict[str, Any]:
    with app_sqlite.connection() as conn:
        _insert_message(conn, user_id, conversation_id, message)
    return json.loads(json.dumps(message, ensure_ascii=False))


def touch_conversation(user_id: str, conversation_id: str, status: str | None = None, updated_at: str | None = None, last_opened_at: str | None = None) -> None:
    sets: list[str] = []
    params: list[Any] = []
    if status is not None:
        sets.append("status=?")
        params.append(status)
    if updated_at is not None:
        sets.append("updated_at=?")
        params.append(updated_at)
    if last_opened_at is not None:
        sets.append("last_opened_at=?")
        params.append(last_opened_at)
    if not sets:
        return
    with app_sqlite.connection() as conn:
        conn.execute(f"UPDATE qa_conversations SET {', '.join(sets)} WHERE conversation_id=? AND user_id=?", (*params, conversation_id, user_id))


def update_message(user_id: str, conversation_id: str, message_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    current = _get_message(user_id, conversation_id, message_id)
    if current is None:
        return None
    current.update({key: value for key, value in patch.items() if value is not None})
    current["updated_at"] = patch.get("updated_at") or _now()
    with app_sqlite.connection() as conn:
        _insert_message(conn, user_id, conversation_id, current)
    return json.loads(json.dumps(current, ensure_ascii=False))


def _get_message(user_id: str, conversation_id: str, message_id: str) -> dict[str, Any] | None:
    with app_sqlite.connection() as conn:
        row = conn.execute(
            "SELECT * FROM qa_messages WHERE message_id=? AND conversation_id=? AND user_id=?",
            (message_id, conversation_id, user_id),
        ).fetchone()
    return _row_message(row) if row else None


def create_conversation(user_id: str, title: str = "新对话") -> dict[str, Any]:
    now = _now()
    conversation = {
        "conversation_id": _new_id("qa_conv"), "user_id": user_id, "type": "qa_chat",
        "title": (title or "新对话").strip()[:40], "status": "empty", "messages": [],
        "created_at": now, "updated_at": now, "last_opened_at": now, "is_archived": False,
    }
    upsert_conversation(user_id, conversation)
    return json.loads(json.dumps(conversation, ensure_ascii=False))


def list_conversations(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    _ensure_legacy_loaded(user_id)
    safe_limit = max(1, min(limit, 200))
    with app_sqlite.connection() as conn:
        rows = conn.execute(
            """
            SELECT c.conversation_id, c.title, c.status, c.updated_at, COUNT(m.message_id) AS message_count
            FROM qa_conversations c
            LEFT JOIN qa_messages m ON m.conversation_id=c.conversation_id AND m.user_id=c.user_id
            WHERE c.user_id=? AND c.is_archived=0
            GROUP BY c.conversation_id
            ORDER BY c.updated_at DESC
            LIMIT ?
            """,
            (user_id, safe_limit),
        ).fetchall()
    return [
        {
            "conversation_id": row["conversation_id"],
            "title": row["title"],
            "status": row["status"],
            "message_count": int(row["message_count"] or 0),
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def get_conversation(user_id: str, conversation_id: str, touch: bool = False) -> dict[str, Any] | None:
    if not _safe_conversation_id(conversation_id):
        return None
    _ensure_legacy_loaded(user_id)
    with app_sqlite.connection() as conn:
        row = conn.execute(
            "SELECT * FROM qa_conversations WHERE conversation_id=? AND user_id=? AND is_archived=0",
            (conversation_id, user_id),
        ).fetchone()
        if row is None:
            return None
        messages = [
            _row_message(item)
            for item in conn.execute(
                "SELECT * FROM qa_messages WHERE conversation_id=? AND user_id=? ORDER BY created_at",
                (conversation_id, user_id),
            ).fetchall()
        ]
    conversation = _row_conversation(row, messages)
    if touch:
        conversation["last_opened_at"] = _now()
        touch_conversation(user_id, conversation_id, last_opened_at=conversation["last_opened_at"])
    return json.loads(json.dumps(conversation, ensure_ascii=False))


def archive_conversation(user_id: str, conversation_id: str) -> dict[str, Any] | None:
    conversation = get_conversation(user_id, conversation_id)
    if conversation is None:
        return None
    now = _now()
    with app_sqlite.connection() as conn:
        conn.execute(
            "UPDATE qa_conversations SET is_archived=1, updated_at=? WHERE conversation_id=? AND user_id=?",
            (now, conversation_id, user_id),
        )
    conversation.update({"is_archived": True, "updated_at": now})
    return json.loads(json.dumps(conversation, ensure_ascii=False))


def delete_or_archive_conversation(user_id: str, conversation_id: str) -> dict[str, Any] | None:
    return archive_conversation(user_id, conversation_id)


def append_user_message(user_id: str, conversation_id: str | None, question: str) -> tuple[dict[str, Any], dict[str, Any]]:
    conversation = get_conversation(user_id, conversation_id) if conversation_id else None
    if conversation is None:
        conversation = create_conversation(user_id, question[:20] or "新对话")
    now = _now()
    message = {"message_id": _new_id("msg"), "role": "user", "content": question, "created_at": now, "updated_at": now, "status": "completed"}
    append_message(user_id, conversation["conversation_id"], message)
    if not conversation.get("title") or conversation.get("title") == "新对话":
        conversation["title"] = question[:20] or "新对话"
    conversation.update({"status": "running", "updated_at": now, "is_archived": False})
    upsert_conversation(user_id, conversation)
    conversation["messages"] = [*conversation.get("messages", []), message]
    return json.loads(json.dumps(conversation, ensure_ascii=False)), message


def append_assistant_message(user_id: str, conversation_id: str, content: str, sources: list[dict[str, Any]] | None = None, warnings: list[str] | None = None, status: str = "completed") -> dict[str, Any]:
    conversation = get_conversation(user_id, conversation_id)
    if conversation is None:
        raise RuntimeError("QA 会话不存在。")
    now = _now()
    message = {
        "message_id": _new_id("msg"), "role": "assistant", "content": content,
        "sources": sources or [], "warnings": warnings or [], "status": status,
        "created_at": now, "updated_at": now,
    }
    append_message(user_id, conversation_id, message)
    touch_conversation(user_id, conversation_id, status=status, updated_at=now)
    return json.loads(json.dumps(message, ensure_ascii=False))


def create_assistant_message(user_id: str, conversation_id: str, status: str = "streaming") -> dict[str, Any]:
    return append_assistant_message(user_id, conversation_id, "", sources=[], warnings=[], status=status)


def update_assistant_message(
    user_id: str,
    conversation_id: str,
    message_id: str,
    content: str | None = None,
    sources: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
    status: str | None = None,
    error: str | None = None,
) -> dict[str, Any] | None:
    patch: dict[str, Any] = {}
    if content is not None:
        patch["content"] = content
        if status in {"stopped", "cancelled"}:
            patch["partial_content"] = content
    if sources is not None:
        patch["sources"] = sources
    if warnings is not None:
        patch["warnings"] = warnings
    if error:
        patch["error"] = error
    if status:
        patch["status"] = status
    message = update_message(user_id, conversation_id, message_id, patch)
    if message and status:
        touch_conversation(user_id, conversation_id, status=status, updated_at=message["updated_at"])
    return message
