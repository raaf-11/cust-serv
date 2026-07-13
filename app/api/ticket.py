from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user
from app.models.user import User

from app.schemas.ticket import (
    TicketCreate,
    TicketResponse
)

from app.services.ticket_service import ticket_service

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.post(
    "/",
    response_model=TicketResponse
)
def create_ticket(
    request: TicketCreate,
    current_user: User = Depends(
        get_current_user
    )
):

    ticket = ticket_service.create_ticket(
        user_id=current_user.id,
        session_id=request.session_id,
        subject=request.subject,
        description=request.description
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return ticket


@router.get(
    "/",
    response_model=List[TicketResponse]
)
def get_tickets(
    current_user: User = Depends(
        get_current_user
    )
):

    return ticket_service.get_tickets(
        user_id=current_user.id
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse
)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(
        get_current_user
    )
):

    ticket = ticket_service.get_ticket(
        ticket_id=ticket_id,
        user_id=current_user.id
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return ticket