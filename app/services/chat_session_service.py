from app.db.database import SessionLocal
from app.models.chat_session import ChatSession
from app.models.conversation import Conversation
from app.models.ticket import Ticket


class ChatSessionService:
    def create_session(self, user_id: int, title: str = "New Chat") -> ChatSession:
        db = SessionLocal()
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        db.close()
        return session

    def get_session(self, session_id: int, user_id: int):
        db = SessionLocal()

        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .first()
        )

        db.close()
        return session

    def get_sessions(self, user_id: int):
        db = SessionLocal()

        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

        db.close()
        return sessions

    def get_messages(self, session_id: int, user_id: int):
        db = SessionLocal()

        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .first()
        )

        if not session:
            db.close()
            return None

        conversations = (
            db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .order_by(Conversation.id)
            .all()
        )

        db.close()
        return conversations

    def delete_session(self, session_id: int, user_id: int) -> str:
        db = SessionLocal()

        try:
            session = (
                db.query(ChatSession)
                .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
                .first()
            )

            if not session:
                return "not_found"

            active_ticket = (
                db.query(Ticket)
                .filter(
                    Ticket.session_id == session_id,
                    Ticket.status.in_(["OPEN", "IN_PROGRESS"]),
                )
                .first()
            )

            if active_ticket:
                return "has_active_ticket"

            db.query(Ticket).filter(Ticket.session_id == session_id).delete(
                synchronize_session=False
            )

            db.query(Conversation).filter(Conversation.session_id == session_id).delete(
                synchronize_session=False
            )

            db.delete(session)
            db.commit()
            return "deleted"

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def update_title(self, session_id: int, title: str):
        db = SessionLocal()
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

        if session:
            session.title = title
            db.commit()

        db.close()


chat_session_service = ChatSessionService()
