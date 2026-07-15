from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import require_employee
from app.models.user import User
from app.schemas.ticket import TicketResponse
from app.services.employee_service import employee_service
from app.schemas.employee import EmployeeMessageRequest
from app.schemas.conversation import ConversationResponse

router = APIRouter(
    prefix="/employee",
    tags=["Employee"]
)


@router.get(
    "/tickets",
    response_model=List[TicketResponse]
)
def get_open_tickets(
    current_user: User = Depends(require_employee)
):

    return employee_service.get_open_tickets()


@router.get(
    "/my-tickets",
    response_model=List[TicketResponse]
)
def get_my_tickets(
    current_user: User = Depends(require_employee)
):

    return employee_service.get_my_tickets(
        employee_id=current_user.id
    )


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse
)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(require_employee)
):

    ticket = employee_service.get_ticket(
        ticket_id=ticket_id
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found."
        )

    return ticket


@router.patch(
    "/tickets/{ticket_id}/accept",
    response_model=TicketResponse
)
def accept_ticket(
    ticket_id: int,
    current_user: User = Depends(require_employee)
):

    ticket = employee_service.accept_ticket(
        ticket_id=ticket_id,
        employee_id=current_user.id
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found or already accepted."
        )

    return ticket


@router.patch(
    "/tickets/{ticket_id}/resolve",
    response_model=TicketResponse
)
def resolve_ticket(
    ticket_id: int,
    current_user: User = Depends(require_employee)
):

    ticket = employee_service.resolve_ticket(
        ticket_id=ticket_id,
        employee_id=current_user.id
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found or not assigned to you."
        )

    return ticket

@router.post("/tickets/{ticket_id}/message")
def send_message(
    ticket_id: int,
    request: EmployeeMessageRequest,
    current_user: User = Depends(require_employee)
):

    message = employee_service.send_message(
        ticket_id=ticket_id,
        employee_id=current_user.id,
        message=request.message
    )

    if message is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found."
        )

    return {
        "message": "Reply sent successfully."
    }

@router.get(
    "/tickets/{ticket_id}/conversation",
    response_model=list[ConversationResponse]
)
def get_conversation(
    ticket_id: int,
    current_user: User = Depends(require_employee)
):

    conversation = employee_service.get_conversation(
        ticket_id=ticket_id,
        employee_id=current_user.id
    )

    if conversation is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found."
        )

    return conversation