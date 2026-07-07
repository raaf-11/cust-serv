from app.db.database import SessionLocal
from app.models.chat_session import ChatSession
from app.models.conversation import Conversation


class ChatSessionService:

    def create_session(
        self,
        user_id: int,
        title: str = "New Chat"
    ) -> ChatSession:

        db = SessionLocal()

        session = ChatSession(
            user_id=user_id,
            title=title
        )

        db.add(session)
        db.commit()
        db.refresh(session)
        db.close()
        return session


    def get_session(
        self,
        session_id: int,
        user_id: int
    ):

        db = SessionLocal()

        session = (
            db.query(ChatSession)
            .filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
            .first()
        )

        db.close()

        return session

    def get_sessions(
        self,
        user_id: int
    ):

        db = SessionLocal()

        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

        db.close()

        return sessions

    def get_messages(
        self,
        session_id: int,
        user_id: int
    ):

        db = SessionLocal()

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

        conversations = (
            db.query(Conversation)
            .filter(
                Conversation.session_id == session_id
            )
            .order_by(Conversation.id)
            .all()
        )

        db.close()

        return conversations

    def delete_session(
        self,
        session_id: int,
        user_id: int
    ):

        db = SessionLocal()

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
            return False

        db.delete(session)
        db.commit()

        db.close()

        return True


chat_session_service = ChatSessionService()