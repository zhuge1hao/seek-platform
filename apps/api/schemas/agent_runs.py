import os
from typing import Any

from pydantic import BaseModel, Field


DEFAULT_VIDEO_SCRIPT_SESSION_ID = "019dd824-f4bb-7273-8ac3-6e19b195ff82"
DEFAULT_VIDEO_SCRIPT_MODE = "standard_breakdown"


def default_video_script_session_id() -> str:
    return os.getenv("LOCAL_AGENT_VIDEO_SCRIPT_SESSION_ID") or os.getenv("LOCAL_AGENT_SESSION_ID") or DEFAULT_VIDEO_SCRIPT_SESSION_ID


def default_generic_session_id() -> str | None:
    return os.getenv("LOCAL_AGENT_DEFAULT_SESSION_ID") or None


class AgentRunCreate(BaseModel):
    agent_type: str = Field(..., min_length=1)
    mode: str | None = None
    prompt: str = Field(..., min_length=1)
    selected_skill_ids: list[str] | None = None
    link: str | None = None
    file_ids: list[str] | None = None
    dataset_ids: list[str] | None = None
    image_paths: list[str] | None = None
    video_path: str | None = None
    video_url: str | None = None
    session_id: str | None = None
    workflow_options: dict[str, Any] | None = None
    conversation_id: str | None = None


class AgentRunCreateResponse(BaseModel):
    run_id: str
    conversation_id: str
    status: str
    message: str
