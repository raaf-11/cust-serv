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


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post(
    "/",
    response_model=ChatResponse
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