from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    agent_type: str = Field(default="", max_length=100)
    title: str = Field(default="", max_length=200)


class ConversationRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
