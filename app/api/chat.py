from fastapi import APIRouter, Depends

from app.schemas.chat import (
    ChatRequest,
    ChatResponse
)

from app.services.chat_service import (
    chat_service
)

from app.dependencies.auth import (
    get_current_user
)

from app.models.user import User

from app.core.config import settings
from app.core.rate_limiter import limit_by_user


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post(
    "/",
    response_model=ChatResponse,
    # Burst limit + hourly budget per user. Runs before the handler, so a
    # rejected message is never saved, retrieved or sent to the LLM.
    dependencies=[
        Depends(
            limit_by_user(
                "chat",
                (settings.CHAT_RATE_PER_MINUTE, 60),
                (settings.CHAT_RATE_PER_HOUR, 3600),
            )
        )
    ],
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(
        get_current_user
    )
):

    return await chat_service.process_message(
        session_id=request.session_id,
        user_id=current_user.id,
        message=request.message
    )