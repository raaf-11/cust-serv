from fastapi import APIRouter
from app.services.chat_session_service import (chat_session_service)
from fastapi import Depends
from app.dependencies.auth import get_current_user
from app.models.user import User
from fastapi import HTTPException
from typing import List
from app.schemas.chat_session import SessionResponse
from app.schemas.conversation import ConversationResponse

router = APIRouter(
    prefix="/sessions",
    tags=["Chat Sessions"]
)


@router.post(
    "/",
    response_model=int
)
def create_session(
    current_user: User = Depends(
        get_current_user
    )
):

    return chat_session_service.create_session(
        user_id=current_user.id
    )

@router.get(
    "/",
    response_model=List[SessionResponse]
    )
def get_sessions(
    current_user: User = Depends(
        get_current_user
    )
    ):

    return chat_session_service.get_sessions(
        user_id=current_user.id
    )

@router.get("/{session_id}",response_model=List[ConversationResponse])
def get_messages(
    session_id: int,
    current_user: User = Depends(
        get_current_user
    )
):

    conversations = chat_session_service.get_messages(
        session_id=session_id,
        user_id=current_user.id
    )

    if conversations is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return conversations

@router.delete("/{session_id}")
def delete_session(
    session_id: int,
    current_user: User = Depends(
        get_current_user
    )
):

    deleted = chat_session_service.delete_session(
        session_id=session_id,
        user_id=current_user.id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return {
        "message": "Session deleted"
    }