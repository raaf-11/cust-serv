from app.db.database import SessionLocal
from app.models.chat_session import ChatSession


class ChatSessionService:

    def create_session(
        self,
        user_id: int,
        title: str = "New Chat"
    ) -> int:

        db = SessionLocal()

        session = ChatSession(
            user_id=user_id,
            title=title
        )

        db.add(session)

        db.commit()

        db.refresh(session)

        session_id = session.id

        db.close()

        return session_id


chat_session_service = ChatSessionService()