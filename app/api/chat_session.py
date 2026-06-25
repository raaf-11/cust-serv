from fastapi import APIRouter

from app.services.chat_session_service import (
    chat_session_service
)

router = APIRouter(
    prefix="/sessions",
    tags=["Chat Sessions"]
)


@router.post("/")
def create_session():

    session_id = chat_session_service.create_session(
        user_id=1
    )

    return {
        "session_id": session_id
    }