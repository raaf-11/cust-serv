from app.db.database import SessionLocal
from app.models.ticket import Ticket
from app.models.conversation import Conversation
from app.models.chat_session import ChatSession


class EmployeeService:

    def get_open_tickets(self):

        db = SessionLocal()

        tickets = (
            db.query(Ticket)
            .filter(
                Ticket.status == "OPEN"
            )
            .order_by(Ticket.created_at.asc())
            .all()
        )

        db.close()

        return tickets

    def get_my_tickets(
        self,
        employee_id: int
    ):

        db = SessionLocal()

        tickets = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_employee_id == employee_id,
                Ticket.status == "IN_PROGRESS"
            )
            .order_by(Ticket.created_at.asc())
            .all()
        )

        db.close()

        return tickets

    def get_ticket(
        self,
        ticket_id: int
    ):

        db = SessionLocal()

        ticket = (
            db.query(Ticket)
            .filter(
                Ticket.id == ticket_id
            )
            .first()
        )

        db.close()

        return ticket

    def accept_ticket(
        self,
        ticket_id: int,
        employee_id: int
    ):

        db = SessionLocal()

        ticket = (
            db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.status == "OPEN"
            )
            .first()
        )

        if not ticket:
            db.close()
            return None

        ticket.assigned_employee_id = employee_id
        ticket.status = "IN_PROGRESS"

        db.commit()
        db.refresh(ticket)

        db.close()

        return ticket

    def resolve_ticket(
        self,
        ticket_id: int,
        employee_id: int
    ):

        db = SessionLocal()

        ticket = (
            db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.assigned_employee_id == employee_id,
                Ticket.status == "IN_PROGRESS"
            )
            .first()
        )

        if not ticket:
            db.close()
            return None

        ticket.status = "RESOLVED"

        db.commit()
        db.refresh(ticket)

        db.close()

        return ticket

    def send_message(
        self,
        ticket_id: int,
        employee_id: int,
        message: str
    ):

        db = SessionLocal()

        ticket = (
            db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.assigned_employee_id == employee_id,
                Ticket.status == "IN_PROGRESS"
            )
            .first()
        )

        if not ticket:
            db.close()
            return None

        conversation = Conversation(
            session_id=ticket.session_id,
            sender="EMPLOYEE",
            content=message
        )

        db.add(conversation)

        db.commit()

        db.refresh(conversation)

        db.close()

        return conversation

    def get_conversation(
        self,
        ticket_id: int,
        employee_id: int
    ):

        db = SessionLocal()

        ticket = (
            db.query(Ticket)
            .filter(
                Ticket.id == ticket_id
            )
            .first()
        )

        if not ticket:
            db.close()
            return None

        # Allow viewing if ticket is OPEN
        # or assigned to this employee
        if (
            ticket.status != "OPEN"
            and ticket.assigned_employee_id != employee_id
        ):
            db.close()
            return None

        conversations = (
            db.query(Conversation)
            .filter(
                Conversation.session_id == ticket.session_id
            )
            .order_by(
                Conversation.created_at
            )
            .all()
        )

        db.close()

        return conversations


employee_service = EmployeeService()