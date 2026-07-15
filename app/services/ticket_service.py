from app.db.database import SessionLocal
from app.models.ticket import Ticket
from app.models.chat_session import ChatSession


class TicketService:

    def create_ticket(
        self,
        user_id: int,
        session_id: int,
        subject: str,
        description: str
    ):

        db = SessionLocal()

        # Verify the session belongs to the current user
        session = (
            db.query(ChatSession)
            .filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
            .first()
        )

        if not session:
            db.close()
            return None

        ticket = Ticket(
            user_id=user_id,
            session_id=session_id,
            subject=subject,
            description=description
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        db.close()

        return ticket

    def get_tickets(
        self,
        user_id: int
    ):

        db = SessionLocal()

        tickets = (
            db.query(Ticket)
            .filter(Ticket.user_id == user_id)
            .order_by(Ticket.created_at.desc())
            .all()
        )

        db.close()

        return tickets

    def get_ticket(
        self,
        ticket_id: int,
        user_id: int
    ):

        db = SessionLocal()

        ticket = (
            db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.user_id == user_id
            )
            .first()
        )

        db.close()

        return ticket

    def get_active_ticket(
    self,
    session_id: int
    ):

        db = SessionLocal()

        ticket = (
            db.query(Ticket)
            .filter(
                Ticket.session_id == session_id,
                Ticket.status == "IN_PROGRESS"
            )
        .   first()
        )

        db.close()

        return ticket


ticket_service = TicketService()