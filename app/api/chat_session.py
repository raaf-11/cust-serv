from fastapi import APIRouter
from app.services.chat_session_service import (chat_session_service)
from fastapi import Depends
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/sessions",
    tags=["Chat Sessions"]
)


@router.post("/")
def create_session(
    current_user: User = Depends(
        get_current_user
    )
):

    return chat_session_service.create_session(
        user_id=current_user.id
    )