from typing import Any

from fastapi import APIRouter, Depends

from schemas.chat import ChatRequest, ChatResponse
from services.mock_ai import generate_mock_answer
from services.auth_service import require_operator_or_admin

router = APIRouter()


@router.post("/chat/mock", response_model=ChatResponse)
def mock_chat(payload: ChatRequest, _user: dict[str, Any] = Depends(require_operator_or_admin)) -> ChatResponse:
    return ChatResponse(answer=generate_mock_answer(payload.message))
